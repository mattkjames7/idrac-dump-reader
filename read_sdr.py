

fname = "sdr.bin"


class RawRecordData:
  def __init__(self, data):
    self.iterator = iter(data)

  def next(self, n=1):
    if not isinstance(n, int) and not n == "all":
      raise ValueError

    items = []
    try:
      if n == "all":
        items = list(self.iterator)
      else:
        items = [next(self.iterator) for _ in range(n)]
    except StopIteration:
      pass
    return items



def read_header(file_data):
  out = {}
  out["record_id"] = int.from_bytes([next(file_data), next(file_data)], byteorder="little")
  out["sdr_version"] = int.from_bytes([next(file_data)], byteorder="little")
  out["record_type"] = int.from_bytes([next(file_data)], byteorder="little")
  out["record_length"] = int.from_bytes([next(file_data)], byteorder="little")

  record_bytes = [next(file_data) for _ in range(out["record_length"])]
  return out, RawRecordData(record_bytes)


def decode_bcd(str_bytes):

  char_map = {
    10: " ",
    11: "-",
    12: ".",
    13: ";",
    14: ",",
    15: "_"
  }

  out = ""
  for byte in str_bytes:
    upper = byte >> 4
    lower = byte & 0b00001111

    for part in [upper, lower]:
      out += char_map.get(part, f"{int(part)}")
  return out


def decode_6bit_ascii(str_bytes):

  chars = " !\"#$%&'()*+,-./0123456789:;<=>?"
  chars += "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"

  out = ""
  last = None
  remaining = 0
  for i, byte in enumerate(str_bytes):
    t = i % 3

    if t == 0:
      upper = byte >> 6
      remaining = upper
      lower = byte & 0b00111111
      out += chars[lower]
    elif t == 1:
      upper = byte >> 4
      lower = byte & 0b00001111
      index = (lower << 2) | remaining
      out += chars[index]
      remaining = upper
    else:
      upper = byte >> 2
      lower = byte & 0b00000011
      index = (lower << 4) | remaining
      out += chars[index]
      out += chars[upper]
  return out


def decode_8bit_ascii(str_bytes):

  return bytes(str_bytes).decode("latin-1")


def decode_unicode(str_bytes):

  return bytes(str_bytes).decode("utf-16-le")


def read_record_key_bytes(data):
  out = {}

  value = data.next()[0]
  owner_id = (value >> 1) & 0x7F
  is_system_software_id = bool(value &0x01)
  if is_system_software_id:
    key = "system_software_id"
  else:
    key = "ipmb_slave_address"
  out[key] = owner_id

  value = data.next()[0]
  channel = (value >> 4) & 0x0F
  reserved = (value >> 2) & 0x03
  owner_lun = value & 0x03

  out["sensor_owner_lun"] = {
    "channel": channel,
    "reserved": reserved,
    "owner_lun": owner_lun
  }

  out["sensor_number"] = data.next()
  return out


