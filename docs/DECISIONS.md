# Design decisions

Every choice in this repository that could reasonably have been made
differently, with the alternative that was rejected and the reason. Read an entry before changing the behaviour it describes.

Entries are numbered; new ones go at the top. Every entry has the same four parts: **Decision**, **Alternative rejected**, **Reason**, **Consequence**.

> **Numbering note.** D009, D018 and D019 are not present. D009 was planned
> for the toolkit reorganization and superseded by D010 (the broader scope
> made a service-only entry redundant) before it was written. D018 and D019
> were reserved for the layer-cache work; that work was not carried out, so
> no entry records an unmeasured claim.

## D025: two segmentations combined into one multi-label NIfTI on the full-limb grid

**Decision:** The femur and tibia masks used by the pipeline come from a
single multi-label NIfTI, produced in 3D Slicer by loading the
`Shanks-Feet` and `Thighs_Reconstruction` segmentations onto the full-limb
volume (`_1`), renumbering the labels so femur and tibia have distinct
values, and exporting to one `.nii.gz` on `_1`'s grid.

**Alternative rejected:** (a) Use the two `.seg` files directly in Python.
(b) Use only one segmentation (femur-only path).

**Reason:** (a) `.seg` is a Slicer-internal format; reading it from Python
either requires Slicer's Python interpreter (which is not the project
environment) or round-tripping through NIfTI, which the combined export
does anyway. Loading two separate `.seg` files in the pipeline also creates
two grids that must be reconciled downstream, and any mismatch becomes a
silent error. (b) Would remove the HKA angle from the project, which is the
central measurement the application is built around; the dataset supports
it, so cutting it would be a scope decision without a data reason.

**Consequence:** The combined `.nii.gz` becomes the canonical reference for
every later stage (mask extraction, meshing, landmark detection). The two
source `.seg` files stay in `data/raw/` as the original record but are not
read by any project code. Label numbering (femur=1, tibia=2, and so on) is
recorded in `DATA_NOTES.md` and in the export step of the runbook. If a
second subject is added later (stretch item S1), the same combined-export
step is repeated, not the split-file load.

## D024: environment record written by code, as JSON

**Decision:** `train_utils.environment_record()` returns a flat dict of
software and hardware versions, and the training script writes it as
`environment.json` next to `config.json` and `metrics.csv`. The record
is not produced by shell lines in the launch command.

**Alternative rejected:** Three shell lines appending `python --version`,
`pip freeze`, and `sha256sum data/splits.json` to an `environment.txt`.

**Reason:** Shell lines are skipped on busy days — the exact days the
record matters most. The `environment_record()` function is called once
inside `main()`, so the record is always written when a run starts, never
by human memory. JSON (not TXT) matches the format of the other files
in the run folder and lets `read_metrics`, `load_config` and any future
tool read all run folder files with the same `json.loads`.

**Consequence:** The record captures the Python and package versions
in the *training environment* (the venv), not the shell's default
Python. A wrong-venv run is caught by the `which python` check in the
runbook before this becomes an issue. GPU detection is optional and
passed by the caller — the default `"none"` means "CPU", not "unknown";
if `torch.cuda.is_available()` at the call site is true, the training
script passes the actual card name.

## D022: `verdict` handles lower-is-better metrics by argument order

**Decision:** `verdict(base, cand, threshold)` always treats the first
list as the baseline and the second as the candidate; higher is better.
A metric where lower is better, such as a surface distance in
millimetres, is handled by swapping the arguments at the call site
(`verdict(cand_hd95, base_hd95, 1.0)`), not by a `direction` parameter.

**Alternative rejected:** A `direction: "increase" | "decrease"`
parameter, with the function flipping the sign internally.

