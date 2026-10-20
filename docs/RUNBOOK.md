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

    7 passed

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
`PYTHONPATH=src` was omitted. If it fails with a `FileNotFoundException`,
`data/small.npy` was not created — re-run the second line from the project
root.


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


## Verifying a build from a clean checkout

The build above copies from the working folder, not from git. A file that was
never committed builds on this workstation but fails on every other. The clean
checkout proves that committed files alone are enough.

    cd /tmp
    rm -rf scratch_check
    git clone ~/FemuraLabs scratch_check
    cd scratch_check
    docker build -t toolkit-hello-clean .
    docker run --rm toolkit-hello-clean
    cd ~/FemuraLabs

Expected: the same three lines as the previous section, from a folder that
contains nothing but tracked files.

If `COPY` fails with `file not found`, a file is uncommitted or excluded by
`.dockerignore`. If the build succeeds but `docker run` fails with
`ModuleNotFoundError`, the working build was relying on a file that is not in
git, and the local cache masked the problem — exactly the failure the clean
checkout is designed to catch.


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

## Recording a flow diagram

Each change that alters the module flow gets a diagram in `docs/FLOW.md`.
The section is prepended above the marker `<!-- INSERT HERE -->`; old
sections are never edited or removed. The command is the same every time —
only `--id`, `--title`, `--description` and the JSON spec change:

    python scripts/draw_flow.py \
      --slug write-info-out-flag \
      --title "write_info and the --out flag" \
      --description "..." \
      --spec - <<'EOF'
    {
      "nodes": [
        {"id": "cli",  "label": "cli.main(argv)",        "kind": "cli"},
        {"id": "save", "label": "save_json(path, data)", "kind": "module"},
        {"id": "info", "label": "output/info.json",      "kind": "file"}
      ],
      "edges": [
        {"from": "cli",  "to": "save", "label": "if --out"},
        {"from": "save", "to": "info", "label": "writes"}
      ]
    }
    EOF

Expected: two printed lines, `wrote docs/flow/block-4-1.png` and
`prepended section for block 4.1 to docs/FLOW.md`, then the new section at
the top of `docs/FLOW.md` and the PNG in `docs/flow/`.

Node kinds map to colours: `module` (blue), `script` (green), `cli` (yellow),
`file` (white-dashed), `external` (grey). Every node may carry `col` and `row`
to override the automatic BFS layout.

Re-running with an existing --slug exits non-zero with A diagram with slug <slug> already exists. That is a guard against double-
prepending; delete the section from `FLOW.md` (or pick a new `--id`) if a
regeneration is intentional.

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