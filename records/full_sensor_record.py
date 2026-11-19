from .common import int_to_bool_array, read_u16, signed_nibble
from .decode_device_id import decode_device_id
from .devices import entity_id_codes
from .events import event_reading_type
from .sensors import (
  get_linearization,
  get_sensor_capabilities,
  get_sensor_units,
  raw_converter,
  raw_hysteresis_converter,
  raw_tolerance_converter,
  read_record_key_bytes,
  sensor_initialization,
  sensor_threashold_reading_masks,
  sensor_type
)

def full_sensor_record_body_bytes(data):

  out = {}

  # 9 - entity id
  out["entity_id"] = entity_id_codes(data.next()[0])

  # 10 - entity instance
  instance = data.next()[0]
  out["physical"] = (instance >> 7) == 0  # or logical
  out["number"] = instance & 0x7f

  # 11 - sensor initialization
  out["initialization"] = sensor_initialization(data.next()[0])

  # 12 - sensor capabilities
  value = data.next()[0]
  out["capabilities"] = get_sensor_capabilities(value)

  # 13 - sensor type
  value = data.next()[0]
  out["type"] = {
    "code": value,
    "name": sensor_type(value)
  }

  # 14 - event/reading type code
  value = data.next()[0]
  out["reading_type"] = {
    "code": value,
    **event_reading_type(value)
  }

  # 15 - 20
  is_threshold_based = out["reading_type"]["class"] == "threshold"
  out.update(sensor_threashold_reading_masks(data, is_threshold_based))

  # 21-23 - sensor units 1, 2 and 3
  values = data.next(3)
  out.update(get_sensor_units(values))

  # 24 - linearization
  out["linearization"] = get_linearization(data.next()[0])

  # 25, 26 - M and Tolerance
  value = data.next(2)  # is 10 bit signed + tolerance
  m_lsb = value[0]
  m_msb = (value[1] >> 6) << 8
  m_raw = m_lsb | m_msb
  out["m"] = m_raw - 512 if (m_raw & 0x200) else m_raw
  out["tolerance_raw"] = value[1] & 0b00111111

  # 27, 28, 29 - B, Accuracy
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

  # 30 - R and B exp
  value = data.next()[0]
  out["r_exp"] = signed_nibble(value >> 4)
  out["b_exp"] = signed_nibble(value)

  value_convert = raw_converter(
    out["m"],
    out["b"],
    out["b_exp"],
    out["r_exp"],
    out["units"]["format"]["name"],
    out["linearization"]
  )

  is_numeric = out["units"]["format"]["code"] != 3
  if is_numeric:
    out["tolerance"] = raw_tolerance_converter(
      out["tolerance_raw"],
      out["m"],
      out["r_exp"],
      out["linearization"]
    )

  # 31 - analog characteristics
  value = data.next()[0]
  out["has_normal_min"] = bool((value & 0b00000100) >> 2)
  out["has_normal_max"] = bool((value & 0b00000010) >> 1)
  out["has_nominal_reading"] = bool(value & 0b00000001)

  # 32-34 - nominal reading, min and max

  out["nominal_reading_raw"] = data.next()[0]
  out["nominal_reading"] = value_convert(out["nominal_reading_raw"], out["has_nominal_reading"] and is_numeric)

  out["normal_maximum_raw"] = data.next()[0]
  out["normal_maximum"] = value_convert(out["normal_maximum_raw"], out["has_normal_max"] and is_numeric)

  out["normal_minimum_raw"] = data.next()[0]
  out["normal_minimum"] = value_convert(out["normal_minimum_raw"], out["has_normal_min"] and is_numeric)

  # 35-36 - sensor range
  out["sensor_maximum_raw"] = data.next()[0]
  out["sensor_maximum"] = value_convert(out["sensor_maximum_raw"], is_numeric)

  out["sensor_minimum_raw"] = data.next()[0]
  out["sensor_minimum"] = value_convert(out["sensor_minimum_raw"], is_numeric)

  # 37-44 thresholds
  out["upper_non-recoverable_threshold_raw"] = data.next()[0]
  out["upper_critical_threshold_raw"] = data.next()[0]
  out["upper_non-critical_threshold_raw"] = data.next()[0]
  out["lower_non-recoverable_threshold_raw"] = data.next()[0]
  out["lower_critical_threshold_raw"] = data.next()[0]
  out["lower_non-critical_threshold_raw"] = data.next()[0]

  if is_threshold_based and is_numeric:
    out["upper_non-recoverable_threshold"] = value_convert(
      out["upper_non-recoverable_threshold_raw"],
      (
        out["threshold_settable_mask"]["upper_non-recoverable"] |
        out["threshold_readable_mask"]["upper_non-recoverable"] |
        out["upper_threshold_reading_mask"]["non-recoverable"]
      )
    )
    out["upper_critical_threshold"] = value_convert(
      out["upper_critical_threshold_raw"],
      (
        out["threshold_settable_mask"]["upper_critical"] |
        out["threshold_readable_mask"]["upper_critical"] |
        out["upper_threshold_reading_mask"]["critical"]
      )
    )
    out["upper_non-critical_threshold"] = value_convert(
      out["upper_non-critical_threshold_raw"],
      (
        out["threshold_settable_mask"]["upper_non-critical"] |
        out["threshold_readable_mask"]["upper_non-critical"] |
        out["upper_threshold_reading_mask"]["non-critical"]
      )
    )
    out["lower_non-recoverable_threshold"] = value_convert(
      out["lower_non-recoverable_threshold_raw"],
      (
        out["threshold_settable_mask"]["lower_non-recoverable"] |
        out["threshold_readable_mask"]["lower_non-recoverable"] |
        out["lower_threshold_reading_mask"]["non-recoverable"]
      )
    )
    out["lower_critical_threshold"] = value_convert(
      out["lower_critical_threshold_raw"],
      (
        out["threshold_settable_mask"]["lower_critical"] |
        out["threshold_readable_mask"]["lower_critical"] |
        out["lower_threshold_reading_mask"]["critical"]
      )
    )
    out["lower_non-critical_threshold"] = value_convert(
      out["lower_non-critical_threshold_raw"],
      (
        out["threshold_settable_mask"]["lower_non-critical"] |
        out["threshold_readable_mask"]["lower_non-critical"] |
        out["lower_threshold_reading_mask"]["non-critical"]
      )
    )

  out["positive-going_threshold_hysteresis_value_raw"] = data.next()[0]
  out["negative-going_threshold_hysteresis_value_raw"] = data.next()[0]
  supports_hysteresis = out["capabilities"]["hysteresis"]["supported"]
  if supports_hysteresis and is_threshold_based and is_numeric:
    out["positive-going_threshold_hysteresis_value"] = raw_hysteresis_converter(
      out["positive-going_threshold_hysteresis_value_raw"],
      out["m"],
      out["r_exp"],
      out["linearization"]
    )
    out["negative-going_threshold_hysteresis_value"] = raw_hysteresis_converter(
      out["negative-going_threshold_hysteresis_value_raw"],
      out["m"],
      out["r_exp"],
      out["linearization"]
    )

  #  45,46 - reserved
  out["reserved"] = data.next(2)

  # 47 - OEM
  out["oem"] = data.next()[0]

  # 48 onwards
  out["device_id_fmt"], out["device_id"] = decode_device_id(data)

  return out


def full_sensor_record(data):

  out = read_record_key_bytes(data, include_fru=False)
  out.update(full_sensor_record_body_bytes(data))

  return out
