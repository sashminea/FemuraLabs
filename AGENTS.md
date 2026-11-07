# AGENTS.md

For any AI agent or new contributor. Read this before the code.

## What this project is

FemuraLabs is a research prototype for lower-limb CT analysis:
segmentation, 3D meshes, landmarks, alignment angles. Not for clinical use.
The clinical pipeline is not built yet; the foundation (array toolkit,
training utilities, HTTP service, synthetic-volume demo, DICOM grouping,
and the reference data) is.

## Layout

    src/femuralabs/toolkit/
      arrays.py  summary.py  volume_info.py  cli.py  io.py  report.py
      decision.py
      training/  model.py    train_utils.py
      service/   routes.py   api.py    serve.py

    scripts/     run-by-hand entry points (train_small_cnn, api_demo,
                 clean_check.sh, draw_flow.py, ...)
    tests/       pytest suite
    docs/        see "Documentation" below
    web/         static page served by the `web` Compose service

    data/, output/       not committed
    runs/, reports/      committed despite the rule below; a cleanup commit
                         is pending and will remove them
    notebooks/           committed exploration; not authoritative

## Documentation

Read these before changing a design that seems wrong:

- `README.md` — purpose, quick start, limits
- `docs/runbook.md` — commands with expected output and failure modes
- `docs/decisions.md` — architectural choices, with the alternative rejected
- `docs/architecture.md` — folder map and pipeline stages
- `docs/data.md` — dataset, licence, coverage, how to combine segmentations
- `docs/FLOW.md` — cumulative annotated call graphs (newest first)
- `CITATION.cff` — citations for dataset, paper, tools
- `LICENSE` — code is Apache 2.0 (see `NOTICE` for attribution); data has its own licences

Every dataset, paper and tool is cited in `CITATION.cff`. Read each licence
from its own record page, not from a secondary source.

## The two kinds of Python files

**Module** — `src/femuralabs/toolkit/`. Importable. Takes its inputs as
parameters; returns values; does not print; no hidden global state; has a
test.

**Script** — `scripts/`. Run by hand. Reads its inputs from `argparse` or a
fixed path; may print; may hard-code demo data; is not imported by other
code. If another script needs its logic, the logic moves to `src/` first.

The boundary matters because tests can call modules directly and because
container commands can call scripts without a test framework.

## Rule against duplicate functions

One function, one definition, one import. Before writing a Python function:

    grep -rn -E "^(def |class )" src scripts tests --include=*.py

If the function exists and does almost the right thing, edit it in place. Do
not add a variant, a helper, a `_v2`, or a second copy in another file. If
two callers genuinely need different behaviour, extract the shared part into
a private function and have both call it.

## Working protocol

Before writing code:

    git status
    git log --oneline -5
    grep -rn -E "^(def |class )" src scripts tests --include=*.py

After writing code:

1. Run the code and paste the real output; do not describe what it "should"
   print.
2. Update `docs/decisions.md` if a design choice was made.
3. Update `docs/runbook.md` if a command was verified.
4. Update `docs/FLOW.md` if the module flow changed, via
   `scripts/draw_flow.py --slug <short-semantic-slug> ...`. The slug is
   semantic, never a chapter, block, session or date reference.
5. Update `docs/data.md` if a dataset fact (coverage, segment names,
   licence) changed.
6. `pytest -q` — tests must pass.
7. `git diff --cached` — review the exact content being committed.
8. Commit with a message that describes the change, not the session.

Commit messages follow `<type>: <imperative summary>` where type is one of
`feat`, `fix`, `docs`, `test`, `refactor`, `chore`. One logical change per
commit. Do not amend a pushed commit.

## Hard constraints

**Never commit:** `data/`, `output/`, `*.npy`, `*.nii.gz`, `*.pt`, `*.pth`,
`.venv/`, `__pycache__/`, `*.pyc`, any token or password, any personal path,
screenshots with the terminal username, hostname, home path, or a licence
number visible.

**Never remove without a decision entry:** a passing test; an entry in
`docs/decisions.md`; a licence notice.

**Never:** mount data with `:rw`; run containers as root; commit derived data
that carries a non-commercial licence; write a second implementation of an
existing function; write a doc that refers to external material instead of
stating the fact.

**Known cleanup pending:** `runs/`, `reports/`, `notebooks/*.ipynb` are
committed despite the rule above. Do not add more. A dedicated cleanup
commit will remove them.

## Where to look first

- To run it: `docs/runbook.md`
- To understand a design choice: `docs/decisions.md`
- To understand the layout: `docs/architecture.md`
- To understand the data: `docs/data.md`