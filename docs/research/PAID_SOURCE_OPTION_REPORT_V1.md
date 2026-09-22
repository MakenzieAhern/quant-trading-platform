# Paid source option report V1

Date: 2026-09-20

## Option

| Field | Finding |
|---|---|
| Provider | Shenzhen Securities Information Co., Ltd. (SSIC), the SZSE-authorized information distributor |
| Product | SZSE market-data / end-of-day data service; exact archival product name is not publicly stated |
| Potential facts | Per-security historical daily OHLCV and transaction value; the public page describes Level-1 fields and an end-of-day service |
| Remaining blocker potentially solved | Exact 2011-07-25 OHLCV for 239 ChiNext securities |
| Historical 2011 coverage | Not publicly documented; manual confirmation required |
| Price | Not publicly documented |
| Application | Contact or authorization process required; detailed requirements are not publicly documented |
| Free official alternative | Exact close and factor-relevant liquidity decision closed for all 239; exact open/high/low/volume/amount remain partial |
| Research benefit | Could replace a partial feature-only methodology choice with complete exact official raw bars |
| Required or convenient | `UNDETERMINED_NOT_AUTHORIZED`; no evidence establishes that purchase is the only route |

Official product description:
`https://www.szse.cn/English/services/dataServices/`.

Official contact page:
`https://www.szse.cn/English/about/contactus/index.html`.

The public description identifies SSIC as the authorized distributor and lists
Level-1 fields including security code/name, open, high, low, close, volume and
value. Its end-of-day subsection explicitly lists close and high/low, but does
not establish historical depth, exact archival schema, delivery terms or price.
Those details must be confirmed manually before claiming the option solves the
gap.

`PAID_SOURCE_REQUIRED = NO`: necessity has not been demonstrated. No inquiry,
application, order or purchase is authorized by this report.
