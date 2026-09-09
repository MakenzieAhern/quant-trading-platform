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
The code records rule ID, publication date, effective range, scope and provenance. Main-board rules
are split at the 2023 registration reform; STAR starts in 2019; ChiNext is explicitly split on
2020-08-24. Pre-reform IPO sessions and named ChiNext transition securities use conservative no-fill
where daily bars cannot prove executable liquidity. Unknown security-specific suspensions or special
dispositions remain a documented gap; current rules are never projected backward by default.
