from records.raw_record_data import RawRecordData

fname = "sdr.bin"





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


def device_type_code(values):

  options = {
    0x02: ("DS1624 temperature sensor / EEPROM", "other"),
    0x03: ("DS1621 temperature sensor", "other"),
    0x04: ("LM75 Temperature Sensor", "other"),
    0x05: ("‘Heceta’ ASIC", "heceta"),
    0x08: ("EEPROM / 24C01", "eeprom"),
    0x09: ("EEPROM / 24C02", "eeprom"),
    0x0a: ("EEPROM / 24C04", "eeprom"),
    0x0b: ("EEPROM / 24C08", "eeprom"),
    0x0c: ("EEPROM / 24C16", "eeprom"),
    0x0d: ("EEPROM / 24C17", "eeprom"),
    0x0e: ("EEPROM / 24C32", "eeprom"),
    0x0f: ("EEPROM / 24C64", "eeprom"),
    0x10: ("FRU Inventory Device", "fru"),
    0x14: ("PCF 8570 256 byte RAM", "other"),
    0x15: ("PCF 8573 clock/calendar", "other"),
    0x16: ("PCF 8574A ‘i/o port’", "other"),
    0x17: ("PCF 8583 clock/calendar", "other"),
    0x18: ("PCF 8593 clock/calendar ", "other"),
    0x19: ("Clock calendar", "other"),
    0x1a: ("PCF 8591 A/D, D/A Converter", "other"),
    0x1b: ("i/o port, specific device not specified", "other"),
    0x1c: ("A/D Converter, specific device not specified", "other"),
    0x1d: ("D/A Converter, specific device not specified", "other"),
    0x1e: ("A/D, D/A Converter, specific device not specified", "other"),
    0x1f: ("LCD controller / Driver, specific device not specified", "other"),
    0x20: ("Core Logic (Chip set) Device, specific device not specified", "other"),
    0x21: ("LMC6874 Intelligent Battery controller, or equivalent", "other"),
    0x22: ("Intelligent Battery controller, specific device not specified", "other"),
    0x23: ("Combo Management ASIC, specific device not specified", "other"),
    0x24: ("Maxim 1617 Temperature Sensor", "other"),
    0xbf: ("Other / unspeicified device", "other")
  }

  if values[0] in options:
    device_type, modifier_type = options[values[0]]

    if modifier_type == "heceta":
      modifier = {
        0: "Heceta 1 e.g. LM78",
        1: "Heceta 2 e.g. LM79",
        2: "LM80",
        3: "Heceta 3 e.g. LM81/ ADM9240 / DS1780",
        4: "Heceta 4",
        5: "Heceta 5"
      }.get(values[1], "unknown")
    elif modifier_type == "eeprom":
      modifier = {
        0: "unspecified",
        1: "DIMM Memory ID",
        2: "IPMI FRU Inventory",
        3: "System Processor Cartridge FRU / PIROM"
      }.get(values[1], "reserved")
    elif modifier_type == "fru":
      modifier = {
        0: "IPMI FRU Inventory",
        1: "DIMM Memory ID",
        2: "IPMI FRU Inventory",
        3: "System Processor Cartridge FRU / PIROM",
        0xff: "unspecified"
      }.get(values[1], "reserved")
    else:
      modifier = "unspecified" if values[1] == 0 else values[1]

    return device_type, modifier
  elif (values[0] >= 0xc0) & (values[0] <= 0xff):
    return "OEM specified device", "OEM specific"
  else:
    return "reserved", "n/a"


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


