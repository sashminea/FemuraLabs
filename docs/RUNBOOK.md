# Runbook

Every command in this document has been typed and run on the workstation used
to develop this repository, with the output shown. Each section states what the
commands do, what output to expect, what the step proves, and what a failure
means. Commands are grouped so that a failure localises to one stage.

Nothing here requires a GPU. The container stages use the CPU only.


## Environment setup

Run this before any other command in a new terminal. The three checks confirm
that the shell is in the project root, that the virtual environment is active,
and that no unexpected files are modified.

    cd ~/FemuraLabs
    source .venv/bin/activate
    pwd
    which python
    git status

Expected:

- `pwd` ends in `FemuraLabs`.
- `which python` contains `.venv`.
- `git status` reports either `nothing to commit` or only files intended for
  change.

If `pwd` is wrong, later commands fail for unrelated reasons — a `pytest` run
from the wrong folder often collects nothing, and a `docker build .` from the
wrong folder copies the wrong context. If `which python` does not contain
`.venv`, packages install into the system Python, not the project one, and
later "module not found" errors trace back to this step, not to the code.

On Windows the activation command is `.venv\Scripts\Activate.ps1`.


## Running the test suite

The suite tests the array helpers and the training utilities against
hand-computed results. It is fast and it is the cheapest check that the
existing behaviour is intact.

    pytest -q

Expected:

    n passed 

`n` is any variable integer which might increase or decrease based on test modules, expect all test scripts to pass 
`conftest.py` at the project root puts `src/` on the import path, so no
`PYTHONPATH` prefix is needed for pytest.

If a test fails, the output names the file and line of the failed assertion.
Do not change the test to match the code; change the code, or add an entry to
`docs/DECISIONS.md` explaining why the expected value was wrong.


## Statistics summary tool

Reads a `.npy` file and prints shape, dtype, min, max and mean. Smallest
end-to-end test of the installed package.

    mkdir -p data
    python -c 'import numpy as np; np.save("data/small.npy", np.arange(6, dtype=np.float32).reshape(2,3))'
    PYTHONPATH=src python -m femuralabs.toolkit.summary data/small.npy

Expected:

    shape: (2, 3)
    dtype: float32
    min: 0.00
    max: 5.00
    mean: 2.50

The six numbers 0–5 sum to 15, so a mean of 2.50 is checkable by hand without
trusting the tool.

If the command fails with `ModuleNotFoundError: No module named 'femuralabs'`,
`PYTHONPATH=src` was omitted. If it fails with a `FileNotFoundError`,
`data/small.npy` was not created — re-run the second line from the project
root.


## Training the small CNN

Trains `SmallCNN` on MNIST for a few epochs. First run downloads the
MNIST data into `data/` (a few MB). Each run writes one folder under
`runs/`, named by `--run-name`, containing `config.json`,
`environment.json`, `metrics.csv` and `best.pt`.

    PYTHONPATH=src python scripts/train_small_cnn.py \
        --seed 0 --epochs 5 \
        --run-name run_a_s0 \
        --commit "$(git describe --always --dirty)"

Expected: one line per epoch with training loss, validation loss and
accuracy, then a PNG in `reports/run_a_s0_curves.png`.

The `$(...)` runs `git describe` before the script starts, so
`config.json` records the exact commit. A `-dirty` suffix in the hash
is a warning: the run was started from an uncommitted tree, and the
recorded commit is not the code that actually ran.

`environment.json` is written by
`train_utils.environment_record()`. It records Python, numpy, torch
and torchvision versions, the OS, CPU count and (when a GPU is used)
the GPU name. If a future run gives different numbers, comparing the
two `environment.json` files shows whether a package update is the
cause.

Do not reuse a run name; `runs/<name>/` is overwritten. For three
seeds of one variant, use `run_a_s0`, `run_a_s1`, `run_a_s2`.

On Windows PowerShell, replace `PYTHONPATH=src python` with a separate
line `$env:PYTHONPATH = "src"` before the `python` call, and replace
`"$(git describe ...)"` with `(git describe --always --dirty)`.

## Building the tool container

