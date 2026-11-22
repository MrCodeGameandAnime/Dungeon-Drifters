# M8.9: Region And Enemy Visual Presentation

**Status:** BLOCKED on a separate M8-D6 visual specification and explicit approval. The owner requested expanded presentation; the earlier eight-static-assets-only scope is not approved. No implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate asset pipeline and client sizes at package entry.

## Goal

Plan the expanded visual presentation only after its bounded scope is supplied and explicitly approved. Do not infer the visuals, rendering architecture, runtime surfaces, or deliverables from the earlier static-only proposal.

## Approval Boundary

**Already-approved inputs:** Python remains authoritative for gameplay and clients remain projections/adapters; M7's shared combat model is unchanged. The owner requested expanded visual presentation instead of accepting the earlier eight-static-assets-only proposal.

**Still pending:** a separate bounded M8-D6 specification and explicit approval. The prior eight static asset IDs are historical planning suggestions only, not the approved scope, a minimum deliverable, or a commission.

## Scope

- Revisit the old static-only asset suggestions after approval of the separate visual specification; do not assume those eight items meet the requested expansion.
- Region 2 has no playable routes in M8; no Region 2 visual identity or presentation treatment has been specified or approved.
- Once scope is approved, record its deliverables, asset/source provenance, accessibility and readable fallbacks, platform/runtime targets, and verification matrix in this package.

## Exclusions And Dependencies

No graphical renderer, animation engine, new combat mechanics, boss phases, formations, or hazards are authorized by the current direction. The separate M8-D6 specification must define bounded presentation work without silently expanding gameplay scope. Begin only after the specification and its approval; then revalidate any stable IDs and dependencies. M8.9 qualifies approved visual integration before M8.10.

**Persistence impact:** none for an asset-only implementation. If asset references alter serialized content identities, stop and review that scope separately.

M8.9 can record production evidence once manifest IDs and visual scope are approved. Close only after checking each asset or approved fallback through its actual region or encounter, including the reunion boss.

## Package Gates And Qualification History

Define qualification from the approved D6 specification. It must cover every approved presentation deliverable, client/runtime parity, accessibility/fallbacks, and the actual user-visible integration; do not use the former eight-ID checklist as an assumed scope.

- **Gate A, plan approval:** Blocked; confirm relevant M8-D1 content IDs/associations, receive the bounded expanded-visual specification, and obtain explicit M8-D6 approval before finalizing this package.
- **Gate B, asset integration and focused checks:** Not started; content-reference, fallback and responsive rendering checks.
- **Gate C, exact-SHA qualification and closure:** Not run; relevant root/web/build/content checks and hosted workflow. No MicroPython rerun for asset-only changes unless shared runtime code is touched.

| Implementation SHA | Hosted CI URL/results | Asset/build evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record reviewer disposition, final asset manifest, CI URL and closure here and in the parent.

