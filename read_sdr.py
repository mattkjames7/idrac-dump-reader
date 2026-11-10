

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


def read_u16(data):
  low, high = data.next(2)
  return low | (high << 8)


def int_to_bool_array(value, length):
  return [bool(value & (1 << i)) for i in reversed(range(length))]


def sensor_type(code):
  sensor_types = {
    0x00: "reserved",
    0x01: "temperature",
    0x02: "voltage",
    0x03: "current",
    0x04: "fan",
    0x05: "physical security",
    0x06: "platform security violation attempt",
    0x07: "processor",
    0x08: "power supply",
    0x09: "power unit",
    0x0a: "cooling device",
    0x0b: "other units-based sensor",
    0x0c: "memory",
    0x0d: "drive slot/bay",
    0x0e: "post memory resize",
    0x0f: "system firmware progress",
    0x10: "event logging disabled",
    0x11: "watchdog 1",
    0x12: "system event",
    0x13: "critical interrupt",
    0x14: "button/switch",
    0x15: "module/board",
    0x16: "microcontroller/coprocessor",
    0x17: "add-in card",
    0x18: "chassis",
    0x19: "chip set",
    0x1a: "other fru",
    0x1b: "cable/interconnect",
    0x1c: "terminator",
    0x1d: "system boot/restart initiated",
    0x1e: "boot error",
    0x1f: "base os boot/installation status",
    0x20: "os stop/shutdown",
    0x21: "slot/connector",
    0x22: "system acpi power state",
    0x23: "watchdog 2",
    0x24: "platform alert",
    0x25: "entity presence",
    0x26: "monitor asic/ic",
    0x27: "lan",
    0x28: "management subsystem health",
    0x29: "battery",
    0x2a: "session audit",
    0x2b: "version change",
    0x2c: "fru state",
  }

  if code in sensor_types:
    return sensor_types[code]
  if 0xc0 <= code <= 0xff:
    return "oem reserved"
  return "reserved"


def event_reading_type(code):
  event_reading_types = {
    0x00: {"category": "unspecified", "class": "n/a"},
    0x01: {"category": "threshold", "class": "threshold"},
    0x6f: {"category": "sensor-specific", "class": "discrete"},
  }

  if code in event_reading_types:
    return event_reading_types[code].copy()
  if 0x02 <= code <= 0x0c:
    return {"category": "generic", "class": "discrete"}
  if 0x70 <= code <= 0x7f:
    return {"category": "oem", "class": "oem"}
  return {"category": "reserved", "class": "reserved"}


def get_sensor_unit_type(code):

  units = {
    0: "unspecified",
    1: "degrees C",
    2: "degrees F",
    3: "degrees K",
    4: "Volts",
    5: "Amps",
    6: "Watts",
    7: "Joules",
    8: "Coulombs",
    9: "VA",
    10: "Nits",
    11: "lumen",
    12: "lux",
    13: "Candela",
    14: "kPa",
    15: "PSI",
    16: "Newton",
    17: "CFM",
    18: "RPM",
    19: "Hz",
    20: "microsecond",
    21: "millisecond",
    22: "second",
    23: "minute",
    24: "hour",
    25: "day",
    26: "week",
    27: "mil",
    28: "inches",
    29: "feet",
    30: "cu in",
    31: "cu feet",
    32: "mm",
    33: "cm",
    34: "m",
    35: "cu cm",
    36: "cu m",
    37: "liters",
    38: "fluid ounce",
    39: "radians",
    40: "steradians",
    41: "revolutions",
    42: "cycles",
    43: "gravities",
    44: "ounce",
    45: "pound",
    46: "ft-lb",
    47: "oz-in",
    48: "gauss",
    49: "gilberts",
    50: "henry",
    51: "millihenry",
    52: "farad",
    53: "microfarad",
    54: "ohms",
    55: "siemens",
    56: "mole",
    57: "becquerel",
    58: "PPM (parts/million)",
    60: "Decibels",
    61: "DbA",
    62: "DbC",
    63: "gray",
    64: "sievert",
    65: "color temp deg K",
    66: "bit",
    67: "kilobit",
    68: "megabit",
    69: "gigabit",
    70: "byte",
    71: "kilobyte",
    72: "megabyte",
    73: "gigabyte",
    74: "word (data)",
    75: "dword",
    76: "qword",
    77: "line (re. mem. line)",
    78: "hit",
    79: "miss",
    80: "retry",
    81: "reset",
    82: "overrun / overflow",
    83: "underrun",
    84: "collision",
    85: "packets",
    86: "messages",
    87: "characters",
    88: "error",
    89: "correctable error",
    90: "uncorrectable error",
    91: "fatal error",
    92: "grams",
  }
  return units.get(code, None)