Builds the `toolkit-hello` image. The image installs numpy only and runs
`scripts/hello_pipeline.py` on start, so it is the deliverable that executes
the project without depending on the host Python.

    docker build -t toolkit-hello .

`-t` names the image (tag defaults to `latest`). The final `.` is the build
context — the folder the build is allowed to copy from. It is the project
root, not `scripts/`.

Expected: the build ends with a line naming the image, for example
`=> naming to docker.io/library/toolkit-hello:latest`. The first build pulls
the base image and installs numpy, so it takes a minute or two. Rebuilds reuse
the cached dependency layer and finish in a few seconds.

If Docker reports `Cannot connect to the Docker daemon`, Docker Desktop is not
running. If `COPY` fails with `file not found`, the missing file is either
untracked or excluded by `.dockerignore`; check `git status` first and the
ignore file second.

Verify the ignore file is doing its job by looking at the `transferring context`
line in the build output — a few tens of kB, not megabytes. If it grows,
compare `du -sh .venv runs data` against `.dockerignore` and find the
unmatched entry.


## Running the tool container

    docker run --rm toolkit-hello

Expected:

    shape (z, y, x): (4, 6, 6)
    spacing (mm): (2.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (8.0, 6.0, 6.0)

Any words after the image name replace the container's default command
completely. Three examples:

    # different shape and spacing
    docker run --rm toolkit-hello python -m femuralabs.toolkit.cli --shape 3 5 5 --spacing 1.5 1.5 1.5

    # which account does the container use?
    docker run --rm toolkit-hello id
    # expected: uid=1000(student) gid=1000(student) groups=1000(student)

    # start the service on host port 8000
    docker run --rm -p 8000:8000 toolkit-hello python -m femuralabs.toolkit.service.serve
    # in a second terminal:  curl http://localhost:8000/health

`--rm` deletes the container when it stops; without it, stopped containers
accumulate and `docker ps -a` lists them. `-p 8000:8000` forwards host port
8000 to container port 8000 (host:container order). If it errors with
`port is already allocated`, another program holds 8000 on the workstation —
publish to `-p 8001:8000` and `curl :8001` instead.

## Mounting data in and results out

The container reads a host folder marked read-only and writes results to a
second host folder. The image holds neither folder; both live on the host.

Create the input volume by calling the shared `make_volume` — the same
function used by `hello_pipeline.py` and the CLI's `--shape` path:

    PYTHONPATH=src python -c 'import numpy as np; from femuralabs.toolkit.volume_info import make_volume; v, _ = make_volume((2,3,4), (3.0,1.0,1.0)); np.save("data/volume.npy", v)'

Create the output folder as the host user before the container starts.
Docker creates a missing bind-mount folder as `root`; a pre-created folder
belongs to the host user (UID 1000 by default in WSL2), matching the
container's `student` account:

    mkdir -p output
    ls -la output                # owner should be your host user

Run with two mounts — data read-only, output writable:

    docker run --rm \
      -v "$(pwd)/data:/data:ro" \
      -v "$(pwd)/output:/output" \
      toolkit-hello \
      python -m femuralabs.toolkit.cli \
        --file /data/volume.npy \
        --spacing 3 1 1 \
        --out /output

Expected:

    shape (z, y, x): (2, 3, 4)
    spacing (mm): (3.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (6.0, 3.0, 4.0)
    wrote: /output/info.json

The `wrote:` line names the **container** path. The host file is:

    cat output/info.json
    ls -la output/               # owner should be your host user, not root

Read-only is enforced — attempting to write into `/data` fails:

    docker run --rm -v "$(pwd)/data:/data:ro" toolkit-hello \
      python -c "open('/data/test.txt', 'w').write('x')"
    # OSError: [Errno 30] Read-only file system

A mount hides what the image holds at the mount path:

    docker run --rm -v "$(pwd)/data:/app/src:ro" toolkit-hello \
      python -m femuralabs.toolkit.cli
    # No module named 'femuralabs'

Failure modes:

- `No such file or directory: /data/volume.npy` — the host path in the flag
  was wrong; Docker silently created an empty folder there.
- `Permission denied` on `/output` — the host folder is owned by root, not
  UID 1000. `rm -rf output && mkdir -p output` before the run.
- `Read-only file system` on `/output` — `--out` points into `/data`. Use
  `/output` (container path) for `--out`.
- `No module named 'femuralabs'` — a mount overlaps `/app/src` or `/app`,
  hiding the code. Use `/data` and `/output`.

`output/` and `data/` are ignored by git.

## Running both services with Compose

Starts the API and the static web page together, on one private network, with
one command. Both are published on the host, so a browser and `curl` reach
them by port.

Before the first start:

    mkdir -p web output
    docker compose config

`config` validates the file and prints it with every default filled in. If
the output is a YAML parse error naming a line and column, there is a tab or
a wrong indent — YAML forbids tabs.

Start, inspect, request, stop:

    docker compose up --build -d
    docker compose ps
    curl http://localhost:8000/health
    curl http://localhost:8000/info
    curl -I http://localhost:8080/
    docker compose logs api
    docker compose down

Expected:

- `up` creates the network `femuralabs_default` and starts `api` and `web`.
- `ps` lists both, each with `0.0.0.0:8000->8000/tcp` and
  `0.0.0.0:8080->8080/tcp`.
- `curl` on port 8000 `/health` gives `{"status": "ok"}`.
- `curl` on port 8000 `/info` gives the content of `output/info.json` if it
  exists, or the four-key geometry dictionary if not.
- `curl -I` on port 8080 gives `HTTP/1.0 200 OK` and a `Content-type:
  text/html` header.
- `logs api` shows `serving on 0.0.0.0:8000`. Per-request lines are silenced
  by the handler.
- `down` removes both containers and the network. `output/` and `web/`
  survive — they are bind mounts on the host.

The `--build` flag rebuilds the `toolkit-hello` image before starting; without
it, Compose uses the last built image of that name. `-d` runs in the
background; without it both services' logs stream into the terminal and
`Ctrl+C` stops them.

Recreate the report if `/info` returns the fallback shape `(4, 6, 6)` rather
than `(2, 3, 4)` — meaning `output/info.json` is missing:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output

`_report_body()` reads the file on every request, so a fresh `curl` picks up
the new content without restarting the container.

Test the Compose network — services reach each other by name:

    docker compose up -d
    docker compose exec web python -c "import urllib.request; print(urllib.request.urlopen('http://api:8000/health').read())"
    docker compose down

Expected: `b'{"status": "ok"}'` — `web` reached `api` by service name, not by
IP. The service name only resolves on the Compose network; from the
workstation, use the published ports.

Common failures:

- `no configuration file provided: not found` — the terminal is not in the
  folder holding `docker-compose.yml`.
- `port is already allocated` — another program or a leftover project holds
  8000 or 8080. `docker compose ps` shows leftovers; `docker compose down`
  removes them. If a different program holds the port, change the host side
  in `ports:` (for example `"8001:8000"`).
- `Error response from daemon: pull access denied` — the `web` image pull
  failed (network issue); `docker pull python:3.12-slim` first.
- `/info` returns the fallback `(4, 6, 6)` shape — `output/info.json` is
  missing; see above.


## Running the geometry service

Starts a small HTTP service that answers two JSON routes. No Docker needed.

    PYTHONPATH=src python -m femuralabs.toolkit.service.serve
    # prints: serving on 0.0.0.0:8000

In a second terminal:

    curl http://localhost:8000/health
    curl http://localhost:8000/info
    curl -i http://localhost:8000/missing

Expected:

    {"status": "ok"}
    {"shape": [4, 6, 6], "spacing": [2.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [8.0, 6.0, 6.0]}
    HTTP/1.0 404 Not Found
    {"error": "not found"}

Stop the server with `Ctrl+C`. The bind address must be `0.0.0.0`: if it is
`127.0.0.1`, `curl` on the workstation hangs or is refused, because the
server is listening only on its own loopback, not the network interface the
host reaches.

Without `curl`, the demo script does the same three requests against a random
free port:

    PYTHONPATH=src python scripts/api_demo.py

The `/info` route can serve a written report instead of the computed default.
Set `REPORT_FOLDER` and put an `info.json` in that folder:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output
    REPORT_FOLDER=output PYTHONPATH=src python -m femuralabs.toolkit.service.serve
    # in a second terminal:
    curl http://localhost:8000/info
    # {"shape": [2, 3, 4], "spacing": [3.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [6.0, 3.0, 4.0]}

Without `REPORT_FOLDER`, or when the folder does not hold `info.json`,
`/info` falls back to the four-key geometry dictionary. Both cases exit 200
and both are covered by `tests/test_routes.py`.


## Recording a flow diagram

Each change that alters the module flow gets a diagram in `docs/FLOW.md`.
The section is prepended above the marker `<!-- INSERT HERE -->`; old
sections are never edited or removed. The command is the same every time —
only `--slug`, `--title`, `--description` and the JSON spec change:

    python scripts/draw_flow.py \
      --slug <short-semantic-slug> \
      --title "<human-readable heading>" \
      --description "<2-4 sentences>" \
      --spec - <<'EOF'
    {
      "nodes": [ ... ],
      "edges": [ ... ]
    }
    EOF

Expected: two printed lines, `wrote docs/flow/<slug>.png` and
`prepended section '<slug>' to docs/FLOW.md`. Open `docs/FLOW.md` and
confirm the new section is at the top, above any older section, with
the `<img src="flow/<slug>.png" ...>` attribute **relative to `docs/`**
(the file lives at `docs/FLOW.md`, so `flow/...` resolves to
`docs/flow/...`; writing `docs/flow/...` would look for
`docs/docs/flow/...` and render a broken link on GitHub).

`--slug` values are semantic (`write-info-out-flag`,
`mounts-readonly-data-writable-output`), never a chapter, block, session
or date reference. Node kinds map to colours: `module` (blue),
`script` (green), `cli` (yellow), `file` (white-dashed), `external` (grey).
Every node may carry `col` and `row` to override the automatic BFS layout.

Re-running with an existing `--slug` exits non-zero with
`A diagram with slug <slug> already exists`. That is a guard against
double-prepending; if a regeneration is intentional, delete the section
from `FLOW.md`, delete the PNG, and re-run.

The script is host-only and never runs inside the container.

## Adding a new stage

When a new command has been run successfully on the workstation and its
output verified, add a section to this file with four parts:

1. **What it does**, in one sentence.
2. **The commands**, as a code block, no prompts inside the block.
3. **The expected output**, as a code block, so the reader can diff.
4. **What a failure means**, as a list of common failure modes and their cause.

Do not add a command that has not been run and verified. An unrun command is a
guess dressed as documentation.

## Verifying a clean checkout

Proves that the files tracked by git are enough to reproduce the project.
Clones into a temporary folder, runs the test suite, runs the CLI, builds the
image, runs it, and checks the output. Cleans up the clone on exit.

From project root, with the virtual environment active:

    bash scripts/clean_check.sh

Expected: `pytest -q` passes (count varies), the four geometry lines are
printed twice (once from the host Python, once from inside the container), and
the script ends with:

    clean checkout: all checks passed

Run this before trusting any commit: a file that exists in your working tree
but was never committed is invisible here. That is the point. The four failure
modes and their meaning are documented in `docs/INVENTORY.md` under
`scripts/clean_check.sh`.

## Writing a geometry result to a folder

The `--out` flag writes `info.json` inside the named folder. Uses the
synthetic-volume path from the CLI section, so no input file is needed:

    PYTHONPATH=src python -m femuralabs.toolkit.cli --shape 2 3 4 --spacing 3 1 1 --out output
    cat output/info.json

Expected:

    shape (z, y, x): (2, 3, 4)
    spacing (mm): (3.0, 1.0, 1.0)
    dtype: float32
    extent (mm): (6.0, 3.0, 4.0)
    wrote: output/info.json
    {"shape": [2, 3, 4], "spacing": [3.0, 1.0, 1.0], "dtype": "float32", "extent_mm": [6.0, 3.0, 4.0]}

The extent 6.0, 3.0, 4.0 is 2×3, 3×1, 4×1 — voxel count times voxel spacing,
checkable by hand.

Omitting `--out` prints the four lines and writes nothing. The folder is
created if missing and left unchanged if present.

`output/` and `data/` are both ignored by git; nothing under them is
committed.