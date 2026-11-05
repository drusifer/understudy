"""The statechart of a run, laid out for the page to draw (ADR-0054).

`layout` turns a machine (its states and the moves between them, as the first line of a run's event stream tells it)
into boxes and arrows in pixels: states in layers from the initial state downward, wide layers wrapped into rows,
every arrow routed through the gaps between rows and the gutters beside them so it never runs through a box, and a
label for each guarded move placed inside its own lane so no two labels meet. `overlay` adds what a run says: the state
it is in and the move it just made. The page only draws what this returns; nothing here is browser code.
"""

import json
from dataclasses import dataclass

NODE_H = 44
MIN_NODE_W = 150
CHAR_W = 9  # the page's box font, about this wide per character
HGAP = 48
MIN_GAP = 56  # between two rows; the first and last gap are smaller
EDGE_GAP = 24
LANE = 22  # one horizontal run of one arrow
GUTTER = 26  # one vertical run beside the boxes
MARGIN = 24
ROW_MAX = 6  # boxes in a row before it wraps
MIN_INNER = 300  # room for the widest label
LABEL_H = 18
LABEL_CHAR = 7
LABEL_MAX = 32
SPREAD = 14  # where arrows meet one box, they leave a little apart
MOVE = 2  # states a run has entered when it has made a move

OPERATORS = {"eq": "=", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">=", "in": "in", "not_in": "not in",
             "has": "has", "ends": "ends"}


def guard_text(condition) -> str:
    """A move's guard as a person would say it, cut short to fit a label."""
    text = _say(condition, nested=False)
    return text if len(text) <= LABEL_MAX else text[:LABEL_MAX - 3] + "..."


def _value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, list | tuple):
        return ", ".join(_value(each) for each in value)
    return str(value)


def _say(condition, *, nested: bool) -> str:
    if not isinstance(condition, dict):
        return _value(condition)
    parts = []
    for key, value in condition.items():
        if key in ("and", "or") and isinstance(value, list):
            joined = f" {key} ".join(_say(each, nested=True) for each in value)
            parts.append(f"({joined})" if nested else joined)
        elif key == "not":
            parts.append(f"not {_say(value, nested=True)}")
        elif isinstance(value, dict) and len(value) == 1:
            ((operator, operand),) = value.items()
            parts.append(f"{key} {OPERATORS.get(operator, operator)} {_value(operand)}")
        else:
            parts.append(f"{key} {_value(value)}")
    return " and ".join(parts)


def layout(states: list[dict], transitions: list[dict], initial: str | None = None) -> dict:
    """The machine as boxes and arrows: `{width, height, nodes, edges}`, the same machine always the same drawing."""
    names = [each["name"] for each in states]
    final = {each["name"] for each in states if each.get("final")}
    start = initial if initial in names else (names[0] if names else None)
    moves = _unique_moves(names, transitions)
    back, order = _classify(names, moves, start)
    rows, row_of = _rows(names, moves, back, order)
    return _Drawing(names, final, start, moves, back, rows, row_of).draw()


def _unique_moves(names: list[str], transitions: list[dict]) -> list[dict]:
    known, seen, found = set(names), set(), []
    for move in transitions:
        key = (move["from"], move["to"], json.dumps(move.get("when"), sort_keys=True))
        if move["from"] in known and move["to"] in known and key not in seen:
            seen.add(key)
            found.append({"from": move["from"], "to": move["to"], "when": move.get("when")})
    return found


def _classify(names: list[str], moves: list[dict], start: str | None) -> tuple[set[int], list[str]]:
    """Which moves go back to a state still being visited (loops), and the states in an order where every other move
    goes forward. A depth-first walk from the initial state, then from any state nothing reached."""
    out: dict[str, list[tuple[int, str]]] = {name: [] for name in names}
    for index, move in enumerate(moves):
        out[move["from"]].append((index, move["to"]))
    state: dict[str, int] = {}  # 1 on the walk, 2 finished
    back: set[int] = set()
    finished: list[str] = []

    def walk(name: str) -> None:
        state[name] = 1
        for index, target in out[name]:
            if state.get(target) == 1:
                back.add(index)
            elif target not in state:
                walk(target)
        state[name] = 2
        finished.append(name)

    for name in ([start] if start else []) + names:
        if name not in state:
            walk(name)
    return back, finished[::-1]