def entity_id_codes(value):

  entities = {
    0x00: "unspecified",
    0x01: "other",
    0x02: "unknown",
    0x03: "processor",
    0x04: "disk or disk bay",
    0x05: "peripheral bay",
    0x06: "system management module",
    0x07: "system board",
    0x08: "memory module",
    0x09: "processor module",
    0x0a: "power supply",
    0x0b: "add-in card",
    0x0c: "front panel board",
    0x0d: "back panel board",
    0x0e: "power system board",
    0x0f: "drive backplane",
    0x10: "system internal expansion board ",
    0x11: "Other system board",
    0x12: "processor board",
    0x13: "power unit / power domain",
    0x14: "power module / DC-to-DC converter",
    0x15: "power management / power distribution board",
    0x16: "chassis back panel board",
    0x17: "system chassis",
    0x18: "sub-chassis",
    0x19: "Other chassis board",
    0x1a: "Disk Drive Bay",
    0x1b: "Peripheral Bay",
    0x1c: "Device Bay",
    0x1d: "fan / cooling device",
    0x1e: "cooling unit / cooling domain",
    0x1f: "cable / interconnect",
    0x20: "memory device",
    0x21: "System Management Software",
    0x22: "System Firmware",
    0x23: "Operating System",
    0x24: "system bus",
    0x25: "Group",
    0x26: "Remote (Out of Band) Management Communication Device",
    0x27: "External Environment",
    0x28: "battery",
    0x29: "Processing blade",
    0x2a: "Connectivity switch",
    0x2b: "Processor/memory module",
    0x2c: "I/O module",
    0x2d: "Processor/ IO module",
    0x2e: "Management Controller Firmware",
    0x2f: "IPMI Channel",
    0x30: "PCI Bus",
    0x31: "PCI Express™ Bus",
    0x32: "SCSI Bus (parallel)",
    0x33: "SATA / SAS bus",
    0x34: "Processor / front-side bus",
    0x35: "Real Time Clock (RTC)",
    0x37: "air inlet",
    0x40: "air inlet",
    0x41: "processor / CPU ",
    0x42: "baseboard / main system board ",
  }

  if value in entities:
    return entities[value]

  if (value >= 0x90) & (value <= 0xaf):
    return "Chassis-specific"

  if (value >= 0xb0) & (value <= 0xcf):
    return "Board-set-specific"

  if (value >= 0xd0) & (value <= 0xff):
    return "OEM defined"

  return "reserved"


def compact_sensor_record(data):
  """Table 43-2 - page 558-563"""

  out = {}

  # 9 entity ID -> 43-13
  out["entity_id"] = data.next()[0]  # TODO

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
  out["sensor_type"] = data.next()[0]  # TODO

  # 12 - event type reading code (table 36-1)
  out["event_reading_type_code"] = data.next()[0]  # TODO

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


def event_association_flags(value):

  out = {
    "type": "range" if (value >> 7) else "list",
    "record_link_exists": bool(value & 0b0100_0000),
    "accessible_presence_sensor": bool(value & 0b0010_000),
    "reserved": (value & 0b0001_1111)
  }
  return out


def event_association_record_key_bytes(data):

  out = {}
  out["container_entity_id"] = data.next()[0]
  out["container_entity_instance"] = data.next()[0]

  value = data.next()[0]
  out["flags"] = event_association_flags(value)

  values = data.next(2)
  if out["flags"]["type"] == "list":
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


def read_device_relative_entity_association_block(
  data: RawRecordData,
  contained_number: int,
  range_number: int,
  range_type: str,  # first|last
  record_type: str
) -> dict:

  out = {}

  # Contained Entity X Device Address
  value = data.next()[0]
  device_relative = value == 0
  address = value >> 1

  # Contained Entity X Device Channel
  channel = data.next()[0] >> 4
  out[f"contained_entity_{contained_number}_device"] = {
    "address":  address,
    "channel":  channel,
    "device-relative": device_relative
  }

  record_type = out["flags"]["type"]
  # Contained Entity X / Range X Entity ID
  value = data.next()[0]
  if record_type == "list":
    out[f"contained_entity_{contained_number}_id"] = value
  else:
    out[f"range_{range_number}_entity_id"] = value

  # Contained Entity X Instance /  Range X first/last entity instance
  value = data.next()[0]
  if record_type == "list":
    out[f"contained_entity_{contained_number}_instance"] = value
  else:
    out[f"range_{range_number}_{range_type}_entity_instance"] = value

  return out


def device_relative_entity_association_record_key_bytes(data):

  out = {}
  out["container_entity_id"] = data.next()[0]
  out["container_entity_instance"] = data.next()[0]

  # 8 - Container Entity Device Address
  value = data.next()[0]
  address = value >> 1

  # 9 - Container Entity Device Channel
  channel = data.next()[0] >> 4  # remove the reserved bits

  out["container_entity_device"] = {
    "address": address,
    "channel": channel,
    "device-relative": channel == 0
  }

  # 10 - flags
  value = data.next()[0]
  out["flags"] = event_association_flags(value)

  # 11 - Contained Entity 1 Device Address
  # 12 - Contained Entity 1 Device Channel
  # 13 - Contained Entity 1 / Range 1 Entity ID
  # 14 - Contained Entity 1 Instance /  Range 1 first entity instance
  out.update(read_device_relative_entity_association_block(data,1,1,"first",record_type))

  return out


