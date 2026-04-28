# Game Migration Unity UI Recon

Use this skill before implementing or reviewing frontend migration of a Unity UI.

## Goals

- Force a source-first workflow.
- Inspect prefabs, scenes, scripts, sprites, atlases, Spine assets, and localization files before frontend edits.
- Preserve hierarchy, layout, and asset identity instead of improvising a generic web UI.

## Rules

- Name the exact screen or flow in scope before coding.
- Inspect likely Unity source files and reconstruct hierarchy, RectTransform layout, sorting order, and interactions.
- Build an asset manifest that maps source paths and intended frontend usage.
- Write a migration brief before frontend edits and record fidelity risks.
- Treat missing source assets or unknown structure as blockers, not as permission to substitute generic UI.