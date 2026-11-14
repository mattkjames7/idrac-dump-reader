from .events import event_association_flags
from .raw_record_data import RawRecordData


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
  address = value >> 1

  # Contained Entity X Device Channel
  channel = data.next()[0] >> 4
  out[f"contained_entity_{contained_number}_device"] = {
    "address":  address,
    "channel":  channel,
    "device-relative": channel == 0 and address == 0
  }

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
  out.update(read_device_relative_entity_association_block(data,1,1,"first",out["flags"]["type"]))

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


def device_relative_entity_association_record(data):

  out = device_relative_entity_association_record_key_bytes(data)
  record_type = out["flags"]["type"]
  out.update(device_relative_entity_association_record_body(data, record_type))

  return out
