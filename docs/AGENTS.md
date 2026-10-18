# AGENTS.md

Instructions for any AI agent or new contributor working in this repository.
Read this file first. It describes the layout, the rules, the documentation
that must be kept accurate, and the workflow that keeps duplicate work out of
the codebase.

Do not skip to the code. Read `docs/INVENTORY.md` before adding a file, and
`docs/DECISIONS.md` before changing a design that seems wrong. Both are kept
accurate by the process described here.


## What this project is

FemuraLabs is a research prototype for lower-limb CT analysis: it segments the
femur and tibia from CT, builds 3D meshes, places anatomical landmarks, and
computes mechanical axes and alignment angles. Nothing in this repository is
suitable for clinical use.

The current state is foundation-only: a NumPy array toolkit (normalisation,
intensity window, reference convolution), a small CNN training pipeline with
seeded reproducibility, a `.npy` summary tool, and the container
infrastructure to run the pipeline image on a CPU-only host. The clinical
pipeline is not present yet; do not invent it.

The repository is a learning and research exercise.


## Layout

    src/femuralabs/          Importable package. Only place code may be added as a module.
      toolkit/
        arrays.py            NumPy array helpers (zscore, window, conv2d).
        summary.py           Statistics of a .npy file; also a command line.
        volume_info.py       make_volume, describe (shape, spacing, extent).
        cli.py               Command-line geometry tool.
        training/
          model.py           SmallCNN.
          train_utils.py     Seeding, device, checkpoints, logging, plotting.
        service/
          routes.py          Pure request routing.
          api.py             HTTP handler.
          serve.py           Process entry point (binds 0.0.0.0:PORT).
          
    scripts/                 One-off scripts, run by hand.
      hello_pipeline.py      Prints the geometry of a synthetic volume.
      train_small_cnn.py     Training loop with seeded reproducibility.
      compare_runs.py        Compares two runs' metrics.csv.
      check_tree.py          Verifies that the files the project claims to have exist.

    tests/                   pytest files. One test file per module under src/.

    docs/                    Documentation. Do not add prose anywhere else.
      INVENTORY.md           Every tracked path, described in one or two sentences.
      DECISIONS.md           Every design choice that could have been made differently.
      RUNBOOK.md             Every command that has been run, with expected output.

    docker/, Dockerfile      Container recipe. Currently one image: toolkit-hello.

    data/                    Downloaded or generated input. Not committed.
    runs/                    Training run output. Tracked in error; see D006.
    reports/                 Figures for reports. Committed.
    notebooks/               Exploration only. Committed, not authoritative.

    AGENTS.md                This file.
    README.md                Public entry point: purpose, quick start, limits.
    conftest.py              Adds src/ to sys.path for pytest.


## The two kinds of Python files

Every Python file in this repository is exactly one of these:

**Module** — a file under `src/femuralabs/toolkit/`. Importable.

- Takes its inputs as parameters.
- Returns values. Does not print.
- Has no hidden global state.
- Is covered by at least one test under `tests/`.

**Script** — a file under `scripts/`. Run by hand.

- Reads its inputs from the command line via `argparse` or from a fixed path.
- May print. May hard-code small demonstration data.
- Is not imported by other code. If another script needs its logic, that
  logic belongs in a module under `src/`.

The boundary matters because tests can call modules directly without a
terminal, and because container commands can call scripts without a test
framework. Mixing the two — a script that another script imports, or a module
that prints when loaded — is the most common source of duplicated logic.


## The rule against duplicate functions

One function, one definition, one import. Before writing a Python function,
check whether it already exists:

    git grep -n "def <function_name>" -- '*.py'

    grep -rn -E "^(def |class )" src scripts tests --include=*.py

If the function exists and does almost the right thing, edit it in place. Do
not add a variant, a helper, a `_v2`, or a second copy in another file. If two
callers genuinely need different behaviour, extract the shared part into a
private function and have both call it.

`docs/INVENTORY.md` is the mechanical check on this. Every module appears
there exactly once with a description of what it does. If a change would add a
second implementation of an existing idea, the inventory would either need two
descriptions of the same concept (obvious duplication) or one description that
covers both files (a smell). Either way, the inventory makes the problem
visible before the code does.


## Documentation is the source of truth

Three files under `docs/` and one at the root are maintained as part of every
change, not as an afterthought.

`docs/INVENTORY.md` — one row per tracked file. Updated when a file is added,
removed, or gains a new public function. The description is a full sentence
that stands alone: no external reading required, no reference to any tutorial,
course, chapter, block, phase, or session.

`docs/DECISIONS.md` — one entry per design choice that could have been made
differently. Updated when a choice is made or reversed. Four parts: Decision,
Alternative rejected, Reason, Consequence. Every entry names the alternative,
so the reasoning is visible. "It was the obvious choice" is not a reason.

`docs/RUNBOOK.md` — one section per stage that has been run successfully on
the workstation. Updated when a new stage is verified, and only when it has
been run and the output confirmed. An unrun command is not added.

