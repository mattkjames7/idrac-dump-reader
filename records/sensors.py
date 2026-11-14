from .common import int_to_bool_array, read_u16


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


def get_sensor_units(values, compact=False):

  out = {}

  if not compact:
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

  if compact:
    out["units"]["reserved"] = values[0] >> 6
  else:
    out["units"]["format"] = {
      "code": format_value,
      "name": format_name
    },

  out["base_unit"] = get_sensor_unit_type(values[1])
  out["modifier_unit"] = get_sensor_unit_type(values[2])
  return out



def get_sensor_capabilities(value, compact=False):

  hyst_value = (value & 0b00110000) >> 4
  hysteresis = {
    "supported": hyst_value != 0,
    "readable": hyst_value in [1, 2],
    "settable": hyst_value == 2,
    "fixed": hyst_value == 3
  }
  thresh_value = (value & 0b00001100) >> 2
  threshold = {
    "supported": thresh_value not in (0,2) if compact else (0,),
    "readable": thresh_value in ((1,) if compact else (1, 2)),
    "settable": (thresh_value == 2) & (compact == False),
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


def read_record_key_bytes(data, include_fru=True):

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
  key = "reserved" if not include_fru else "fru_inventory_device_owner"
  out[key] = (value & 0b0000_1100) >> 2 if include_fru else 0
  out["sensor_owner_lun"] = value & 0b0000_0011

  # 8 sensor number
  out["sensor_number"] = data.next()[0]

  return out


def sensor_initialization(value, compact=False):
  threshold_key = "reserved" if compact else "thresholds"
  return {
    "settable": (value & 0b10000000) >> 7,
    "scanning": (value & 0b01000000) >> 6,
    "events": (value & 0b00100000) >> 5,
    threshold_key: 0 if compact else (value & 0b00010000) >> 4,
    "hysteresis": (value & 0b00001000) >> 3,
    "sensor_type": (value & 0b00000100) >> 2,
    "default_state": {
      "generation": (value & 0b00000010) >> 1,
        "scanning": (value & 0b00000001)
    }
  }


def get_linearization(value):

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
  masked_value = value & 0b01111111
  if masked_value in LINEARIZATION:
      linearization = LINEARIZATION[masked_value]
  elif masked_value == 0x70:
      linearization = "non-linear"
  elif 0x71 <= masked_value <= 0x7F:
      linearization = "OEM-defined"
  else:
      linearization = "reserved"
  return linearization


def sensor_threashold_reading_masks(data, is_threshold_based):
  """Common to both compact and full sensor records"""

  out = {}

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

  return out
