"""Every name a sketch may use, in one place: the checker validates against it, the stages register against it."""

OPERATORS = ("eq", "ne", "lt", "le", "gt", "ge", "in", "not_in", "has")
COMBINATORS = ("and", "or", "not")
ON_EMPTY = ("fail", "fallback", "skip")  # `walk_away` arrives with the evening example (slice B)

SINK_PREFIX = "sink."
SKETCH_PREFIX = "sketch."