`scripts/check_tree.py` — verifies that every path the project claims to have
exists. Its `REQUIRED` list is the file list the inventory describes. A path
is added to `REQUIRED` in the same commit as the inventory row, never in a
separate commit.

`README.md` — public entry point. One paragraph of purpose, one quick-start
block, one limits block. Kept short; `docs/` holds the maintainer detail.


## Working protocol

Follow this order for every change, no exceptions.

**Before writing code:**

1. `git status` — confirm the working tree is clean or holds only the intended change.
2. `git log --oneline -5` — know what the last change was.
3. `grep -rn -E "^(def |class )" src scripts tests --include=*.py` — know what exists.
4. `python scripts/check_tree.py` — confirm the documented state matches disk.

**After writing code:**

1. Run the code and paste the actual output; do not describe what it "should" print.
2. Update `docs/INVENTORY.md` if a file was added or a public function was added.
3. Update `docs/DECISIONS.md` if a design choice was made.
4. Update `docs/RUNBOOK.md` if a new command was verified.
5. Update `scripts/check_tree.py`'s `REQUIRED` list if a file was added or removed.
6. `pytest -q` — confirm the test suite still passes.
7. `git diff --cached` — review the exact content being committed.
8. Commit with a message that describes the change, not the session.

**Commit message format:**

    <type>: <imperative summary, lower case, no full stop>

Types:

- `feat` — a new function, file, or behaviour.
- `fix` — a correction to existing behaviour.
- `docs` — a documentation change only.
- `test` — a test file change only.
- `refactor` — a change that does not alter behaviour.
- `chore` — a tooling or dependency change.

One logical change per commit. Do not combine a code change and an unrelated
docs change. Do not amend a commit that has been pushed.


## Constraints

These are hard rules. Deviating breaks reproducibility or exposes data.

**Never commit:**

- `data/`, `runs/`, any `.npy` or `.nii.gz` file.
- `.venv/`, `__pycache__/`, any `*.pyc`.
- Any file containing a token, key, password, or personal path.
- Screenshots that have not been cropped to remove the terminal username,
  hostname, home folder path, bookmarks, and notifications.

**Never remove without a decision entry:**

- A test. If a test is wrong, fix the code, or fix the test and record the
  reason in the commit message and in `DECISIONS.md`.
- A `REQUIRED` entry in `check_tree.py` that is still present on disk.
- A `docs/DECISIONS.md` entry.

**Never assume:**

- That a Docker build was tested by a `docker run` on the same machine. The
  clean-checkout test exists because the two are not equivalent.
- That a script in `scripts/` can be imported. If another script needs its
  logic, the logic must move to `src/` first.
- That a file in `notebooks/` is authoritative. Notebooks are exploration;
  the modules under `src/` are the definition.

**Never write:**

- A second implementation of a function that already exists.
- A description in any doc that refers to any external material. Every doc
  must be readable on its own.
- A commit message that describes the session rather than the change.


## When documentation needs updating

The question to ask after every change is: what in the documentation is now
wrong, incomplete, or missing? Update exactly those parts.

| Change | Update |
|---|---|
| New file added | `docs/INVENTORY.md` (one row), `scripts/check_tree.py` (`REQUIRED`) |
| File removed | Delete the row from `docs/INVENTORY.md`; remove from `REQUIRED` |
| Function renamed or added | `docs/INVENTORY.md` (update or extend the description) |
| Design choice made or reversed | `docs/DECISIONS.md` (new entry; do not edit old ones) |
| New command verified | `docs/RUNBOOK.md` (new section, with expected output) |
| Command no longer works | Update the `docs/RUNBOOK.md` section after re-verification |
| Public behaviour changed | `README.md` (only if the quick start is affected) |
| Test added | No doc change; the test suite is the source of truth for behaviour |

If you are unsure whether a change needs a `DECISIONS.md` entry, add one. A
short entry is cheap; a hidden design choice is expensive.


## Reproducibility

- Every random generator in every training script is seeded via
  `train_utils.set_seed`. Do not add a script that draws random numbers
  without calling it.
- The train/validation split uses a seeded generator. Do not switch to a
  fresh generator inside the loader without updating the reproducibility
  section of the README.
- Every training run writes to `runs/<name>/` with `config.json` and
  `metrics.csv`. Do not reuse a run name; the metrics file is appended to.
- Comparing two runs is done with `scripts/compare_runs.py`. The result is
  expected to be zero on CPU and non-zero but tiny on GPU; a non-zero on CPU
  is a bug.


## Where to look first

- To run the project: `docs/RUNBOOK.md`.
- To understand a file: `docs/INVENTORY.md`.
- To understand why a design looks unusual: `docs/DECISIONS.md`.
- To change the project safely: this file, "Working protocol".

Anything that does not appear in one of those places does not exist yet as
part of the project, and should be discussed before it is added.