# Data notes

**Source.** Zenodo record 8302449 (segmentation and surface models), derived
from the CT collection record linked from the same study. Subject 006.zip,
internal name SMIR.Lower_limb.051Y.F.CT.168. Licence CC BY-NC-SA 4.0
International. Data are never committed; `data/` is in `.gitignore`.

**Coverage.** Full lower-limb hip-to-ankle, but the reference segmentation
is split across two files:

- `...-Shanks-Feet_Segmentation.seg` — Tibia_R/L, Fibula_R/L, Talus_R/L,
  Calcaneus_R/L, Tarsals_R/L, Metatarsals_R/L, Phalanges_R/L. No femur.
- `...-Thighs_Reconstruction` — Sacrum, Hip_R/L, Femur_R/L, Patella_R/L.
  No tibia.

Combining the two is required for full-limb HKA; see D025.

**Volumes.** Two files under `data/raw/SMIR.Lower_limb.051Y.F.CT.168/`:

- `_1`: 512 x 512 x 1637, spacing (0.9766, 0.9766, 0.6998) mm,
  origin (249.5, 392.5, 119.7) mm. Full lower limb. **Use this as the
  working volume.**
- `_2`: 312 x 205 x 889, same spacing, origin (142.1, 226.5, 643.1) mm.
  Pelvis-thighs crop. Do not use directly.

**Direction matrix.** Slicer shows ITK-to-RAS as diag(-1, -1, 1). SimpleITK
reads the same file in LPS, so x and y are negated relative to Slicer's
displayed coordinates. This must be handled correctly in D01, or left and
right will be swapped.

**Decision.** Full path (not femur-only). Femur and tibia masks for the
pipeline come from a single combined multi-label NIfTI produced in Slicer
on `_1`'s grid. See D025.