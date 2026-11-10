# Component completion verification

Date: 2026-11-09. Platform: Windows. Python: 3.11. PySide6: 6.11.1.

All 35 previously pending component types are integrated. The toolbox now exposes 72 component types; the registry contains 77 entries, including window structure entries.

- `pytest.xml`: 1068 tests passed, with zero failures, errors, or skips. The final pytest run completed in 627.44 seconds.
- `release-check.json` / `release-check.png`: Windows source delivery checks passed, including construction, canvas rendering, and independent export for the 35 added types.
- `preview-native.json` / `preview-native.png`: native preview checks passed. Web content loaded, JavaScript returned 42, and OpenGL and RHI surfaces initialized and rendered the expected pixels.
- `export-native.json` / `export-native.png`: the same native checks passed for independent export. The current exported application is `graphics-export/main.py`.
- `workbench-layouts.png`, `workbench-pages-scroll.png`, and `workbench-mdi.png`: captured workbench views for layouts, pages, scrolling, and MDI containers.

Final core Python source and resource fingerprint, calculated by `scripts/source_fingerprint.py`:

`3710861301fbdfafd52981a98788dd8a4d26e141418ff5af9a48b2bb4571233b`

The historical portable executable was not rebuilt. Start the updated source application with `python main.py` from the project root. Component interfaces and usage limits are documented under `docs`.
