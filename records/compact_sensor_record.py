from .sensors import read_record_key_bytes


def compact_sensor_record_body(data):
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


def compact_sensor_record(data):

  out = read_record_key_bytes(data)

  out.update(compact_sensor_record_body(data))

  return out
