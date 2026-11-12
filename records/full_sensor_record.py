from .common import read_u16, int_to_bool_array, signed_nibble
from .decode_device_id import decode_device_id
from .sensors import (
  get_sensor_capabilities,
  read_record_key_bytes,
  sensor_type
)


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


def full_sensor_record(data):

  out = read_record_key_bytes(data)
  out.update(full_sensor_record_body_bytes(data))

  return out