**Reason:** A `direction` parameter adds a branch to the function and
one more place where a typo can silently produce a wrong verdict.
Swapping the argument order puts the direction in the caller's hands,
where the semantics are visible: "`verdict(baseline=worse, candidate=
better)`" reads as what it is. The function stays three lines and
mathematically unidirectional.

**Consequence:** Every caller with a lower-is-better metric must remember
to swap. The runbook records this convention with one example. Guards
(a metric that should not worsen) use the same rule with a negative
threshold: `verdict(base, cand, -0.005)` asks "is the candidate at most
0.005 worse than the baseline".

## D021: two Compose services — `api` (built) and `web` (public image)

**Decision:** `docker-compose.yml` defines two services. `api` is built from
the project's Dockerfile, starts `femuralabs.toolkit.service.serve`, publishes
port 8000, and mounts `./output:/output:ro` with `REPORT_FOLDER=/output`.
`web` uses the public `python:3.12-slim` image, runs
`python -m http.server 8080 --directory /web`, publishes port 8080, mounts
`./web:/web:ro`, and depends on `api` only for start order.

**Alternative rejected:** (a) One service for both — a single image with two
processes under a supervisor. (b) A second build for `web`, even though it
only serves static files. (c) Add a `trainer` service as a placeholder.

**Reason:** (a) mixes two responsibilities in one container and forces the
whole system to share one process tree; if one crashes, both do. Container
separation is the whole point. (b) serves nothing that the public
`python:3.12-slim` image does not already provide — a standard-library static
file server — and adds a `Dockerfile` that must be maintained for no benefit.
The image is a dependency, not code we own. (c) is premature: a placeholder
service without a real container behind it would make `docker compose up`
raise errors or be silently skipped, and the next block's trainer will need a
real image and a real output folder before it can be declared here. Not being
in the file yet is honest.

The `:ro` mount on `api` follows D016: `/output` is where a written report
already exists; the API reads it, never writes it. `output/` is writable on
the host by the command-line tool, which is where reports come from.

`depends_on: [api]` is chosen over nothing because Compose otherwise has no
ordering guarantee — `web` may start before `api`, and a fresh `docker compose
up` would show `web` up while `api` is still pulling. The ordering does not
wait for `/health` to answer (`depends_on` is start order, not readiness); a
future service that needs `api` ready would add a healthcheck and the
`condition: service_healthy` form, which the current `web` does not need.

**Consequence:** `docker compose up --build -d` is the one command that starts
the whole system. `docker compose down` stops it. `docker compose ps`, `logs
SERVICE`, `config` are the diagnostic tools. `docker run toolkit-hello …`
still works for one-container runs, because `image: toolkit-hello` names the
built image. `web/` is new and lives at the project root next to `output/`;
both are bind-mounted, so editing `web/index.html` and refreshing the browser
picks up the change immediately without a rebuild.

## D020: `routes.route` extended to read a written report; no `status.py`

**Decision:** `service/routes.py` gains a `_report_body()` helper. When the
`REPORT_FOLDER` environment variable is set and `{REPORT_FOLDER}/info.json`
exists, `/info` returns that file's JSON. Otherwise it falls back to the
geometry dictionary it always returned. `api.py`, `serve.py`,
`scripts/api_demo.py` and the three existing tests in `tests/test_routes.py`
are unchanged.

**Alternative rejected:** A second module `service/status.py` implementing a
separate `/health` + `/info` service that reads `/output/info.json`, as one
alternative design would suggest.

**Reason:** A second service would duplicate every part of the existing one —
the `/health` branch, the `do_GET` order of `send_response` → `send_header` →
`end_headers` → `wfile.write`, the `HTTPServer` bootstrap, the `PORT` env var.
The only genuine difference is that one endpoint serves a file and the other
computes a dictionary. That is an extra branch inside `route`, not a second
program. Everything below `route` (the HTTP layer, the process, the port)
is identical and stays one implementation.

The `REPORT_FOLDER` env var is chosen over a `--folder` CLI flag because the
Compose file sets env vars on a service without a shell (`environment:`), and
because it matches how the container already receives `PORT` from
`serve.py`'s existing `os.environ.get`. Two env vars, one convention.

**Consequence:** The endpoint is more robust than before: it answers `/info`
whether or not a report has been written. A caller (browser, curl, a future
viewer) gets either a written report or the computed default, never a 404.
The `-v ./output:/output:ro` mount on the API service in the Compose file
gives the container read access to the folder; `environment: REPORT_FOLDER:
/output` makes it look there. If both are set but the file is missing, the
fallback runs — a valid state, not an error.

## D017: writer tests use `tmp_path`, never `output/`

**Decision:** `tests/test_report.py` uses pytest's `tmp_path` fixture for the
output folder; no test writes to `output/` or `data/`.

**Alternative rejected:** Test against the real `output/` folder after
creating it, then delete the resulting file.

**Reason:** A test that writes to a known folder collides with a real run
(the file exists when the test starts, so `mkdir` fails, or the test's file is
in the way of the run's file), leaves state behind when it fails before
cleanup, and cannot run in parallel with anything else. `tmp_path` gives
each test a unique empty folder, deletes it afterwards even when the test
fails, and does not interact with the working tree. The same reason makes the
writer take the folder as a parameter (D013): a test cannot point a hidden
default at `tmp_path`; it can only point a parameter there.

**Consequence:** Any new test that writes a file uses `tmp_path`. Tests that
need a file on disk for input use `tmp_path` and create it in the test body,
never `data/` or `output/`. The real `output/` is written only by
`docker run` (or the host CLI when someone passes `--out output`
deliberately); no `pytest` run touches it.

## D016: mounts use `/data` (read-only) and `/output` (writable)

**Decision:** Every container run that reads host data mounts it at `/data`
with `:ro`; every run that writes host results mounts at `/output` with the
default writable mode. The image's `WORKDIR` is `/app`, and no mount point
overlaps anything under it.

**Alternative rejected:** (a) A single `-v "$(pwd):/work"` mount, so
everything is visible at once. (b) `:rw` for the data mount. (c) Mount points
inside `/app`, for example `/app/data`.

**Reason:** (a) exposes the entire repository — `.git`, `runs/`, any future
secrets file — to the container and defeats `.dockerignore`'s purpose. (b)
lets a bug in the tool modify or delete a scan; the mount should make that
impossible, not merely discouraged. (c) hides whatever the image holds at
that path. A folder mounted at `/app/src` makes `femuralabs` (which lives at
`/app/src/femuralabs`) invisible, and every command fails with `No module
named 'femuralabs'`. The chosen paths `/data` and `/output` are empty in the
image, so mounting there removes nothing.

**Consequence:** The two mount flags are typed at every run that reads or
writes. The CLI's `--file` and `--out` arguments name the container path
(`/data/volume.npy`, `/output`) — not the host path — because the CLI runs
inside the container and cannot see the host. The output folder must be
created **before** the run, as the host user. Docker creates a missing
bind-mount folder as `root`; the container's `student` (UID 1000) then
cannot write to it. `mkdir -p output` makes the folder owned by UID 1000,
matching the container user.

## D015: cumulative annotated call graphs in `docs/FLOW.md`

**Decision:** `docs/FLOW.md` records one annotated call graph per recorded point in the project's development, at
the stage the change left the code. Diagrams are generated by
`scripts/draw_flow.py`, which reads a JSON spec on stdin, renders a PNG into
`docs/flow/`, and prepends a section above the `<!-- INSERT HERE -->` marker.
Sections are cumulative and append-only (newest first); old sections are never
edited. The PNG is committed; the spec is not. `--slug` is a semantic,
filename-safe identifier, never a chapter or session reference.

**Alternative rejected:** (a) A single hand-drawn diagram updated in place.
(b) Diagrams generated automatically from the AST at commit time. (c) No
diagrams; rely on `INVENTORY.md` and `RUNBOOK.md` prose only.

**Reason:** (a) is a living document that becomes wrong the moment the code
changes and looks correct even when it is stale. (b) is expensive, brittle on
partial understanding (a function whose purpose is documented only in a prose
sentence cannot be extracted from code), and would require a real
Python-parsing dependency. (c) forces a reader to reconstruct the wiring from
prose, which is slow and error-prone. A cumulative append-only series lets a
reader see the *evolution*: the current shape is the newest section, older
shapes remain visible, and a wrong diagram in the middle is caught by the
sections above and below it.

**Rule adopted:** a diagram is regenerated in the same commit as the code
change it describes. It supplements the tests, it does not replace them.

**Consequence:** The spec JSON is not committed; only the rendered PNG and
the `FLOW.md` section are. A reader reconstructing an old diagram regenerates
it from the `FLOW.md` description; the current section is regenerated by
running the command in `RUNBOOK.md`. `scripts/draw_flow.py` is a host-only
tool: it depends on matplotlib, which the tool image does not install, and it
is never run inside the container. The script's `--spec` input is a JSON
literal, not a file, so no per-block spec file is created and the repository
does not grow a `specs/` folder.

## D014: extract `save_json` to `toolkit/io.py`; `save_config` and `write_info` share it

**Decision:** The primitive — create parent folders, `json.dumps`, write, add
a trailing newline — lives once in `femuralabs.toolkit.io.save_json`.
`training/train_utils.save_config` and `toolkit/report.write_info` both call
it.

**Alternative rejected:** (a) Let `write_info` reimplement the two-line body
(`mkdir` + `write_text(json.dumps(...))`) next to `save_config`. (b) Import
`save_config` into `report.py` from `training/train_utils.py`.

**Reason:** Option (a) is a second definition of the same operation; they drift
the first time one gains an argument (an `indent`, an encoding, a
trailing-newline policy). Option (b) fails for a different reason: `train_utils`
imports `torch`, and the tool image ships numpy only (D001, D011), so
`report.write_info` would fail at import time inside the tool container.
Extracting to a module that does not pull `torch` lets both use the primitive
and keeps it in the tool image.

**Rule applied:** a subpackage appears when two or more files share one
coherent purpose and are expected to grow. `io.py` is one file, called from two
locations; it stays flat and moves into a subpackage only when a second I/O
helper arrives.

**Consequence:** `train_utils.save_config` becomes a one-line wrapper — same
signature, same behaviour, callers unchanged. `write_info` writes to
`out_dir/info.json` in one line. The two public functions have different
signatures because they have different caller contracts (full path vs folder);
they share the implementation underneath, which is the part the reuse rule
protects.

## D013: `--out` has no default; `write_info` takes the folder as a parameter

**Decision:** `report.write_info(info, out_dir)` takes the output folder as a
required parameter and has no default. The `--out` flag on the CLI has no
default either: when the flag is absent, nothing is written.

**Alternative rejected:** A default folder (`output/` or `reports/`), so
`--file` alone always writes a file.

**Reason:** A hidden default folder is one that a host run and a container run
disagree about. On the host, `output/` is next to the script; inside a
container started with `-v "$(pwd)/output:/output"`, the container's working
folder is `/app`, and `output/` there is a different folder or does not exist.
With a default, the two runs silently produce different results, and the mount
block cannot show whether the mount is doing anything. With no default, the
caller states the folder, and a wrong folder is a visible error.

**Consequence:** Every writing invocation passes `--out` explicitly, including
in the runbook. A caller that wants a default passes it by name
(`--out output`). The function's contract is "writes to the folder you name,
returns the path"; that contract is what makes `tests/test_report.py` in the
next block able to use a `tmp_path` folder and never touch `output/`.

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
by the container; create it with the host user before running. If a future entry point needs `training/`, either
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