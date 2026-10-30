"""Every name a sketch may use, in one place: the checker validates against it, the stages register against it."""

OPERATORS = ("eq", "ne", "lt", "le", "gt", "ge", "in", "not_in", "has")
COMBINATORS = ("and", "or", "not")
ON_EMPTY = ("fail", "fallback", "skip")  # `walk_away` arrives with the evening example (slice B)

# stage name -> {`with` key: what the value must be}: a source name, a key under `data`, or plain text
STAGES = {
    "etl.split_by_share": {"source": "source", "field": "text", "segments": "data"},
    "etl.join_weights": {"probabilities": "source", "weights": "data"},
    "convert.recipes": {"recipes": "data", "packs": "data"},
}
SINK_PREFIX = "sink."
SKETCH_PREFIX = "sketch."
