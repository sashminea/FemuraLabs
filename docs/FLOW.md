# Flow diagrams

A cumulative record of the module-level flow at each recorded point in the
project. Each section shows the functions involved, their parameters and
return values on the node labels, and the data that moves between them on the
arrows. This is an **annotated call graph**: a call graph where each edge
carries the data that flows across it.

Sections are **added at the top and never removed or edited**. If the code
changes shape later, the older diagram is still accurate for its point in
time; the current shape is the topmost section. This mirrors the append-only
convention of `DECISIONS.md`.

Diagrams supplement the tests, they do not replace them. The tests under
`tests/` are the source of truth for behaviour; a diagram is a summary that
makes the wiring visible at a glance, and it cannot catch an error path or an
edge case.

To add a section, run `scripts/draw_flow.py` with a JSON specification on
stdin and a descriptive `--slug`. See `docs/RUNBOOK.md` for the exact command.

Node colours: blue = module, green = script, yellow = CLI entry point,
white-dashed = file on disk, grey = external.

---

## write_info and the --out flag

<img src="docs/flow/write-info-out-flag.png" alt="write_info and the --out flag">

The geometry CLI branches on --file (load a .npy) and on --out (write info.json). The writer lives in report.py and delegates the actual write to io.save_json, which is also what training/train_utils.save_config uses. One JSON writer, two public faces; the CLI never touches the file system directly.

---

<!-- INSERT HERE -->