def get_sensor_capabilities(value):

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
  out = {
    "ignore": bool((value & 0b10000000) >> 7),
    "auto_rearm": bool((value & 0b01000000) >> 6),
    "hysteresis": hysteresis,
    "threshold_access": threshold,
    "messages": messages
  }
  return out


def get_sensor_units(values):

  out = {}

  format_value = values[0] >> 6
  format_name = {
    0: "unsigned",
    1: "signed, 1's complement",
    2: "signed, 2's complement",
    3: "not numeric"
  }[format_value]

  rate_value = (values[0] & 0b00111111) >> 3
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

  mod_value = (values[0] & 0b00000110) >> 1
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
    "percentage": bool(values[0] & 0b00000001)
  }

  out["base_unit"] = get_sensor_unit_type(values[1])
  out["modifier_unit"] = values[2]
  return out


def decode_device_id(data):

  value = data.next()[0]
  fmt_code = (value & 0b11000000) >> 6
  fmt = {
    0: "unicode",
    1: "bcd-plus",
    2: "6-bit-ascii",
    3: "8-bit-ascii"
  }[fmt_code]

  str_length = value & 0b00011111
  if fmt == "unicode":
    byte_length = str_length * 2
  elif fmt == "bcd-plus":
    byte_length = (str_length + 1) // 2
  elif fmt == "6-bit-ascii":
    byte_length = (str_length * 6 + 7) // 8
  else:
    byte_length = str_length

  device_id = None
  if not str_length in [0, 31]:
    str_bytes = data.next(byte_length)

    if fmt == "unicode":
      device_id = decode_unicode(str_bytes)
    elif fmt == "bcd-plus":
      device_id = decode_bcd(str_bytes)
    elif fmt == "6-bit-ascii":
      device_id = decode_6bit_ascii(str_bytes)
    else:
      device_id = decode_8bit_ascii(str_bytes)

  return fmt, device_id


def full_sensor_record_body_bytes(data):

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
  out["capabilities"] = get_sensor_capabilities(value)

  value = data.next()[0]
  out["type"] = {
    "code": sensor_type(value)
  }

  value = data.next()[0]
  out["reading_type"] = {
    "code": value,
    **event_reading_type(value)
  }

  is_threshold_based = out["reading_type"]["class"] == "threshold"
  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)

  if is_threshold_based:
    out["lower_threshold_reading_mask"] = mask[1:4]
    out["threshold_assertion_mask"] = mask[4:]
  else:
    out["assertion_event_mask"] = mask[1:]

  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)
  if is_threshold_based:
    out["upper_threshold_reading_mask"] = mask[1:4]
    out["threshold_deassertion_mask"] = mask[4:]
  else:
    out["deassertion_event_mask"] = mask[1:]

  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)
  if is_threshold_based:
    out["settable_threshold_mask"] = mask[2:8]
    out["threshold_readable_mask"] = mask[10:]
  else:
    out["read_mask"] = mask[1:]

  values = data.next(3)
  out.update(get_sensor_units(values))

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
  accuracy_ms = (value >> 4) << 6
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

  def signed_nibble(value):
    value = value & 0b1111
    out = value - 16 if value & 0b1000 else value
    return out

  value = data.next()[0]
  out["r_exp"] = signed_nibble(value >> 4)
  out["b_exp"] = signed_nibble(value)

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

  _ = data.next(3)  # 2 reserved values + OEM value

  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def read_compact_record_key_bytes(data):

  out = {}

  # 6 sensor owner ID
  value = data.next()[0]
  record_type = bool(value & 0b0000_0001)
  record_value = value >> 1
  if record_type:
    out["software_id"] = record_value
  else:
    out["slave_address"] = record_value

  # 7 sensor owner LUN
  value = data.next()[0]
  out["channel_number"] = value >> 4
  out["fru_inventory_device_owner"] = (value & 0b0000_1100) >> 2
  out["sensor_owner_lun"] = value & 0b0000_0011

  # 8 sensor number
  out["sensor_number"] = data.next()[0]

  return out


