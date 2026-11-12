
def bmc_message_channel_info_record(data):

  out = {}
  for i in range(8):
    out[f"channel_{i}"] = channel_info(data.next()[0])

  out["messaging_interrupt_type"] = interrupt_type(data.next()[0])
  out["event_message_buffer_interrupt_type"] = interrupt_type(data.next()[0])

  return out
