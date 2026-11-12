
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
