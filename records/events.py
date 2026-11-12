

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


def event_association_flags(value):

  out = {
    "type": "range" if (value >> 7) else "list",
    "record_link_exists": bool(value & 0b0100_0000),
    "accessible_presence_sensor": bool(value & 0b0010_000),
    "reserved": (value & 0b0001_1111)
  }
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
