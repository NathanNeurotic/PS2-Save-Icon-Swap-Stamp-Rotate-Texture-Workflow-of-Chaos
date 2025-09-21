# PS2 Save Icon Swap/Stamp/Rotate Texture Workflow of Chaos — **Clear, End-to-End Guide**

> **Goal:** start with base PS2 icon models (`.icn`) and textures, stamp/skin them, optionally create transform variants (FlipY/rotations), optionally round-trip in Blender/MilkShape — no guesswork.

---

## 0) Requirements (one-time)

- **Windows 10+**
- **Python 3.9+** on PATH  
  Install Pillow:
  ```bat
  pip install pillow
  ```

---

## 1) Repository layout (required + created)

```
<repo-root>\
│  README.md
│  box.txt                         # stamp area; 4 integers: x0 y0 x1 y1
│  doubleclick-stamper.bat         # easiest way to stamp or texture-swap
│  Make_ICN_Candidates_All_Transforms.bat
│  Rename_FlipY_ICN_All_Subfolders.bat
│  ps2icon_to_obj.exe
│  obj_to_ps2icon.exe
│  stamp_like_example.py
│  icn_texture_replace.py          # texture injector (keeps geometry/UVs)
│  transforms.cfg                  # which variants the “Make_*” script builds
│
│  copy.bmp  del.bmp  delete.bmp  list.bmp   # base textures (replace with yours)
│  copy.icn  del.icn  list.icn               # example ICNs (yours may live in subfolders)
│
├─ICONS\                            # (recommended) your project ICNs live here (any subfolder layout)
│   ├─APP_Example\
│   │    copy.icn  del.icn  list.icn
│   └─... (more)
│
├─out_stamped\                      # (created) stamped textures land here
└─CANDIDATES\                       # (created) transform variants (or next to sources, depending on bat)
```

---

## 2) One-screen quick start (most users only need this)

> Run from the repo root. If your paths contain spaces, keep the quotes.

```bat
REM 1) Stamp (or texture-only with a single space)
doubleclick-stamper.bat "DVR"
REM or
doubleclick-stamper.bat " "

REM 2) Inject stamped textures into all ICNs (current + subfolders)
python icn_texture_replace.py

REM 3) Generate transform candidates per transforms.cfg
Make_ICN_Candidates_All_Transforms.bat

REM 4) Auto-select FlipY variant in bulk (if needed)
Rename_FlipY_ICN_All_Subfolders.bat
```

You now have final `.icn` files ready for your PS2 save folder.

---

## 3) Visual flow (Mermaid)

```mermaid
flowchart LR
    A[Base BMP/PNG<br/>copy/del/delete/list] --> B[Stamp textures<br/>(doubleclick-stamper.bat)]
    B --> C[out_stamped/*.bmp]
    C --> D[Inject textures into ICNs<br/>(icn_texture_replace.py)]
    D --> E[Generate variants<br/>(Make_ICN_Candidates_All_Transforms.bat)]
    E -->|need FlipY| F[Bulk pick FlipY<br/>(Rename_FlipY_ICN_All_Subfolders.bat)]
    E -->|no FlipY needed| G[Select best variant]
    F --> H[Finalize ICNs]
    G --> H[Finalize ICNs]
    H -. optional .-> K[Round-trip ICN<->OBJ<br/>(ps2icon_to_obj / obj_to_ps2icon)]
    K --> D
```

---

## 4) Batch files — what they do (no surprises)

- **`doubleclick-stamper.bat`**  
  Runs the stamper over the base textures.
  - **Label:** pass the text you want (e.g., `"DVR"`).  
  - **Texture-only:** pass a **single space** (`" "`).
  - **Input:** `copy.bmp`, `del.bmp`, `delete.bmp`, `list.bmp`.  
  - **Output:** `out_stamped\*.bmp`.

