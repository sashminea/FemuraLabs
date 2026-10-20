"""Render a flow diagram to docs/flow/ and prepend a section to docs/FLOW.md.

Host-only tool: it needs matplotlib, which the tool container does not install.
It is not run inside the image and its output is committed, not generated at
build time.

Run as:

    python scripts/draw_flow.py --id 4.1 --title "..." --description "..." --spec - <<'EOF'
    { "nodes": [...], "edges": [...] }
    EOF

Node kinds map to colours: module (blue), script (green), cli (yellow), file
(white, dashed border), external (grey). Every node may carry `col` and `row`
to override automatic layout.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


KIND_COLOURS = {
    "module":   "#cfe2f3",
    "script":   "#d9ead3",
    "cli":      "#fff2cc",
    "file":     "#ffffff",
    "external": "#e6e6e6",
}
MARKER = "<!-- INSERT HERE -->"


def layout(spec: dict) -> dict[str, tuple[int, int]]:
    """Assign (col, row) to each node.

    Roots (no incoming edges) at col 0. BFS to assign subsequent columns.
    Unreached nodes (cycles, disconnected) go on a column after the last.
    A node may override its position with `col` and `row` keys.
    """
    nodes, edges = spec["nodes"], spec["edges"]
    by_id = {n["id"]: n for n in nodes}
    incoming: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        incoming[e["to"]].append(e["from"])

    roots = [n["id"] for n in nodes if not incoming[n["id"]]]
    if not roots:
        roots = [nodes[0]["id"]]

    col: dict[str, int] = {}
    frontier = [(rid, 0) for rid in roots]
    while frontier:
        nid, lvl = frontier.pop(0)
        if nid in col:
            continue
        col[nid] = lvl
        for e in edges:
            if e["from"] == nid:
                frontier.append((e["to"], lvl + 1))

    last = max(col.values(), default=0) + 1
    for n in nodes:
        col.setdefault(n["id"], last)
        if "col" in n:
            col[n["id"]] = n["col"]

    per_col: dict[int, list[str]] = defaultdict(list)
    for n in nodes:
        per_col[col[n["id"]]].append(n["id"])

    coords: dict[str, tuple[int, int]] = {}
    for lvl, ids in per_col.items():
        for i, nid in enumerate(ids):
            row = by_id[nid].get("row", i)
            coords[nid] = (lvl, -row)
    return coords


def draw(spec: dict, out_png: Path) -> None:
    coords = layout(spec)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_axis_off()

    for n in spec["nodes"]:
        x, y = coords[n["id"]]
        colour = KIND_COLOURS.get(n.get("kind", "module"), "#ffffff")
        dashed = n.get("kind") == "file"
        ax.add_patch(FancyBboxPatch(
            (x - 0.42, y - 0.15), 0.84, 0.3,
            boxstyle="round,pad=0.02",
            linewidth=1.2,
            edgecolor="#333333",
            facecolor=colour,
            linestyle="--" if dashed else "-",
        ))
        ax.text(x, y, n["label"], ha="center", va="center", fontsize=9)

    for e in spec["edges"]:
        x0, y0 = coords[e["from"]]
        x1, y1 = coords[e["to"]]
        ax.add_patch(FancyArrowPatch(
            (x0 + 0.42, y0), (x1 - 0.42, y1),
            arrowstyle="->",
            mutation_scale=15,
            linewidth=1.0,
            color="#333333",
        ))
        if "label" in e:
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(
                mx, my + 0.05, e["label"],
                ha="center", va="bottom", fontsize=8, color="#555555",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
            )

    xs = [c[0] for c in coords.values()]
    ys = [c[1] for c in coords.values()]
    ax.set_xlim(min(xs) - 0.8, max(xs) + 0.8)
    ax.set_ylim(min(ys) - 0.5, max(ys) + 0.5)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def prepend(flow_md: Path, slug: str, title: str, description: str, png: Path) -> None:
    text = flow_md.read_text()
    if MARKER not in text:
        raise SystemExit(f"Marker {MARKER!r} missing from {flow_md}")
    img_tag = f'<img src="{png.as_posix()}"'
    if img_tag in text:
        raise SystemExit(f"A diagram with slug {slug!r} already exists in {flow_md}")
    section = (
        f"## {title}\n\n"
        f'{img_tag} alt="{title}">\n\n'
        f"{description}\n\n---\n\n"
    )
    flow_md.write_text(text.replace(MARKER, section + MARKER, 1))

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--slug", required=True,
                   help='short descriptive filename slug, e.g. "write-info-out-flag"')
    p.add_argument("--title", required=True,
                   help="human-readable heading for the section")
    p.add_argument("--description", required=True,
                   help="2–4 sentences stating what the diagram shows")
    p.add_argument("--spec", default="-", help='JSON spec path, or "-" for stdin')
    p.add_argument("--out-dir", type=Path, default=Path("docs/flow"))
    p.add_argument("--flow-md", type=Path, default=Path("docs/FLOW.md"))
    a = p.parse_args()

    spec = json.load(sys.stdin if a.spec == "-" else open(a.spec))
    png = a.out_dir / f"{a.slug}.png"
    draw(spec, png)
    prepend(a.flow_md, a.slug, a.title, a.description, png)
    print(f"wrote {png}")
    print(f"prepended section {a.slug!r} to {a.flow_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())