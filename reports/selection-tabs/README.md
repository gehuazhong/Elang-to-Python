# Selection tab verification

Date: 2026-11-09. Platform: Windows, PySide6 6.11.1.

- `regression.xml`: 410 related tests passed, zero failures, errors, or skips. This includes 22 new selection tab tests and regression coverage for existing components, scaling, events, property mappings, and code export. Pytest elapsed time: 62.76 seconds.
- `verification.json`: native page switching, designer property visibility, canvas clicks and undo, and isolated Python export checks passed.
- `preview.png`: native window showing top, bottom, left, right, and hidden tab bars.
- `designer.png`: the example open in the designer with the new tab header property group visible.
- `export/main.py`: independently runnable export of the comparison example.

The editable example is `examples/选择夹表头与页面.uipro` in the project root. Usage and property descriptions are in `docs/选择夹属性.md`.

Core Python source and resource fingerprint from `scripts/source_fingerprint.py`:

`83d2d420e51a5ce6b2973bbdbac7eb6a055b93069a4b20609f407deb3e212ec5`

Restart the source designer to load the updated registry. Historical portable executables and previously exported applications were not rebuilt.
