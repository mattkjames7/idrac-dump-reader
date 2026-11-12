from .sensors import read_record_key_bytes


def event_only_record_body(data):
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


def event_only_record(data):

  out = read_record_key_bytes(data)

  out.update(event_only_record_body(data))

  return out
