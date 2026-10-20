# Design decisions

Every choice in this repository that could reasonably have been made
differently, with the alternative that was rejected and the reason. Read an
entry before changing the behaviour it describes.

Entries are numbered; new ones go at the top. Every entry has the same four
parts: **Decision**, **Alternative rejected**, **Reason**, **Consequence**.

## D012: clean-checkout check as a script, not a manual sequence

**Decision:** The proof that committed files reproduce the project is a
single script, `scripts/clean_check.sh`, committed and run before any release
or handover. The four checks it runs — pytest, CLI, docker build, docker run
— are always run together, never individually as part of this proof.

**Alternative rejected:** A manual sequence documented in the runbook and
typed from memory each time.

**Reason:** Manual sequences drift. A step is skipped "because I know it
works", or one command is mistyped, or the working tree is used instead of a
clone. The script removes both failure modes: it always clones (so the working
tree is invisible), and it always runs the same four checks in the same order.
The order matters — pytest is fastest and catches module-level errors before
the Docker build wastes minutes on an image that cannot import.

**Consequence:** When a new stage is added (a new image, a second service, a
Compose stack), add it to the script in the correct position and re-run.
Publishing a build that has not passed `clean_check.sh` is a decision to
investigate a report from someone else. This entry is the answer to
"should I run it?" — yes, every time.

## D011: image runs as non-root `student`; training code excluded from the image

**Decision:** The `Dockerfile` creates the account `student` with UID 1000
(`RUN useradd --create-home student`) before `COPY src/`, then switches with
`USER student`. The `src/femuralabs/toolkit/training/` subpackage is excluded
from the build context by `.dockerignore`.

**Alternative rejected:** Run as `root` (the default for `python:3.12-slim`)
and ship all of `src/` including `training/`.

**Reason:** A container running as `root` on the host kernel — which is what
containers share — has root inside that namespace. A single kernel exploit
or a mount-configured write path turns "the container is compromised" into
"the host is compromised". Running as a non-root account removes that
escalation path; nothing this project does needs root. The `training/`
subpackage imports `torch`, which the tool image does not install (see D001),
so shipping it would add dead code that cannot even be imported. Excluding
it from the build context also keeps the transfer small.

**Consequence:** Any file the container writes must be writable by UID 1000.
A bind-mounted output folder created by root on the host will be unwritable
by the container; create it with the host user before running (Block 4.2
shows the exact sequence). If a future entry point needs `training/`, either
add `torch` to `requirements-tool.txt` (an image-size decision, see D001) or
copy `training/` explicitly.

## D010: organize `toolkit` into `training/` and `service/` subpackages

**Decision:** `model.py` and `train_utils.py` live under
`femuralabs.toolkit.training`; `routes.py`, `api.py` and `serve.py` live under
`femuralabs.toolkit.service`. `arrays.py`, `summary.py`, `volume_info.py` and
`cli.py` stay flat at `femuralabs.toolkit.*`. The rule for a future
subpackage is stated below.

**Alternative rejected:** Group everything into subpackages by domain
(`image/`, `geometry/`, `io/`, …) in the same change.

**Reason:** A folder with one file in it adds a path segment to every import
and to every `python -m` command, without grouping anything. The two groups
created here have two or more files each, share one coherent purpose, and are
expected to grow (`training/` will gain datasets and losses; `service/` will
gain routes, middleware, healthchecks). The singletons are one file each and
grow into a folder when their second file arrives, not before.

**Rule adopted:** a subpackage appears when two or more files share one
coherent purpose and are expected to grow. Singletons stay flat.

**Consequence:** `python -m femuralabs.toolkit.service.serve` replaces the
previous `python -m femuralabs.toolkit.serve` in the runbook and any external
notes. The `Dockerfile` is unaffected: it copies `src/` wholesale and starts
`scripts/hello_pipeline.py`, neither of which references the moved modules.
No refactor is done again on this folder until a singleton gains a second
file, or a subpackage gains a fourth that is clearly distinct.

## D008: module named `serve.py`, not `server.py`

**Decision:** The HTTP entry point is `src/femuralabs/toolkit/serve.py`, and
the container starts it with `python -m femuralabs.toolkit.serve`.

**Alternative rejected:** `server.py`, matching the verb-vs-noun preference for
nouns.

**Reason:** Naming is arbitrary, but consistency is not: the file on disk, the
`python -m` argument, the `RUNBOOK.md` command and the `Dockerfile`'s `CMD`
must all say the same word. `serve.py` is chosen because it describes the
action the module performs when executed (`serve` on a port); `server.py`
describes what the module is (a noun), which reads more naturally for a
long-running process but is longer by one character and less specific.

**Consequence:** Every reference uses `serve`. If the module is renamed, all
four places (`git mv`, runbook, Dockerfile, tests) must change in one commit.


## D007: `Content-Type: application/json` on the service

**Decision:** The HTTP handler sets `Content-Type: application/json` on every
reply, including the 404.

**Alternative rejected:** `Content-Type: text/plain` (as shown in some
references), or omitting the header entirely.

**Reason:** The body is JSON. `application/json` tells clients to parse it as
JSON; `text/plain` tells them to treat it as raw text; omitting the header
leaves the client to guess. `curl` happens to guess right either way, but a
browser and most HTTP clients do not — some refuse JSON parsing on
`text/plain`. The header is one line and the cost of being right is zero.

**Consequence:** A client that expects `text/plain` (none exists today) would
need to change. Any future service endpoint that returns non-JSON must set a
different `Content-Type` explicitly.

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