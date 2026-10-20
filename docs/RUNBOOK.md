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

## Adding a new stage

When a new command has been run successfully on the workstation and its
output verified, add a section to this file with four parts:

1. **What it does**, in one sentence.
2. **The commands**, as a code block, no prompts inside the block.
3. **The expected output**, as a code block, so the reader can diff.
4. **What a failure means**, as a list of common failure modes and their cause.

Do not add a command that has not been run and verified. An unrun command is a
guess dressed as documentation.