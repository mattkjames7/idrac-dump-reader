from .common import int_to_bool_array, read_u16, signed_nibble
from .decode_device_id import decode_device_id
from .events import event_reading_type
from .sensors import (
  get_linearization,
  get_sensor_capabilities,
  get_sensor_units,
  read_record_key_bytes,
  sensor_initialization,
  sensor_threashold_reading_masks,
  sensor_type
)


def full_sensor_record_body_bytes(data):

  out = {}
  out["id"] = data.next()[0]

  instance = data.next()[0]
  out["physical"] = (instance >> 7) == 0  # or logical
  out["number"] = instance & 0x7f

  out["initialization"] = sensor_initialization(data.next()[0])

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
  out.update(sensor_threashold_reading_masks(data, is_threshold_based))

  values = data.next(3)
  out.update(get_sensor_units(values))

  out["linearization"] = get_linearization(data.next()[0])

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
  out["sensor_direction"] = {
    0: "unspecified",
    1: "input",
    2: "output",
    3: "reserved"
  }[value & 0b00000011]

  value = data.next()[0]
  out["r_exp"] = signed_nibble(value >> 4)
  out["b_exp"] = signed_nibble(value)

  # analog characteristics
  value = data.next()[0]
  out["has_normal_min"] = bool((value & 0b00000100) >> 2)
  out["has_normal_max"] = bool((value & 0b00000010) >> 1)
  out["has_nominal_reading"] = bool(value & 0b00000001)

  out["nominal_reading_raw"] = data.next()[0]
  out["normal_maximum_raw"] = data.next()[0]
  out["normal_minimum_raw"] = data.next()[0]
  out["sensor_maximum_raw"] = data.next()[0]
  out["sensor_minimum_raw"] = data.next()[0]
  out["upper_non-recoverable_threshold_raw"] = data.next()[0]
  out["upper_critical_threshold_raw"] = data.next()[0]
  out["upper_non-critical_threshold_raw"] = data.next()[0]
  out["lower_non-recoverable_threshold_raw"] = data.next()[0]
  out["lower_critical_threshold_raw"] = data.next()[0]
  out["lower_non-critical_threshold_raw"] = data.next()[0]
  out["positive-going_threshold_hysteresis_value"] = data.next()[0]
  out["negative-going_threshold_hysteresis_value"] = data.next()[0]

  #  reserved
  out["reserved"] = data.next(2)

  # OEM
  out["oem"] = data.next()[0]

  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def full_sensor_record(data):

  out = read_record_key_bytes(data)
  out.update(full_sensor_record_body_bytes(data))

  return out
