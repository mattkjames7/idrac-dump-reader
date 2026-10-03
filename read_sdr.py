

fname = "sdr.bin"


def read_header(f):
  out = {}
  out["record_id"] = int.from_bytes(f.read(2), byteorder="little")
  out["sdr_version"] = int.from_bytes(f.read(1), byteorder="little")
  out["record_type"] = int.from_bytes(f.read(1), byteorder="little")
  out["record_length"] = int.from_bytes(f.read(1), byteorder="little")

  return out


def read_record_key_bytes(f):
  out = {}

  value = f.read(1)[0]
  owner_id = (value >> 1) & 0x7F
  is_system_software_id = bool(value &0x01)
  if is_system_software_id:
    key = "system_software_id"
  else:
    key = "ipmb_slave_address"
  out[key] = owner_id

  value = f.read(1)[0]
  channel = (value >> 4) & 0x0F
  reserved = (value >> 2) & 0x03
  owner_lun = value & 0x03

  out["sensor_owner_lun"] = {
    "channel": channel,
    "reserved": reserved,
    "owner_lun": owner_lun
  }

  out["sensor_number"] = f.read(1)[0]
  return out


def record_body_bytes(f):

  out = {}
  out["id"] = f.read(1)[0]

  instance = f.read(1)[0]
  out["physical"] = (instance >> 7) == 0  # or logical
  out["number"] = instance & 0x7f

  sensor_init = f.read(1)[0]
  out["initialization"] = {
    "settable": sensor_init & 0b10000000,
    "scanning": sensor_init & 0b01000000,
    "events": sensor_init & 0b00100000,
    "thresholds": sensor_init & 0b00010000,
    "hysteresis": sensor_init & 0b00001000,
    "sensor_type": sensor_init & 0b00000100,
    "default_state": {
      "generation": sensor_init & 0b00000010,
      "scanning": sensor_init & 0b00000001
    }
  }

  value = f.read(1)[0]

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

  value = f.read(1)[0]
  out["type"] = {
    "code": value  # TODO map to string table 42-3
  }

  value = f.read(1)[0]
  out["reading_type"] = {
    "code": value  # TODO map to string from table 42-1
  }

  value = f.read(2)[0] & 0b0111111111111111
  out["event_assertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = f.read(2)[0] & 0b0111111111111111
  out["threshold_assertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = f.read(2)[0] & 0b0111111111111111
  out["event_deassertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = f.read(2)[0] & 0b0111111111111111
  out["threshold_deassertion_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = f.read(2)[0] & 0b0111111111111111
  out["discrete_reading_mask"] = [bool(value & (1 << i)) for i in reversed(range(16))]

  value = f.read(1)[0] & 0b00111111
  out["threshold_settable_mask"] = [bool(value & (1 << i)) for i in reversed(range(8))]

  value = f.read(1)[0] & 0b00111111
  out["threshold_readable_mask"] = [bool(value & (1 << i)) for i in reversed(range(8))]

  value = f.read(1)[0]
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

  out["base_unit"] = f.read(1)[0]  # TODO: table 43-15
  out["modifier_unit"] = f.read(1)[0]
  out["linearization"] = f.read(1)[0]  # TODO: wtf is this enum?

  value = f.read(2)[0]  # is 10 bit signed + tolerance
  m_lsb = value[0]
  m_msb = (value[1] >> 6) << 8
  m_raw = m_lsb | m_msb
  out["m"] = m_raw - 512 if (m_raw & 0x200) else m_raw
  out["tolerance"] = value[1] & 0b00111111

  value = f.read(2)[0]  # is 10 bit signed + accuracy
  b_lsb = value[0]
  b_msb = (value[1] >> 6) << 8
  b_raw = b_lsb | b_msb
  out["b"] = b_raw - 512 if (b_raw & 0x200) else b_raw
  out["accuracy"] = value[1] & 0b00111111

def main():
  records = []

  with open(fname, "rb") as f:
    while True:
      record = read_header(f)
      if record["record_length"] == 0:
        break
      record.update(read_record_key_bytes(f))
      print(record)
      f.read(record["record_length"]-3)



if __name__ == "__main__":
  main()
