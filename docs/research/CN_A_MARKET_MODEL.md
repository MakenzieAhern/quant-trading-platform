# China A-Share Market Model

The framework-independent domain uses stable `security_id` values and keeps market, exchange,
effective-dated board and symbol periods, listing/delisting periods, daily ST/suspension state,
trading sessions, corporate actions and rules separate. Current scope is `CN_A`, SSE/SZSE, and
SSE Main/STAR plus SZSE Main/ChiNext boards.

Rule resolution is effective-dated and applies precedence from security exception, current status,
listing-age override, board, exchange, then market default. Daily-bar signals use information only
after session t and can fill no earlier than the next tradable session at raw OPEN. Suspensions and
one-price limit locks defer fills; pending orders explicitly expire. Buys round down to board lots,
residual cash remains cash, and sells follow the configured settlement/odd-lot policy.

The encoded `cn-a-2010-2025.2` timeline separates pre/post-registration main-board IPO treatment,
STAR from 22 July 2019, and ChiNext before/after 24 August 2020. Pre-reform first-session mechanics
that cannot be reconstructed safely from daily bars are no-fill. STAR uses minimum buy quantity 200
with one-share increments; other covered boards use 100-share lots. All use RMB 0.01 ticks and
odd-lot liquidation-only behavior. ChiNext transition names identified by the exchange are explicit
security-scoped no-fill rules.

Adjusted values are feature inputs only. Corporate actions must transform holdings and cost basis
explicitly. Complete source terms can update cash, quantity and cost basis; incomplete terms block
eligibility. Official studies remain blocked by the unaudited historical universe.
