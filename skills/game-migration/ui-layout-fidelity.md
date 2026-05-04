# Game Migration UI Layout Fidelity

Use this skill after Unity UI recon is complete but the migrated frontend still
does not match the original layout.

## Goals

- Prevent the "recon was done, but the screen is still only approximately
  correct" failure mode.
- Force translation of canvas behavior, panel chrome, slot frames, label
  offsets, and layering instead of copying only a few coordinates.
- Keep browser validation tied to the current running build rather than stale
  preview processes.

## Rules

- Do not treat extracted RectTransform coordinates as sufficient on their own.
- Preserve the original screen's reference canvas or equivalent scaling model
  instead of converting everything to free-floating percentage layout.
- Translate top panel, main surface, and bottom panel as distinct source-backed
  layers before polishing local details.
- Do not accept a migrated screen where source-backed central content is
  present but surrounding chrome such as top panels, bottom panels, side
  buttons, currency strips, or label backplates is still hand-made CSS
  approximation.
- Reuse source panel and slot art where it exists; do not replace it with
  generic gradients, pills, or dashboard cards.
- Preserve source-backed odd mappings until source evidence proves them wrong.
- If screenshot-guided parity is required but the task has not been routed to
  a vision-capable execution path, mark that as process risk before claiming
  fidelity completion.
- Verify the browser is hitting the intended dev or preview server before
  trusting a fidelity review.

## Browser Validation

- Record the server type, port or entrypoint, dev versus preview mode, and
  whether the loaded page is confirmed to use the latest bundle.
- Treat "page opened without console errors" as insufficient for visual
  fidelity acceptance.

## Acceptance Checklist

- Coordinate correctness: extracted positions, anchors, pivots, offsets, and
  scale behavior match the source screen.
- Chrome completeness: persistent panels, edge controls, strips, frames,
  labels, and source-backed decorative structure are present.
- Hierarchy fidelity: shell layers and local content are owned by the same
  kind of source hierarchy as the original screen.
- If only coordinate correctness is satisfied, the screen is not complete.

## DDGC Notes

- `DreamDeveloperGame-Crossover/Assets/Scenes/EstateManagement.unity` is the
  town layout authority.
- DDGC town should preserve a small top estate panel, central estate surface,
  and bottom embark or roster panel rather than a web dashboard composition.
- Source-backed town chrome includes assets such as `save_name_bg.png`,
  `btn_play.png`, `char_slot.png`, and `building_label_bg01.png`.