from records.raw_record_data import RawRecordData
from records.header import read_header
from records.decode_device_id import decode_device_id

fname = "sdr.bin"








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

  # 11 - sensor type
  out["sensor_type"] = sensor_type(data.next()[0])

  # 12 - event type reading code
  out["event_reading_type_code"] = event_reading_type(data.next()[0])

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


def fru_device_locator_body(data):

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