def compact_sensor_record(data):
  """Table 43-2 - page 558-563"""

  out = {}

  # 9 entity ID -> 43-13
  out["entity_id"] = data.next()[0]

  # 10 entity instance
  value = data.next()[0]
  out["entity_instance"] = {
    "type": "logical" if (value >> 7) else "physical",
    "number": value & 0b0111_1111
  }

  # 11 sensor initialization
  value = data.next()[0]
  out["initialization"] = {
    "settable": (value & 0b10000000) >> 7,
    "scanning": (value & 0b01000000) >> 6,
    "events": (value & 0b00100000) >> 5,
    "thresholds": (value & 0b00010000) >> 4,
    "hysteresis": (value & 0b00001000) >> 3,
    "sensor_type": (value & 0b00000100) >> 2,
    "default_state": {
      "generation": (value & 0b00000010) >> 1,
      "scanning": (value & 0b00000001)
    }
  }

  # 12 capabilities
  value = data.next()[0]
  out["capabilities"] = get_sensor_capabilities(value)

  # 13 sensor type
  value = data.next()[0]
  out["type"] = {
    "code": sensor_type(value)
  }

  # 14 event / reading type code
  value = data.next()[0]
  out["reading_type"] = {
    "code": value,
    **event_reading_type(value)
  }

  # 15/16 asertion event maske / lower threshold reading mask
  is_threshold_based = out["reading_type"]["class"] == "threshold"
  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)

  if is_threshold_based:
    out["lower_threshold_reading_mask"] = mask[1:4]
    out["threshold_assertion_mask"] = mask[4:]
  else:
    out["assertion_event_mask"] = mask[1:]

  # 17/18 Deassertion Event Mask / Upper Threshold Reading Mask
  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)
  if is_threshold_based:
    out["upper_threshold_reading_mask"] = mask[1:4]
    out["threshold_deassertion_mask"] = mask[4:]
  else:
    out["deassertion_event_mask"] = mask[1:]

  # 19/20 Discrete Reading Mask / Settable Threshold Mask, Readable Threshold Mask
  value = read_u16(data) & 0b0111_1111_1111_1111
  mask = int_to_bool_array(value, 16)
  if is_threshold_based:
    out["settable_threshold_mask"] = mask[2:8]
    out["threshold_readable_mask"] = mask[10:]
  else:
    out["read_mask"] = mask[1:]

  # 21, 22 and 23: Sensor units 1, 2 base unit, 3 modifier unit
  values = data.next(3)
  out.update(get_sensor_units(values))

  # 24, 25 sensor record sharing, sensor direction
  values = data.next(2)
  out["sensor_record_sharing"] = {
    "sensor_direction": {
      0: "unspecified",
      1: "input",
      2: "output",
      3: "reserved"
    }[values[0] >> 6],
    "modifier_type": {
      0: "numeric",
      1: "alpha"
    }.get((values[0] & 0b0011_0000) >> 4, "undefined"),
    "share_count": values[0] & 0b0000_1111,
    "sharing": "increments" if values[1] >> 7 else "same",
    "modifier_offset": values[1] & 0b0111_1111
  }

  # 26 positive-going threshold hysteresis value
  out["raw_positive_threshold_hysteresis"] = data.next()[0]

  # 27 negative-going threshold hysteresis value
  out["raw_negative_threshold_hysteresis"] = data.next()[0]

  # 28, 29, 30 - reserved
  out["reserved"] = data.next(3)

  # 31 OEM
  out["oem"] = data.next()[0]

  # 32 device id format + length; 33 onwards device id string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out

