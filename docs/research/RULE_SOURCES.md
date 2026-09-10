# A-Share Rule Sources

Market rules are based on exchange/regulator publications rather than market-data vendors:

- Shanghai Stock Exchange trading rules and 2026 revision notice:
  <https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml>
- Shenzhen Stock Exchange trading rules (2023 revision):
  <https://investor.szse.cn/lawrules/index/rule/t20230217_598773.html>
- Shenzhen Stock Exchange ChiNext registration-based trading notice:
  <https://www.szse.cn/aboutus/trends/news/t20200821_580924.html>
- Ministry of Finance 2023 securities stamp-duty reduction:
  <https://www.mof.gov.cn/jrttts/202308/t20230828_3904235.htm>
- CSRC investor guidance describing same-day sale restrictions:
  <https://www.csrc.gov.cn/hubei/c105451/c1292890/content.shtml>
- SSE STAR launch explanation (first five sessions unlimited, then 20%, minimum order 200):
  <https://www.sse.com.cn/star/media/news/c/c_20190719_4866789.shtml>
- SZSE ChiNext investor explanation confirming pre-reform 10%/ST 5%, 24 August 2020 transition,
  post-reform 20%, first-five-session handling, 100-share lots and named delisting exceptions:
  <https://investor.szse.cn/institute/rules/t20200807_580310.html>

Each encoded rule belongs to a non-overlapping effective range and retains a source version.

R1 correction (2026-09-10): main-board registration trading rules were published
on 2023-02-17 but became effective on 2023-04-10, not publication day. Version
`cn-a-2010-2025.2` corrects both exchanges' boundary. Evidence:
[SZSE official chronology](https://www.szse.cn/aboutus/sse/events/t20240110_605593.html)
and [first-batch listing notice](https://www.szse.cn/aboutus/trends/news/t20230411_599874.html).
The retained pilot master contains no main-board listing on April 1-9, so no
young legacy main-board cohort crosses the corrected pilot boundary. A regression
test preserves publication/effective-date separation; this does not by itself
complete the market-rule authority audit.
The code records rule ID, publication date, effective range, scope and provenance. Main-board rules
are split at the 2023 registration reform; STAR starts in 2019; ChiNext is explicitly split on
2020-08-24. Pre-reform IPO sessions and named ChiNext transition securities use conservative no-fill
where daily bars cannot prove executable liquidity. Unknown security-specific suspensions or special
dispositions remain a documented gap; current rules are never projected backward by default.

R1 remaining regression: [300336 issuer notice 2023-044](https://disc.static.szse.cn/disc/disk03/finalpage/2023-06-27/6aac260a-7444-4164-92f1-927d47039c17.PDF)
states that delisting-period trading began on 2023-06-12, with no first-day
price limit and 20% thereafter. Current DailySecurityStatus has no corresponding
effective-dated field; both is_st values yield 20% in the ChiNext resolver.
Accepted name/ST histories do not automatically prove market-rule mapping.
MARKET_RULE_AUTHORITY remains UNVERIFIED pending this mapping and audit.
