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

Adjusted values are feature inputs only. Corporate actions must transform holdings and cost basis
explicitly. Because the production corporate-action pipeline is incomplete, official studies are
currently blocked.