def device_relative_entity_association_record_body(data, record_type):

  out = {}

  # 15 - Contained Entity 2 Device Address
  # 16 - Contained Entity 2 Device Channel
  # 17 - Contained Entity 2 / Range 1 Entity ID
  # 18 - Contained Entity 2 Instance /  Range 1 last entity instance
  out.update(read_device_relative_entity_association_block(data,2,1,"last",record_type))

  # 19 - Contained Entity 3 Device Address
  # 20 - Contained Entity 3 Device Channel
  # 21 - Contained Entity 3 / Range 2 Entity ID
  # 22 - Contained Entity 3 Instance /  Range 2 first entity instance
  out.update(read_device_relative_entity_association_block(data,3,2,"first",record_type))

  # 23 - Contained Entity 4 Device Address
  # 24 - Contained Entity 4 Device Channel
  # 25 - Contained Entity 4 / Range 2 Entity ID
  # 26 - Contained Entity 4 Instance /  Range 2 last entity instance
  out.update(read_device_relative_entity_association_block(data,4,2,"last",record_type))

  return out


def generic_device_locator_record_key_bytes(data):

  out = {}

  value = data.next()[0]
  address = value >> 0
  out["device_access_address"] = address
  out["on_ipmb"] = address == 0

  value  = data.next()[0]
  out["device_slave_address"] = value >> 1
  channel_msb = value & 0b1

  value = data.next()[0]
  out["channel_number"] = (channel_msb << 3) | (value >> 5)
  out["access_lun"] = (value & 0b0001_1000) >> 3
  out["bus_id"] = value & 0b0000_0111

  return out


def generic_device_locator_record_body(data):

  out = {}

  # 9 - address span
  out["address_span"] = data.next()[0] & 0b0000_0111  # ignore reserved bits

  # 10 - skip reserved
  _ = data.next()

  # 11 - device type (from table 43-12)
  # 12 - device type modifier (from table 43-12)
  out["device_type"], out["device_modifier"] = device_type_code(data.next(2))

  # 13 - entity id
  out["entity_id"] = data.next()[0]

  # 14 - entity instance
  out["entity_instance"] = data.next()[0]

  # 15 - OEM
  out["oem"] = data.next()[0]

  # 16 onward - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def fru_device_locator_record_key_bytes(data):

  out = {}
  out["device_access_address"] = data.next()[0] >> 1

  # I think we need the following byte to define this one
  fru_address = data.next()[0]

  value = data.next()[0]
  out["fru_device_type"] = "logical" if value >> 7 else "physical"
  out["lun"] = (value & 0b0001_1000) >> 3
  out["bus_id"] = value & 0b0000_0111

  if out["fru_device_type"] == "logical":
    out["logical_fru_device"] = fru_address
  else:
    out["device_slave_address"] = fru_address >> 1

  out["channel_number"] = data.next()[0] >> 4

  return out


def fru__device_locator_body(data):

  out = {}

  # 10 - reserved
  _ = data.next()[0]

  # 11 - device type (from table 43-12)
  # 12 - device type modifier (from table 43-12)
  out["device_type"], out["device_modifier"] = device_type_code(data.next(2))

  # 13 - FRU entity id
  out["fru_entity_id"] = data.next()[0]

  # 14 - FRU entity instance
  out["fru_entity_instance"] = data.next()[0]

  # 15 - OEM
  _ = data.next()[0]

  # 16 onwards - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def management_controller_device_record_key_bytes(data):

  out = {}

  out["device_slave_address"] = data.read()[0] >> 1

  out["channel_number"] = data.read()[0] & 0b1111

  return out


def management_controller_device_body(data):
  """table 43-8, page 573-574"""
  out = {}

  # 8 - power state notification / global initialization
  value = data.next()[0]
  out["power_state_notification"] = {
    "acpi_system": bool(value & 0b1000_0000),
    "acpi_device": bool(value & 0b0100_0000),
    "controller": bool(value & 0b0010_0000)
  }
  out["global_initialization"] = {
    "controller_logs_agent_error": bool(value & 0b0000_1000),
    "log_agent_access_error": bool(value & 0b0000_0100),
    "event_message_generation": {
      0: "enabled",
      1: "disabled",
      2: "controller_not_initialized"
    }.get(value & 0b0000_0011, "reserved")
  }

  # 9 - device capabilities
  value = data.next()[0]
  out["capabilities"] = {
    "chassis_device": bool(value & 0b1000_0000),
    "bridge": bool(value & 0b0100_0000),
    "ipmb_event_generator": bool(value & 0b0010_0000),
    "ipmb_event_receiver": bool(value & 0b0001_0000),
    "fru_inventory_device": bool(value & 0b0000_1000),
    "sel_device": bool(value & 0b0000_0100),
    "sdr_repository_device": bool(value & 0b0000_0010),
    "sensor_device": bool(value & 0b0000_0001)
  }

  # 10 - 12 - reserved
  _ = data.next(3)

  # 13 - entity id
  out["entity_id"] = data.next()[0]

  # 14 - entity instance
  out["entity_instance"] = data.next()[0]

  # 15 - OEM
  out["oem"] = data.next()[0]

  # 16 onwards - device ID string
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def bytes_to_guid(values):

  chars = []
  ranges = [
    [0,4],
    [4,6],
    [6,8],
    [8,10],
    [10,16]
  ]

  for i, rng in enumerate(ranges):
    for x in values[rng[0]:rng[1]]:
      chars.append(f"{x:02x}")
    if i < len(ranges) - 1:
      chars.append("-")
  return "".join(chars)


