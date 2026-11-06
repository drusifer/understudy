"""A run's first line as the console reads it: the plan of a small scene, for tests that need only its beats and moves."""


def story_plan(names, moves, final=(), initial=None, pieces=()):
    """`{"plan": ...}` for beats `names` (the first is the initial one unless `initial` says), `moves` as (from, to) or
    (from, to, guard) tuples, `final` beats, and `pieces` read by the first beat."""
    nodes = [{"id": name, "kind": "piece", "write": False, "flow": False, "final": False, "waits": False, "action": None}
             for name in pieces]
    nodes += [{"id": name, "kind": "beat", "write": False, "flow": True, "final": name in final, "waits": False, "action": None}
              for name in names]
    edges = [{"from": each[0], "to": each[1], "kind": "move", **({"when": each[2]} if len(each) > 2 else {})} for each in moves]  # noqa: PLR2004
    edges += [{"from": piece, "to": names[0], "kind": "reads"} for piece in pieces]
    return {"plan": {"nodes": nodes, "edges": edges, "props": [], "initial": initial or names[0]}}
