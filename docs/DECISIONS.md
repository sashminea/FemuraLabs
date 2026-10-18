# Design decisions

Every choice in this repository that could reasonably have been made
differently, with the alternative that was rejected and the reason. Read an
entry before changing the behaviour it describes.

Entries are numbered; new ones go at the top. Every entry has the same four
parts: **Decision**, **Alternative rejected**, **Reason**, **Consequence**.


## D006: tracked `runs/`, `reports/` and `notebooks/` files

**Decision:** These files remain tracked for now, with the cleanup recorded
here rather than acted on immediately.

**Alternative rejected:** `git rm --cached` every file under `runs/`,
`reports/` and `notebooks/` and add the folders to `.gitignore` in the same
change that introduced `.dockerignore`.

**Reason:** The untracking is a history change and would rewrite the working
state of two training runs that are used by later chapters' reproducibility
discussions. It belongs in a dedicated change, not mixed into the container
work. `notebooks/` is committed on purpose (exploration record), but the
`.ipynb` files under it are large and should be discussed before deciding.

**Consequence:** Until the cleanup happens, `git status` after a training run
will show new files under `runs/` as untracked. Do not `git add` them. The
cleanup is tracked as an open item in `AGENTS.md` under "Constraints".


## D005: keep a `.dockerignore` from the first build

**Decision:** `.dockerignore` is present from the first Dockerfile in the
repository, before it becomes strictly necessary.

**Alternative rejected:** Add it only when the build context grows large enough
to matter.

**Reason:** The virtual environment contains PyTorch (several gigabytes).
Without `.dockerignore`, every `docker build` transfers the entire `.venv/`
to the Docker daemon even when no instruction copies from it. This wastes time
on every build and hides the actual context size when a real problem appears
later.

**Consequence:** New entries are added to `.dockerignore` as new generated
folders appear (`runs/`, `reports/`, future `models/`). The file is listed in
`check_tree.py`'s `REQUIRED`, so an accidental deletion is caught.


## D004: consolidate `make_volume` into a module

**Decision:** `make_volume` lives in `src/femuralabs/toolkit/volume_info.py`
and is imported by `scripts/hello_pipeline.py`. The script does not define its
own copy.

**Alternative rejected:** Keep `make_volume` inside `hello_pipeline.py` and let
any other code that needs a zero volume redefine it.

**Reason:** Two implementations of the same function drift. The one in the
script is not importable without side effects (it printed on import in the
first version), so a second copy tends to appear in any module that needs a
zero volume. After the change there is exactly one definition, and the script
is a thin wrapper.

**Consequence:** The script requires `PYTHONPATH=src` (or the equivalent
environment variable) to import the module. Inside the container,
`ENV PYTHONPATH=/app/src` in the Dockerfile makes the same import work without
changing the script.


## D003: separate `femuralabs.toolkit.cli` from `femuralabs.toolkit.summary`

**Decision:** A new command line, `femuralabs.toolkit.cli`, will be added for
volume geometry (shape, spacing, dtype, physical extent) alongside the existing
`femuralabs.toolkit.summary`.

**Alternative rejected:** Extend `summary` with `--spacing` and `--out` flags.

**Reason:** `summary` answers a statistical question (min, max, mean) and its
output is checked character by character by an existing test. Adding geometry
flags to the same command couples two unrelated questions and forces the
existing test to change. The new command shares the underlying `describe`
function with any other code that needs geometry, so there is no duplicated
logic — only two entry points onto the same code.

**Consequence:** Two `python -m` entry points under `femuralabs.toolkit`. The
README names both, with one line of description each.


## D002: `Dockerfile` at project root, not under `docker/`

**Decision:** The Dockerfile is at the repository root and the build context
is the project root.

**Alternative rejected:** Place the Dockerfile under `docker/` and build with
`-f docker/Dockerfile`.

**Reason:** The project has one image at this stage. The `docker/` folder pays
off when two or more Dockerfiles share files (a base image plus two children).
Until that happens, the extra `-f` argument is friction on every command.
Moving the file later is a one-line `git mv` plus a one-line change in the
runbook.

**Consequence:** A rebuild after editing any file in `src/` or `scripts/`
invalidates the source-copy layer; this is correct. A rebuild after editing
`requirements-tool.txt` invalidates the install layer; this is also correct.
The order of layers is what makes the first case fast and the second case
necessary. See D001.


## D001: separate `requirements-tool.txt` for the tool container

**Decision:** The tool container installs from `requirements-tool.txt` (a
single pinned `numpy` line). The development environment installs from the
root `requirements.txt`, which pulls PyTorch from the CUDA wheel index.

**Alternative rejected:** A single requirements file for all environments.

**Reason:** `requirements.txt` installs PyTorch from the CUDA wheel index,
which is several gigabytes. The tool container executes numpy only — no
training, no GPU, no CUDA. Shipping PyTorch into the tool image multiplies the
image size by roughly two orders of magnitude and makes every `docker pull`
(and later, every registry push) impractical.

**Consequence:** Two files must be kept in sync when numpy's pinned version
changes; update both at once and note the change in a single commit. The
`Dockerfile` copies `requirements-tool.txt`, not `requirements.txt`. Changing
that line is a deliberate decision and updates this entry.