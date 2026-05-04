# Game Migration UI Product Sense

Use this skill whenever a migration phase touches player-facing game UI.

## Goals

- Keep the migrated screen feeling like a game surface instead of a generic web page.
- Preserve information hierarchy, direct manipulation, iconography, and layout identity.
- Reject placeholder completion for asset-backed UI.

## Rules

- Prefer landscape-first composition and preserve the original game's effective viewport.
- Keep primary gameplay state visible at a glance and place actions near the state they affect.
- Reject dashboard cards, marketing hero sections, and long scrolling layouts for core game loops.
- Treat missing icons, art, and interaction affordances as incomplete migration on asset-backed screens.
- Validate migrated UI by opening the screen, clicking representative actions, and checking for layout or console issues.

## Review Checklist

- Separate interaction completeness from fidelity completeness on migration
  reviews.
- Treat a usable screen as proof that the interaction path exists, not proof
  that visual migration is faithful.
- When source-backed UI exists, reject completion claims that leave the screen
  functionally usable but visually web-like or approximate.

## DDGC Notes

- Town and meta screens should feel like game control surfaces, not SaaS dashboards.
- Hero, building, provisioning, and result flows should preserve identity and clear return affordances.