def _rows(names: list[str], moves: list[dict], back: set[int], order: list[str]) -> tuple[list[list[str]], dict[str, int]]:
    layer = dict.fromkeys(names, 0)
    forward = [move for index, move in enumerate(moves) if index not in back]
    for name in order:
        for move in forward:
            if move["from"] == name:
                layer[move["to"]] = max(layer[move["to"]], layer[name] + 1)
    by_layer: dict[int, list[str]] = {}
    for name in names:
        by_layer.setdefault(layer[name], []).append(name)
    place: dict[str, float] = {}
    rows: list[list[str]] = []
    for depth in sorted(by_layer):
        def centre(name: str) -> float:
            above = [place[move["from"]] for move in forward if move["to"] == name and move["from"] in place]
            return sum(above) / len(above) if above else float(names.index(name))

        members = sorted(by_layer[depth], key=lambda name: (centre(name), names.index(name)))
        for start in range(0, len(members), ROW_MAX):
            chunk = members[start:start + ROW_MAX]
            rows.append(chunk)
            for at, name in enumerate(chunk):
                place[name] = at + (ROW_MAX - len(chunk)) / 2
    return rows, {name: number for number, row in enumerate(rows) for name in row}


def _route_kinds(moves: list[dict], back: set[int], row_of: dict[str, int], count: int):
    """How each arrow is routed (straight between neighbouring rows, or around by the left or right gutter) and which
    arrows put a horizontal run in which gap (gap g lies above row g; gap `count` is below the last row)."""
    gaps: list[list[int]] = [[] for _ in range(count + 1)]
    kinds: dict[int, str] = {}
    long_seen = 0
    for index, move in enumerate(moves):
        source, target = row_of[move["from"]], row_of[move["to"]]
        gaps[source + 1].append(index)
        if move["from"] == move["to"]:
            continue
        if index in back:
            kinds[index] = "right"
            gaps[target].append(index)
        elif target > source + 1:
            kinds[index] = "left" if long_seen % 2 == 0 else "right"
            long_seen += 1
            gaps[target].append(index)
    return kinds, gaps


def _ports(moves: list[dict], boxes: dict) -> tuple[dict[int, int], dict[int, int]]:
    """Where each arrow leaves its box (on the bottom) and arrives (on the top): spread a little where several meet."""
    out: dict[str, list[int]] = {}
    into: dict[str, list[int]] = {}
    for index, move in enumerate(moves):
        out.setdefault(move["from"], []).append(index)
        into.setdefault(move["to"], []).append(index)

    def spread(group: dict[str, list[int]]) -> dict[int, int]:
        found = {}
        for name, indexes in group.items():
            box = boxes[name]
            centre = box["x"] + box["w"] / 2
            limit = box["w"] / 2 - 12
            for at, index in enumerate(indexes):
                found[index] = round(centre + max(-limit, min(limit, (at - (len(indexes) - 1) / 2) * SPREAD)))
        return found

    return spread(out), spread(into)


def _tidy(points: list[tuple[int, int]]) -> list[list[int]]:
    """The arrow's points without repeats or middles of straight runs, so a straight drop is two points."""
    kept: list[list[int]] = []
    for x, y in points:
        if not kept or kept[-1] != [x, y]:
            kept.append([x, y])
    tidy = [kept[0]]
    for at in range(1, len(kept) - 1):
        a, b, c = kept[at - 1], kept[at], kept[at + 1]
        if not (a[0] == b[0] == c[0] or a[1] == b[1] == c[1]):
            tidy.append(b)
    return [*tidy, kept[-1]] if len(kept) > 1 else tidy