def management_controller_confirmation_record_key_bytes(data):

  out = {}

  out["device_slave_adress"] = data.next()[0] >> 1
  out["device_id"] = data.next()[0]

  value = data.next()[0]
  out["channel_number"] = value >> 4
  out["device_revision"] = value & 0b0000_1111

  return out


def management_controller_confirmation_body(data):
  """Table 43-9, page 575"""
  out = {}

  # 9 - firmware major revision
  major = data.next()[0] & 0b0111_1111

  # 10 - firmware minor revision
  minor = data.next()[0]

  out["firmware_revision"] = f"{major}.{minor}"

  # 11 - IPMI version
  value = data.next()[0]
  lsd = value >> 4
  msd = value & 0b0000_1111
  out["ipmi_version"] = f"{msd}.{lsd}"

  # 12 - 14 - manufacturer id
  values = data.next(3)
  out["manufacturer_id"] = int(
    ((values[2] & 0b0000_1111) << 16)
    | (values[1] << 8)
    | values[0]
  )

  # 15 -16 - product id
  values = data.next(2)
  out["product_id"] = int((values[1] << 8) | values[0])

  # 17 - 32 - device guid
  out["device_guid"] = bytes_to_guid(data.next(16))

  return out


def channel_info(value):

  out = {}
  out["transmit_supported"] = bool(value & 0b1000_0000)
  mess_lun_val = (value & 0b0111_0000) >> 4
  if mess_lun_val <= 0b0011:
    out["message_receive_lun"] = mess_lun_val
  elif mess_lun_val == 0b0111:
    out["message_receive_lun"] = "no LUN"
  else:
    out["message_receive_lun"] = "reserved"

  proto = value & 0b0000_1111
  proto_dict = {
    0: "not present",
    1: "IPMB",
    2: "ICMB v1.0",
    3: "ICMB v0.9",
    4: "SMBus v1.0",
    5: "System Format",
    0xc: "OEM Protocol 1",
    0xd: "OEM Protocol 2",
    0xe: "OEM Protocol 3",
    0xf: "OEM Protocol 4",
  }
  out["protocol"] = proto_dict.get(proto, "reserved")

  return out


def interrupt_type(value):

  if (value >=0) &  (value <= 0x0f):
    return f"IRQ {value}"
  elif (value >= 0x10) & (value <= 0x13):
    letter = chr(ord('a') + 0).upper()
    return f"PCI {letter}"
  elif value == 0x14:
    return "SMI"
  elif value == 0x15:
    return "SCI"
  elif (value >= 0x20) & (value <= 0x5f):
    return f"system interrupt {value - 0x20}"
  elif value == 0x60:
    return "ACPI / Plug 'n Play BIOS"
  elif value == 0xff:
    return "no interrupt"
  else:
    return "reserved"


def bmc_message_channel_info_record(data):

  out = {}
  for i in range(8):
    out[f"channel_{i}"] = channel_info(data.next()[0])

  out["messaging_interrupt_type"] = interrupt_type(data.next()[0])
  out["event_message_buffer_interrupt_type"] = interrupt_type(data.next()[0])

  return out


def oem_record(data, record_length):
  """Table 43-11, page 578"""

  man_id_bytes = data.next(3)
  man_id = (
      ((man_id_bytes[2] & 0x0f) << 16)
      | (man_id_bytes[1] << 8)
      | man_id_bytes[0]
  )
  out = {
    "manufacturer_id": "f{man_id:06x}",
    "data": data.next("all")
  }

  return out


def main():

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