def record_body_bytes(data):

  out = {}
  out["id"] = data.next()[0]

  instance = data.next()[0]
  out["physical"] = (instance >> 7) == 0  # or logical
  out["number"] = instance & 0x7f

  sensor_init = data.next()[0]
  out["initialization"] = {
    "settable": (sensor_init & 0b10000000) >> 7,
    "scanning": (sensor_init & 0b01000000) >> 6,
    "events": (sensor_init & 0b00100000) >> 5,
    "thresholds": (sensor_init & 0b00010000) >> 4,
    "hysteresis": (sensor_init & 0b00001000) >> 3,
    "sensor_type": (sensor_init & 0b00000100) >> 2,
    "default_state": {
      "generation": (sensor_init & 0b00000010) >> 1,
        "scanning": (sensor_init & 0b00000001)
    }
  }

  value = data.next()[0]

  hyst_value = (value & 0b00110000) >> 4
  hysteresis = {
    "supported": hyst_value != 0,
    "readable": hyst_value in [1, 2],
    "settable": hyst_value == 2,
    "fixed": hyst_value == 3
  }
  thresh_value = (value & 0b00001100) >> 2
  threshold = {
    "supported": thresh_value != 0,
    "readable": thresh_value in (1, 2),
    "settable": thresh_value == 2,
    "fixed": thresh_value == 3
  }
  mess_value = (value & 0b00000011)
  messages = {
    "per_threshold": mess_value == 0,
    "entire_sensor": mess_value <= 1,
    "global_disable": mess_value <= 2
  }
  out["capabilities"] = {
    "ignore": value & 0b00000000,
    "auto_rearm": value & 0b00000000,
    "hysteresis": hysteresis,
    "threshold_access": threshold,
    "messages": messages
  }

  value = data.next()[0]
  out["type"] = {
    "code": value  # TODO map to string table 42-3
  }

  value = data.next()[0]
  out["reading_type"] = {
    "code": value  # TODO map to string from table 42-1
  }

  value = data.next()[0] & 0b0111111111111111
  out["event_assertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = data.next(2)[0] & 0b0111111111111111
  out["threshold_assertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = data.next(2)[0] & 0b0111111111111111
  out["event_deassertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = data.next(2)[0] & 0b0111111111111111
  out["threshold_deassertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = data.next(2)[0] & 0b0111111111111111
  out["discrete_reading_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = data.next()[0] & 0b00111111
  out["threshold_settable_mask"] = [bool(value & (1 << i)) for i in reversed(range(8))]

  value = data.next()[0] & 0b00111111
  out["threshold_readable_mask"] = [bool(value & (1 << i)) for i in reversed(range(8))]

  value = data.next()[0]
  format_value = value >> 6
  format_name = {
    0: "unsigned",
    1: "signed, 1's compliment",
    2: "signed, 2's compliment",
    3: "not numeric"
  }[format_value]

  rate_value = (value & 0b00111111) >> 3
  rate_unit = {
    0: None,
    1: "μs",
    2: "ms",
    3: "s",
    4: "minute",
    5: "hour",
    6: "day",
    7: "reserved"
  }[rate_value]

  mod_value = (value & 0b00000110) >> 1
  mod_unit = {
    0: None,
    1: "divide",
    2: "times",
    3: "reserved"
  }[mod_value]

  out["units"] = {
    "format": {
      "code": format_value,
      "name": format_name
    },
    "rate": {
      "code": rate_value,
      "unit": rate_unit
    },
    "modifier": {
      "code": mod_value,
      "unit": mod_unit
    },
    "percentage": bool(value & 0b00000001)
  }

  out["base_unit"] = data.next()[0]  # TODO: table 43-15
  out["modifier_unit"] = data.next()[0]

  LINEARIZATION = {
      0x00: "linear",
      0x01: "ln",
      0x02: "log10",
      0x03: "log2",
      0x04: "exp",
      0x05: "exp10",
      0x06: "exp2",
      0x07: "reciprocal",
      0x08: "square",
      0x09: "cube",
      0x0A: "sqrt",
      0x0B: "cube_root",
  }
  value = data.next()[0] & 0b01111111
  if value in LINEARIZATION:
      linearization = LINEARIZATION[value]
  elif value == 0x70:
      linearization = "non-linear"
  elif 0x71 <= value <= 0x7F:
      linearization = "OEM-defined"
  else:
      linearization = "reserved"
  out["linearization"] = linearization
  print(linearization)

  value = data.next(2)  # is 10 bit signed + tolerance
  m_lsb = value[0]
  m_msb = (value[1] >> 6) << 8
  m_raw = m_lsb | m_msb
  out["m"] = m_raw - 512 if (m_raw & 0x200) else m_raw
  out["tolerance"] = value[1] & 0b00111111

  value = data.next(2)  # is 10 bit signed + accuracy
  b_lsb = value[0]
  b_msb = (value[1] >> 6) << 8
  b_raw = b_lsb | b_msb
  out["b"] = b_raw - 512 if (b_raw & 0x200) else b_raw
  accuracy_ls = value[1] & 0b00111111
  value = data.next()[0]
  accuracy_ms = (value >> 4) << 8
  out["accuracy"] = accuracy_ms | accuracy_ls
  out["accuracy_exp"] = (value & 0b00001100) >> 2
  direction_code = (value & 0b00000011)
  direction_value = {
    0: "unspecified",
    1: "input",
    2: "output",
    3: "reserved"
    }[direction_code]
  out["sensor_direction"] = {
    "code": direction_code,
    "value": direction_value
  }

  value = data.next()[0]
  out["r_exp"] = (value >> 4) - 0b1000
  out["b_exp"] = (value & 0b00001111) - 0b1000

  # analog characteristics
  value = data.next()[0]
  out["has_normal_min"] = bool((value & 0b00000100) >> 2)
  out["has_normal_max"] = bool((value & 0b00000010) >> 1)
  out["has_nominal_reading"] = bool(value & 0b00000001)

  value = data.next()[0]
  out["nominal_reading_raw"] = value

  value = data.next()[0]
  out["normal_maximum_raw"] = value

  value = data.next()[0]
  out["normal_minimum_raw"] = value

  value = data.next()[0]
  out["sensor_maximum_raw"] = value

  value = data.next()[0]
  out["sensor_minimum_raw"] = value

  value = data.next()[0]
  out["upper_non-recoverable_threshold_raw"] = value

  value = data.next()[0]
  out["upper_critical_threshold_raw"] = value

  value = data.next()[0]
  out["upper_non-critical_threshold_raw"] = value

  value = data.next()[0]
  out["lower_non-recoverable_threshold_raw"] = value

  value = data.next()[0]
  out["lower_critical_threshold_raw"] = value

  value = data.next()[0]
  out["lower_non-critical_threshold_raw"] = value

  value = data.next()[0]
  out["positive-going_threshold_hysteresis_value"] = value

  value = data.next()[0]
  out["negative-going_threshold_hysteresis_value"] = value

  _ = data.next(3)  # reserved values

  value = data.next()[0]
  fmt_code = (value & 0b11000000) >> 6
  fmt = {
    0: "unicode",
    1: "bcd-plus",
    2: "6-bit-ascii",
    3: "8-bit-ascii"
  }[fmt_code]

  str_length = value & 0b00011111
  if not str_length in [0, 31]:
    str_bytes = data.read(str_length)

    if fmt == "unicode":
      device_id = decode_unicode(str_bytes)
    elif fmt == "bcd-plus":
      device_id = decode_bcd(str_bytes)
    elif fmt == "6-bit-ascii":
      device_id = decode_6bit_ascii(str_bytes)
    else:
      device_id = decode_8bit_ascii(str_bytes)

    out["device_id"] = device_id

  return out


def main():
  records = []

  with open(fname, "rb") as f:
    file_data = iter(f.read())

  while True:
    try:
      record, record_data = read_header(file_data)
      if record["record_length"] == 0:
        break
      record.update(read_record_key_bytes(record_data))
      if record["record_type"] == 1:
        record.update(record_body_bytes(record_data))
      print(record)
    except StopIteration:
      break


if __name__ == "__main__":
  main()
