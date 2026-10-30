"""Every name a sketch may use, in one place: the checker validates against it, the stages register against it."""

OPERATORS = ("eq", "ne", "lt", "le", "gt", "ge", "in", "not_in", "has")
COMBINATORS = ("and", "or", "not")
ON_EMPTY = ("fail", "fallback", "skip")  # `walk_away` arrives with the evening example (slice B)


# The kinds of stage a state's `do:` can name, each with the one field that names which (owner, 2026-10-30):
#   do: { etl: { action: split_by_share } }     do: { sink: { name: ingredients } }
#   do: { convert: { action: recipes } }        do: { sketch: { file: seating } }
STAGE_TYPES = {"etl": "action", "convert": "action", "sink": "name", "sketch": "file"}


def stage_of(state: dict) -> tuple[str, str] | None:
    """The (type, name) a state's `do:` names, or None when it has no `do:`."""
    do = state.get("do")
    if not do:
        return None
    ((kind, fields),) = do.items()
    return kind, fields[STAGE_TYPES[kind]]
