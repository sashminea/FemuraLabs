# Design decisions

Architectural choices that a reader might reasonably want to reverse.
Each entry: **Decision**, **Alternative rejected**, **Reason**,
**Consequence**. Entries are numbered from the original sequence; gaps are
entries pruned during a 27 October 2026 documentation cleanup. Only the
decisions still load-bearing for the current code are recorded.

New entries go at the top.

---

## D025: combine the two reference segmentations into one multi-label NIfTI

**Decision:** Femur and tibia masks come from one multi-label NIfTI produced
in Slicer, on the `_1` grid, with labels femur=1, tibia=2, fibula=3. The two
source `.seg` files stay in `data/raw/` as the original record but are not
read by pipeline code.

**Alternative rejected:** Read the two `.seg` files directly in Python.

**Reason:** `.seg` is Slicer-internal; reading it from Python requires either
Slicer's interpreter or a NIfTI round-trip that the combined export does
anyway. Two grids downstream invite a silent mismatch.

**Consequence:** Any second subject uses the same combined-export step.
Licences and citations are in `CITATION.cff`; coverage is in `docs/data.md`.


## D022: `verdict` handles lower-is-better metrics by argument order

**Decision:** `verdict(base, cand, threshold)` treats the first list as
baseline, the second as candidate; higher is better. Lower-is-better metrics
are handled by swapping the arguments at the call site
(`verdict(cand_hd95, base_hd95, 1.0)`), not by a `direction` parameter.

**Alternative rejected:** A `direction: "increase" | "decrease"` parameter,
with internal sign flipping.

**Reason:** A direction parameter adds a branch and a place where a typo
silently produces a wrong verdict. Argument order puts the direction in the
caller's hands, where the semantics are visible.

**Consequence:** Callers with lower-is-better metrics must remember to swap.
The runbook records the convention. A guard uses a negative threshold:
`verdict(base, cand, -0.005)` asks "at most 0.005 worse".


## D016: mounts use `/data` (read-only) and `/output` (writable)

**Decision:** Containers that read host data mount it at `/data` with `:ro`;
containers that write results mount at `/output` with the default writable
mode. The image's `WORKDIR` is `/app`, and no mount overlaps anything under
it.

**Alternative rejected:** (a) A single `-v "$(pwd):/work"` mount, exposing
the whole repository. (b) `:rw` for the data mount. (c) Mounts inside `/app`.

**Reason:** (a) exposes `.git`, `runs/` and any future secrets file to the
container, defeating `.dockerignore`. (b) lets a bug modify or delete a scan.
(c) hides whatever the image holds at that path: mounting at `/app/src`
makes `femuralabs` invisible and every command fails with
`No module named 'femuralabs'`. The chosen paths are empty in the image, so
mounting there removes nothing.

**Consequence:** The CLI's `--file` and `--out` arguments name container paths
(`/data/volume.npy`, `/output`), not host paths. The output folder must be
created before the run as the host user; Docker creates missing bind-mount
folders as root, and the container's `student` (UID 1000) cannot write to
them.


## D014: extract `save_json` to `toolkit/io.py`; `save_config` and `write_info` share it

**Decision:** The primitive — create parent folders, `json.dumps`, write,
append a trailing newline — lives once in `femuralabs.toolkit.io.save_json`.
`training/train_utils.save_config` and `toolkit/report.write_info` both call
it.

**Alternative rejected:** (a) Reimplement the two-line body in `write_info`.
(b) Import `save_config` from `train_utils`.

**Reason:** (a) is a second definition of the same operation, which drifts.
(b) fails inside the tool container: `train_utils` imports `torch`, and the
tool image ships numpy only (D001, D011). Extracting to a module that does
not pull `torch` lets both callers share the primitive and keeps it in the
image.

**Consequence:** `save_config` becomes a one-line wrapper. `write_info` writes
`out_dir/info.json` in one line. Two public functions, one implementation.


## D011: image runs as non-root `student`; `training/` excluded

**Decision:** The `Dockerfile` creates the account `student` (UID 1000) before
`COPY src/`, then switches to it with `USER student`. The `training/`
subpackage is excluded from the build context by `.dockerignore`.

**Alternative rejected:** Run as root (the base image default) and ship all
of `src/`.

**Reason:** A container runs as root on the host kernel; one kernel exploit
turns "container compromised" into "host compromised". Nothing this project
does needs root. `training/` imports `torch`, which the tool image does not
install (D001), so shipping it adds dead code that cannot even be imported.

**Consequence:** Any file the container writes must be writable by UID 1000.
A bind-mounted output folder created by root on the host is unwritable by the
container; create it with the host user before running.


## D010: `training/` and `service/` subpackages; singletons stay flat

**Decision:** `model.py` and `train_utils.py` live under
`femuralabs.toolkit.training`; `routes.py`, `api.py` and `serve.py` live
under `femuralabs.toolkit.service`. `arrays.py`, `summary.py`,
`volume_info.py`, `cli.py`, `io.py`, `report.py` and `decision.py` stay flat.

**Alternative rejected:** Group everything by domain (`image/`, `geometry/`,
`io/`) in one refactor.

**Reason:** A folder with one file adds a path segment to every import and
every `python -m` command without grouping anything. The two groups created
here have two or more files each, share one purpose, and are expected to
grow. Singletons grow into a folder when their second file arrives.

**Rule adopted:** a subpackage appears when two or more files share one
purpose and are expected to grow. Singletons stay flat.

**Consequence:** `python -m femuralabs.toolkit.service.serve` replaces the
old import path. The `Dockerfile` copies `src/` wholesale, unaffected.


## D001: `requirements-tool.txt` separate from `requirements.txt`

**Decision:** The tool container installs from `requirements-tool.txt` (one
pinned numpy line). The development environment installs from root
`requirements.txt`, which pulls PyTorch from the CUDA wheel index.

**Alternative rejected:** One requirements file for all environments.

**Reason:** `requirements.txt` installs PyTorch from the CUDA wheel index,
which is several gigabytes. The tool container executes numpy only — no
training, no GPU, no CUDA. Shipping PyTorch into the tool image multiplies
its size by roughly two orders of magnitude and makes every `docker pull`
impractical.

**Consequence:** Two files must stay in sync when numpy's pinned version
changes. The `Dockerfile` copies `requirements-tool.txt`, not
`requirements.txt`.