- **`Make_ICN_Candidates_All_Transforms.bat`**  
  Generates **rotated/flipped/scaled** variants for every `.icn` found.  
  Reads `transforms.cfg`. Produces files with clear suffixes (e.g., `_FlipY`, `_rot90`) either under `CANDIDATES\` or alongside sources (depends on your batch’s implementation).

- **`Rename_FlipY_ICN_All_Subfolders.bat`**  
  Convenience rename to **select the `_FlipY` variant** across all subfolders so the canonical filename points at FlipY.  
  No UV math — purely filename selection.

---

## 5) Stamping details (the “box”)

- **`box.txt`**: four integers:
  ```
  x0 y0 x1 y1
  ```
  Example:
  ```
  0 0 128 128
  ```

- **Fixed box run:**
  ```bat
  python stamp_like_example.py --box-file box.txt --text DVR --images copy.bmp del.bmp list.bmp
  ```

- **Auto-infer box from a “blank” and “texted” example, then save it:**
  ```bat
  python stamp_like_example.py --infer BLANK.png EXAMPLE.png --infer-pad 4 --save-box box.txt
  ```

- Handy flags: `--fit-min`, `--fit-max`, `--h-align`, `--v-align`, `--stroke`, `--stroke-width`,  
  `--box-shift-x`, `--box-shift-y`, `--box-inset`, `--output-dir` (defaults to `out_stamped`).

---

## 6) Texture injection (non-destructive)

```bat
python icn_texture_replace.py
```

- Finds stamped bitmaps (`out_stamped\...`) and updates matching ICNs in **current folder + subfolders**.  
  Match rule: name stem (`copy_*.bmp → copy.icn`, etc.).  
- Geometry + UVs are preserved.

**Naming guideline** (so replacement “just works”):
- `copy*.bmp` ↔ `copy.icn`
- `del*.bmp`  ↔ `del.icn`
- `list*.bmp` ↔ `list.icn`

Add more icons by following the same pattern.

---

## 7) Round-trip for manual UV/mesh edits (optional)

1) ICN → OBJ/MTL:
```bat
ps2icon_to_obj.exe ".\ICONS\YourApp\list.icn"
```
2) Edit in Blender/MilkShape.  
3) OBJ → ICN:
```bat
obj_to_ps2icon.exe ".\ICONS\YourApp\list.obj"
```

Then re-run **texture injection** if you changed textures later.

---

## 8) Example config template

**`transforms.cfg` (example)**
```
# rotations are degrees; set what you actually use
rotate=0,90,180,270
flipX=no
flipY=yes
scale=1.0
```

---

## 9) Troubleshooting

- **Texture upside-down** → Generate candidates, then run `Rename_FlipY_ICN_All_Subfolders.bat` to automatically select the FlipY file.  
- **No visible change after stamping** → verify `out_stamped\` has your stamped files. Then run the injector from the **repo root** so it sees subfolders.  
- **Nothing injected** → ensure base names match (e.g., `copy_*.bmp` ↔ `copy.icn`).  
- **OBJ import looks tiny or scattered** → that’s DCC/format scale/axis, not stamping. Fix in Blender/MilkShape; reconvert to ICN; re-inject textures.

---

## 10) What to commit vs generate

**Commit these (source of truth):**
- `README.md`
- `doubleclick-stamper.bat`
- `Make_ICN_Candidates_All_Transforms.bat`
- `Rename_FlipY_ICN_All_Subfolders.bat`
- `ps2icon_to_obj.exe`
- `obj_to_ps2icon.exe`
- `stamp_like_example.py`
- `icn_texture_replace.py`
- `box.txt`
- `transforms.cfg`
- Base textures you want to ship: `copy.bmp`, `del.bmp`, `delete.bmp`, `list.bmp`
- Any sample/example `.icn` you want in the repo (optional but useful): `copy.icn`, `del.icn`, `list.icn`

**Do NOT commit (generated / build artifacts):**
- `out_stamped/`
- `CANDIDATES/`
- Re-built `.icn` variants (unless you purposely track them)
- `.obj` / `.mtl` export results
- Logs and temps

**Suggested `.gitignore`:**
```
/out_stamped/
/CANDIDATES/
/*.obj
/*.mtl
/*.log
/*.tmp
```

---
