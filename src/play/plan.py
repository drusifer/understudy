"""The plan of a play: its stage's pieces, its beats, who reads what, and the moves between beats (UND-111).

`plan` reads a play as written (the document `read_template` gives, no values needed) and returns a graph the console
lays out and draws. A read piece, a write piece and a beat are nodes; an edge is a `move` (a beat's `to:` or a
`transitions:` entry), a `reads` (a piece or beat feeding a beat) or a `writes` (a `write` beat feeding its piece). Props
are not nodes: they are values, listed by name. The names a beat reads come from the same place `check` looks: the
parameters its action declares as `Source`, plus `each`, a Jev beat's options and state, and a called play's bindings.
"""

import json

import src.play.stages  # noqa: F401 - importing it registers the stages
from src.play.loader import is_flow
from src.play.registry import STAGES, Source

PLAY_KEYS = {"source": "from", "sources": "from"}  # the engine's parameter name -> the play's `with:` key


def plan(document: dict) -> dict:
    """The graph of `document`: `nodes`, `edges`, `props` and the scene's `initial` beat."""
    stage = document.get("stage") or {}
    pieces = {name: entry for name, entry in stage.items() if isinstance(entry, dict) and entry.get("kind") == "file"}
    props = [name for name in stage if name not in pieces]
    beats = document["scene"]["beats"]
    known = set(pieces) | set(beats)
    nodes = [{"id": name, "kind": "piece", "write": entry.get("access") == "write", "flow": False, "final": False,
              "waits": False, "action": None, "with": None} for name, entry in pieces.items()]
    edges = []
    for name, beat in beats.items():
        nodes.append({"id": name, "kind": "beat", "write": False, "flow": is_flow(beat), "final": bool(beat.get("final")),
                      "waits": not is_flow(beat), "action": _action(beat), "with": _with_text(beat)})
        edges.extend({"from": each, "to": name, "kind": "reads"} for each in _reads(beat, known) if each != name)
        edges.extend(_moves(name, beat))
        written = beat.get("do", {}).get("write")
        if written in pieces:
            edges.append({"from": name, "to": written, "kind": "writes"})
    return {"nodes": nodes, "edges": edges, "props": props, "initial": document["scene"].get("initial")}


AUTO_FOLD = 40  # a play with more nodes than this is shown as its flow unless the person asks for everything
VIEWS = ("auto", "flow", "all")


def fold(found: dict, view: str = "auto") -> dict:
    """`found` (a plan) as the `view` asks: `all` is the plan itself, `flow` keeps the files and the beats of the flow and
    passes each read through the beats that wait to be read (a flow beat reads the files and flow beats those beats read, one
    arrow each), and `auto` is `flow` for a play of more than `AUTO_FOLD` nodes and `all` for any other. The answer says
    which it is (`view`), how many beats the flow view hides (`hidden`) and how many nodes the whole plan has (`total`)."""
    if view not in VIEWS:
        raise ValueError(f"the view is one of {', '.join(VIEWS)}, not {view!r}")
    hidden = sum(1 for each in found["nodes"] if each["waits"])
    chosen = ("flow" if len(found["nodes"]) > AUTO_FOLD else "all") if view == "auto" else view
    facts = {"view": chosen, "hidden": hidden, "total": len(found["nodes"])}
    if chosen == "all":
        return {**found, **facts}
    waiting = {each["id"] for each in found["nodes"] if each["waits"]}
    reading: dict[str, list[str]] = {}
    for each in found["edges"]:
        if each["kind"] == "reads":
            reading.setdefault(each["to"], []).append(each["from"])

    def sources(name: str, seen: set[str]) -> list[str]:
        """What `name` reads once the waiting beats between are passed through (a beat is passed once, so a cycle ends)."""
        found_here = []
        for source in reading.get(name, []):
            if source in waiting:
                if source not in seen:
                    seen.add(source)
                    found_here.extend(sources(source, seen))
            elif source not in found_here:
                found_here.append(source)
        return found_here

    kept = [each for each in found["nodes"] if each["id"] not in waiting]
    ids = {each["id"] for each in kept}
    folded = [each for each in found["edges"] if each["kind"] != "reads" and each["from"] in ids and each["to"] in ids]
    for each in kept:
        folded.extend({"from": source, "to": each["id"], "kind": "reads"}
                      for source in dict.fromkeys(sources(each["id"], {each["id"]})) if source in ids and source != each["id"])
    return {**found, "nodes": kept, "edges": folded, **facts}


def _action(beat: dict) -> str | None:
    """What a beat does, in a few words: `map.join`, `jev.choice`, `write:booking`, `play:seating.yaml`."""
    if not beat.get("do"):
        return None
    ((kind, value),) = beat["do"].items()
    if kind in ("map", "reduce"):
        return f"{kind}.{value['action']}"
    if kind == "jev":
        return f"jev.{value['question']}"
    return f"{kind}:{value}"


WITH_CHARS = 160  # the most of a beat's `with` the plan keeps: enough to tell what it asks, not a copy of the file


def _with_text(beat: dict) -> str | None:
    """A beat's `with:` as one short line of JSON, cut with `...` when it is long (None when it has none)."""
    given = beat.get("with")
    if not given:
        return None
    text = json.dumps(given, ensure_ascii=False, default=str)
    return text if len(text) <= WITH_CHARS else text[:WITH_CHARS - 3] + "..."


def _moves(name: str, beat: dict) -> list[dict]:
    moves = [{"from": name, "to": beat["to"], "kind": "move"}] if "to" in beat else []
    moves.extend({"from": name, "to": each["to"], "kind": "move", **({"when": each["if"]} if "if" in each else {})}
                 for each in beat.get("transitions", []))
    return moves


def _reads(beat: dict, known: set[str]) -> list[str]:
    """The pieces and beats `beat` reads, once each, in the order it names them."""
    found: list[str] = []

    def add(value) -> None:
        for each in value if isinstance(value, list) else [value]:
            if isinstance(each, str) and each in known and each not in found:
                found.append(each)

    given = beat.get("with") or {}
    do = beat.get("do") or {}
    add(beat.get("each"))
    if "map" in do or "reduce" in do:
        ((kind, fields),) = do.items()
        registered = STAGES.get(f"{kind}.{fields['action']}")
        for parameter, details in (registered.params.items() if registered else []):
            if details.kind is Source:
                add(given.get(PLAY_KEYS.get(parameter, parameter)))
    elif "jev" in do:
        add((given.get("options") or {}).get("from"))
        for entry in (given.get("state") or {}).values():
            add(entry.get("from") if isinstance(entry, dict) else None)
    elif "play" in do:
        add(list(given.values()))
    elif "write" in do:
        add(given.get("from"))
    return found