def event_only_record(data):
  """Table 43-3 pages 564-565"""
  out = {}

  # 9 - entity ID
  out["entity_id"] = data.next()[0]

  # 10 entity instance
  value = data.next()[0]
  out["entity_instance"] = {
    "type": "logical" if (value >> 7) else "physical",
    "number": value & 0b0111_1111
  }

  # 11 - sensor type (table 36-3)
  out["sensor_type"] = data.next()[0]

  # 12 - event type reading code (table 36-1)
  out["event_reading_type_code"] = data.next()[0]

  # 13,14 - sensor reord sharing/direction
  values = data.next(2)
  out["sensor_record_sharing"] = {
    "sensor_direction": {
      0: "unspecified",
      1: "input",
      2: "output",
      3: "reserved"
    }[values[0] >> 6],
    "modifier_type": {
      0: "numeric",
      1: "alpha"
    }.get((values[0] & 0b0011_0000) >> 4, "undefined"),
    "share_count": values[0] & 0b0000_1111,
    "sharing": "increments" if values[1] >> 7 else "same",
    "modifier_offset": values[1] & 0b0111_1111
  }

  # 15 - reserved
  out["reserved"] = data.next()[0]

  # 16 - OEM
  out["oem"] = data.next()[0]

  # 17, 18 + N -
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def event_association_record_key_bytes(data):

  out = {}
  out["container_entity_id"] = data.next()[0]
  out["container_entity_instance"] = data.next()[0]

  value = data.next()[0]
  out["flags"] = {
    "type": "range" if (value >> 7) else "list",
    "record_link_exists": bool(value & 0b0100_0000),
    "accessible_presence_sensor": bool(value & 0b0010_000),
    "reserved": (value & 0b0001_1111)
  }

  values = data.next(2)
  if ["out"]["type"] == "list":
    out["contained_entity_1"] = values[0]
    out["contained_entity_1_instance"] = values[1]
  else:
    out["range_1_entity"] = values[0]
    out["range_1_first_entity_instance"] = values[1]

  return out

def event_association_record(data, record_type):
  """table 43-4 page 567"""

  out = {}

  values = data.next(6)
  if record_type == "list":
    for i, j in enumerate([2, 3, 4]):
      unspecified = values[i] == 0
      out[f"contained_entity_{j}"] = values[i]
      out[f"contained_entity_{j}_instance"] = 0 if unspecified else values[i+1]
  else:
    unspecified = values[0] == 0
    out["range_1_entity"] = values[0]
    out["range_1_last_entity_instance"] = 0 if unspecified else values[1]

    unspecified = values[2] == 0
    out["range_2_entity"] = values[2]
    out["range_2_first_entity_instance"] = 0 if unspecified else values[3]

    unspecified = values[4] == 0
    out["range_2_entity"] = values[4]
    out["range_2_last_entity_instance"] = 0 if unspecified else values[5]

  return out


# TODO:
# 8 - Entity Association Record
# 9 - Device-relative entity association record
# 16 - generic device locator record
# 17 - FRU device locator record
# 18 - management controller device locator record
# 19 - management controller confirmation record
# 20 - BMC message channel info record
# 192 - OEM record

def main():
  records = []

  with open(fname, "rb") as f:
    file_data = iter(f.read())

  while True:
    try:
      record, record_data = read_header(file_data)
      if record["record_length"] == 0:
        break

      if record["record_type"] == 1:
        record.update(read_record_key_bytes(record_data))
        record.update(full_sensor_record_body_bytes(record_data))
      elif record["record_type"] == 2:
        record.update(read_compact_record_key_bytes(record_data))
        record.update(compact_sensor_record(record_data))
      print(record.get("device_id"), record.get("device_id_fmt"), record)
    except StopIteration:
      break


if __name__ == "__main__":
  main()
