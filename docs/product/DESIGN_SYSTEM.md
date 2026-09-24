# Product design system

## Direction and evidence — 2026-09-22

Selected one direction: neutral sidebar workbench with full-page guided steps and
contextual detail. Existing top-nav/large-type dark-green layout is the baseline;
it has no novice journey and overflows mobile (390px viewport / 880px document).
No further static layout rounds are needed before implementing M1.

Official references read on 2026-09-22:

| Source | Pattern/problem/adoption | Not adopted |
|---|---|---|
| [Linear redesign](https://linear.app/now/how-we-redesigned-the-linear-ui) | Sidebar/header alignment, neutral layers and contrast reduce competing chrome. Apply cohesive tokens across list/detail. | Branding, assets, copied code, large concept exercise. |
| [Stripe full-page](https://docs.stripe.com/stripe-apps/patterns/full-page-apps) | Overview first, linked list/detail and stable navigation while loading. Four-step workspace and summary. | Stripe SDK and product-specific components. |
| [Stripe onboarding](https://docs.stripe.com/stripe-apps/patterns/onboarding-experience) | Contextual setup with explicit next action. Skippable/reopenable orientation. | Account/payment enrollment. |
| [TradingView workspace](https://www.tradingview.com/support/solutions/43000746464-getting-started-with-supercharts/) | Chart workspace, watchlist/details and visible interval/timezone controls. Date-linked charts and watchlist. | Proprietary charts/assets, broker controls, claims of realtime data. |
| [Apple motion](https://developer.apple.com/design/human-interface-guidelines/motion) | Verified in rendered Chrome: purposeful, optional, brief feedback, cancellable motion. Use concise opacity/transform transitions. | Waiting for animations, repeated decorative motion and platform-specific glass treatment. |
| [W3C interaction animation](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) | Optional motion can be disabled; respect OS reduced motion and explicit off. | Treating this AAA criterion as mandatory AA or removing interactions when motion is off. |

## Tokens and behaviors

Single CSS variable palette: background/surface/raised, text/muted/border, primary,
success/error/warning and separate market-up/down. Light warm off-white with cool
neutral surfaces; dark graphite; indigo action accent. Theme defaults to system;
saved choice and market-color preference independent of locale. System fonts only.
Body 15px, line-height 1.65, tabular numbers; h1 28–32px desktop, 26px mobile.
Spacing 4/8/12/16/24/32; radii 6/10/14px; hairline border; restrained shadow.
Sidebar 224px; compact header 64px; workspace max 1440px with 24–32px padding.
Mobile navigation collapses with visible menu control, no full-page horizontal scroll.
Focusable targets ≥40px where possible, 2px focus ring + offset, semantic form labels.

Primary action visually unique on first use. Avoid giant financial KPIs on homepage.
No long hashes on first-use surfaces; lineage remains available in disclosure/details.
All async areas keep their surrounding navigation. Errors explain next step and retry.
Drafts persist before leaving; exit has explicit keep/discard/stay semantics.
Dialog uses native modal focus handling; all essential actions also visible outside
keyboard shortcuts. Monetary values remain exact server strings throughout UI.

Transitions use project target ranges from PRODUCT_MASTER. Reduced motion is both
OS-aware and explicitly selectable; no business timing depends on animation.

## Baseline findings

- Root lands directly on backtest history with IDs and AAPL_fixture, not an A-share
  start experience. New user intent is unclear.
- Chinese navigation opens an English-only Create Backtest form with a long scroll.
- Strategy detail starts with formulas and SHA; there is no configure action.
- Only dark-green styling; remote Google fonts and body min-width 880px.
- Service status says development/paper; does not show data freshness separately.
- Formal reports are correctly retained but no real exploratory runner is exposed.

Evidence location and per-flow status live in ACCEPTANCE.md. Agent observations
are not a claim of novice-user satisfaction testing.