@dataclass
class _Drawing:
    names: list[str]
    final: set[str]
    start: str | None
    moves: list[dict]
    back: set[int]
    rows: list[list[str]]
    row_of: dict[str, int]

    def draw(self) -> dict:
        count = len(self.rows)
        self.kinds, gaps = _route_kinds(self.moves, self.back, self.row_of, count)
        self.left_lanes = sum(1 for kind in self.kinds.values() if kind == "left")
        self.right_lanes = sum(1 for kind in self.kinds.values() if kind == "right")
        heights = [max(EDGE_GAP if gap in (0, count) else MIN_GAP, LANE * (len(runs) + 1)) for gap, runs in enumerate(gaps)]
        top = [MARGIN + heights[0]]
        for number in range(1, count):
            top.append(top[-1] + NODE_H + heights[number])
        self.gap_top = [MARGIN] + [top[number - 1] + NODE_H for number in range(1, count + 1)]
        self.lane_of = {(gap, index): lane for gap, runs in enumerate(gaps) for lane, index in enumerate(runs)}
        self.inner_left = MARGIN + self.left_lanes * GUTTER
        self.boxes = self._boxes(top)
        self.leaving, self.arriving = _ports(self.moves, self.boxes)
        left_seen = right_seen = 0
        edges = []
        for index, move in enumerate(self.moves):
            kind = self.kinds.get(index)
            lane_x = None
            if kind == "left":
                left_seen += 1
                lane_x = self.inner_left - GUTTER * left_seen
            elif kind == "right":
                right_seen += 1
                lane_x = self.inner_right + GUTTER * right_seen
            edges.append(self._edge(index, move, lane_x))
        height = round(top[-1] + NODE_H + heights[-1] + MARGIN) if self.rows else 2 * MARGIN
        return {"width": round(self.inner_right + self.right_lanes * GUTTER + MARGIN), "height": height,
                "nodes": [self.boxes[name] for name in self.names], "edges": edges}

    @property
    def node_w(self) -> int:
        return max([MIN_NODE_W] + [CHAR_W * len(name) + 24 for name in self.names])

    @property
    def inner(self) -> int:
        columns = max((len(row) for row in self.rows), default=1)
        return max(columns * self.node_w + (columns - 1) * HGAP, MIN_INNER)

    @property
    def inner_right(self) -> int:
        return self.inner_left + self.inner

    def _boxes(self, top: list[int]) -> dict:
        boxes = {}
        for number, row in enumerate(self.rows):
            span = len(row) * self.node_w + (len(row) - 1) * HGAP
            left = self.inner_left + (self.inner - span) / 2
            for at, name in enumerate(row):
                boxes[name] = {"id": name, "x": round(left + at * (self.node_w + HGAP)), "y": top[number], "w": self.node_w,
                               "h": NODE_H, "initial": name == self.start, "final": name in self.final}
        return boxes

    def _lane_y(self, gap: int, index: int) -> int:
        return round(self.gap_top[gap] + LANE * (self.lane_of[gap, index] + 1))

    def _edge(self, index: int, move: dict, lane_x: int | None) -> dict:
        source, target = self.boxes[move["from"]], self.boxes[move["to"]]
        sx, tx = self.leaving[index], self.arriving[index]
        below, above = self.row_of[move["from"]] + 1, self.row_of[move["to"]]
        bottom, first = source["y"] + NODE_H, self._lane_y(below, index)
        if move["from"] == move["to"]:
            points = [(sx - SPREAD, bottom), (sx - SPREAD, first), (sx + SPREAD, first), (sx + SPREAD, bottom)]
            run = (sx - SPREAD, sx + SPREAD, first)
        elif lane_x is None:
            points = [(sx, bottom), (sx, first), (tx, first), (tx, target["y"])]
            run = (sx, tx, first)
        else:
            last = self._lane_y(above, index)
            points = [(sx, bottom), (sx, first), (lane_x, first), (lane_x, last), (tx, last), (tx, target["y"])]
            run = (sx, lane_x, first)
        edge = {"from": move["from"], "to": move["to"], "back": index in self.back, "points": _tidy(points)}
        if move["when"] is not None:
            label = guard_text(move["when"])
            width = LABEL_CHAR * len(label) + 12
            x = round(max(self.inner_left, min((run[0] + run[1]) / 2 - width / 2, self.inner_right - width)))
            edge["label"] = label
            edge["label_box"] = {"x": x, "y": run[2] - LABEL_H // 2, "w": width, "h": LABEL_H}
        return edge


def overlay(story: dict, events: list[dict], run_state: str, ended: str) -> dict:
    """The layout of a run's scene plus what the run says: the beat it is on (lit), the move it just made, and how it ended."""
    entered = [each["beat"] for each in events if each.get("event") == "beat_entered"]
    start = story.get("initial") or next((each["beat"] for each in events
                                           if each.get("event") == "beat_entered" and each.get("caused_by") == "start"), None)
    chart = layout(story["beats"], story["transitions"], start)
    current = entered[-1] if entered else None
    last = {"from": entered[-2], "to": entered[-1]} if len(entered) >= MOVE else None
    for node in chart["nodes"]:
        node["current"] = node["id"] == current
    for edge in chart["edges"]:
        edge["taken"] = bool(last) and (edge["from"], edge["to"]) == (last["from"], last["to"])
    chart["last_move"] = last
    chart["ended"] = ended if run_state in ("done", "failed", "stopped") else ""
    return chart
