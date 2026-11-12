
class RawRecordData:
  def __init__(self, data):
    self.iterator = iter(data)

  def next(self, n=1):
    if not isinstance(n, int) and not n == "all":
      raise ValueError

    items = []
    try:
      if n == "all":
        items = list(self.iterator)
      else:
        items = [next(self.iterator) for _ in range(n)]
    except StopIteration:
      pass
    return items
