# Landing Page — Design Rationale

> For Codex review. Covers `index.html` + `assets/css/style.css`.

## Layout decisions

- **Grid vs flex**: tools grid uses CSS Grid (`grid-template-columns: 1fr` → `repeat(2, 1fr)` at the breakpoint) because cards are a symmetric 2D collection with no need for wrapping logic — Grid states intent directly. Everything else (header bar, CTA group, footer row) uses Flexbox because it's one-dimensional alignment (space-between, wrap on narrow screens).
- **Single breakpoint at 720px**, per the constraint. Below it: single-column tool cards, smaller hero type. Above it: 2-column tool grid, larger hero `h1`. Tested by resizing the CSS viewport values mentally against 360px and 1440px — at 360px all flex containers wrap (nav, footer, CTA group) rather than overflow, since nothing has a fixed width.
- No max-width tension: `--max-width: 960px` centers content on desktop without a separate "container" class per section — every section reuses one `.wrap`.

## Color / spacing system

- CSS custom properties (`:root` variables) for color and spacing rather than hardcoded values, so Codex or a future editor can retheme in one place. Spacing uses a small scale (`--space-1` … `--space-5`) instead of arbitrary rem values scattered through the file.
- Accent color (`#14532d`, dark green) chosen for CTA buttons/links only — not used decoratively — to keep the "utility tool," not "product," feel per the brief.
- Security banner uses a distinct amber/orange stripe (`--color-warn-*`) so it reads as a warning at a glance without JS or an icon font — just a Unicode ⚠️ glyph (system font, no external icon set).

## What I read to ground the content (cite file:line)

- `README.md:1-31` — repo tagline, tool table (`slp-split-pdf` row), security warning wording, license note ("未指定。預設 All Rights Reserved").
- `ARCHITECTURE.md:1-17,21-66,70-101` — the three goals (G1/G2/G3), the "10-second" summary used in the Architecture callout is a condensed paraphrase of ARCHITECTURE.md §1.2–§1.3 and §2.1 (manifest + `run(argv)` contract, lazy import, no central registry), not a copy of §10's full summary.
- `tools/slp-split-pdf/tool.yaml:1-7` — name, summary, status: stable, runtime.
- `tools/slp-split-pdf/main.py:19-37` — actual argparse flags (`--input`, `--output-dir`, `--mode`, `--pages`) used to build the real usage snippet in the tool card.
- `tools/slp-split-pdf/README.md:9-23` — quickstart commands (venv + pip install + `python split.py ...`) reused verbatim in the Quickstart section.
- `tools/class-photo-rename/tool.yaml:1-7` — name, summary, status: wip, runtime.
- `tools/class-photo-rename/main.py:26-44` — argparse flags (`--input-dir`, `--output-dir`, `--mapping`) and the fact it's an unimplemented skeleton (`TODO`, prints a stub message) — reflected as "skeleton demo, 邏輯未實作" next to the card link.
- `SECURITY.md:1-16` — exact list of what must never be committed, used to phrase the security banner.
- `cloudsams:1-16` — confirms `./cloudsams <tool>` is the real dispatcher invocation shown in the tool card snippets.
- `git log -1 --format=%ad` → `2026-07-02`, used as the footer build-date stamp (static, since no JS is allowed to compute it at load time).

## What I did NOT do, and why

- **No JavaScript at all**, not even the <2KB allowance. Nothing on this page needs interactivity — nav is anchor links, CTAs are `<a>` tags, and a mobile nav toggle isn't needed because the nav is only 3 links that wrap fine in a flex row at 360px. Adding JS here would be complexity with zero functional payoff.
- **No `class-photo-rename` "try it" snippet dressed up as working** — the tool prints a TODO stub, so the card snippet shows the real (currently no-op) invocation and the card is explicitly labeled "skeleton demo, 邏輯未實作" rather than implying it's usable.
- **Did not touch `tools/_template`** — it's not a shippable tool (no real `summary`/`status` meant for end users), so it's excluded from the tools grid by design, matching how `cloudsams list` would only show folders a teacher should run.
- **No separate `/docs` page** — the brief says don't rewrite ARCHITECTURE.md; the Architecture section here is a short paraphrase plus a direct link, not a duplicate render.
- **Did not add a `<meta name="theme-color">` or Open Graph tags** — out of scope for the stated content blocks, and speculative for a utility page nobody will share as a social card.
- **Footer date is a static string, not computed** — the constraint forbids JS in general and I only get a <2KB allowance for "really needed" interaction; a build timestamp doesn't qualify, so I hardcoded the `git log -1` date at authoring time. This will go stale on future commits — see below.

## Accessibility considerations

- Semantic landmarks: `<header>`, `<nav aria-label="主導覽">`, the security banner uses `role="note" aria-label="安全提示"` since it's supplementary emphasis, not primary content flow, `<main>`, per-tool `<article>`, `<footer>`.
- Color contrast: accent green `#14532d` on white and white-on-green both exceed 4.5:1 (WCAG AA) for body text size; warning banner text `#5c3d05` on `#fff4e0` background also passes AA for normal text. Badge colors (`--badge-*`) chosen as dark-text-on-light-tint pairs, not light-on-light.
- Focus states: `:focus-visible` outline added explicitly for links/buttons since the browser default can be inconsistent across the two CTA button styles.
- No content conveyed by color alone — status badges also carry text ("stable"/"beta"/"wip"), not just background color.
- Code snippets use `<pre><code>` (not images of terminal output), so they're selectable and readable by screen readers.

## Things I'd improve with more time

- The footer build-date is hand-typed from `git log -1` output at write time rather than generated by a CI step that rewrites it on each deploy — it will silently go stale. A GitHub Action that templates this one line in before Pages publish would be a lightweight fix, but that's a build-pipeline change, not something this static-HTML task should introduce unasked.
- `ARCHITECTURE.html` and `SECURITY.html` links assume GitHub Pages is configured to also serve rendered HTML for those markdown files (or a redirect exists) — I did not verify how Jekyll/Pages resolves `.md` → `.html` linking in this repo's current Pages config. Worth confirming before merge; if Pages doesn't auto-render those, the links should instead point at the GitHub blob URLs (`https://github.com/ai-lish/cloudsams-tools/blob/main/ARCHITECTURE.md`).
- Once more than ~4-6 tools exist, the 2-column grid may want a 3rd breakpoint around 1100px+; not needed yet with 2 tools.
