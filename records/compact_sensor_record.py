from .common import int_to_bool_array, read_u16
from .decode_device_id import decode_device_id
from .events import event_reading_type
from .sensors import (
  get_sensor_capabilities,
  get_sensor_units,
  read_record_key_bytes,
  sensor_initialization,
  sensor_threashold_reading_masks,
  sensor_type
)


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
  out["initialization"] = sensor_initialization(data.next()[0], compact=True)

  # 12 capabilities
  value = data.next()[0]
  out["capabilities"] = get_sensor_capabilities(value)

  # 13 sensor type
  value = data.next()[0]
  out["type"] = {
    "code": value,
    "name": sensor_type(value)
  }

  # 14 event / reading type code
  value = data.next()[0]
  out["reading_type"] = {
    "code": value,
    **event_reading_type(value)
  }

  # 15/16 asertion event maske / lower threshold reading mask
  is_threshold_based = out["reading_type"]["class"] == "threshold"
  out.update(sensor_threashold_reading_masks(data, is_threshold_based))

  # 21, 22 and 23: Sensor units 1, 2 base unit, 3 modifier unit
  values = data.next(3)
  out.update(get_sensor_units(values, compact=True))

  # 24, 25 sensor record sharing, sensor direction
  values = data.next(2)
  out["sensor_direction"] = {
    0: "unspecified",
    1: "input",
    2: "output",
    3: "reserved"
  }[values[0] >> 6]
  out["sensor_record_sharing"] = {
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
