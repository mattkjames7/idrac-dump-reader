from .events import event_association_flags


def entity_association_record_key_bytes(data):

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

def entity_association_record_body(data, record_type):
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


def entity_association_record(data):

  out = entity_association_record_key_bytes(data)
  record_type = out["flags"]["type"]
  out.update(entity_association_record_body(data, record_type))

  return out
