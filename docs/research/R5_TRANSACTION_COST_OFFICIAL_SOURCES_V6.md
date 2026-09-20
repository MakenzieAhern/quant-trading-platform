# R5 transaction-cost official-source closure v6

## Result

Six retained official surfaces close the 2010-2025 stamp-duty interval, the
post-2015 transfer-fee interval and the 2023 handling-fee transition:

- the Ministry of Finance fixes seller-only stamp duty at 1 per mille from
  2008-09-19; State Tax Administration announcement 2023-39 halves it from
  2023-08-28;
- ChinaClear fixes the A-share transfer fee at 0.02 per mille of notional from
  2015-08-01 and 0.01 per mille from 2022-04-29, both sides;
- the CSRC fixes the handling fee at 0.0341 per mille from 2023-08-28, both
  sides.

The executable model is unchanged. The 2010 SSE factbook is only a snapshot of
an investor charge of 1 per mille of face value with a CNY 1 minimum. The 2012
ChinaClear notices identify ChinaClear's collector component and a separate
broker-retained component. The retained 2011-2013 SSE factbooks were also
reviewed, but their fee tables explicitly exclude registration-and-settlement
company charges. Those sources therefore do not define one continuous
investor-total transfer charge or minimum through 2015-07-31.

## Remaining authority boundary

Two public-source claim groups remain unresolved:

- `SSE_TRANSFER_INVESTOR_TOTAL_2010_01_01_TO_2015_07_31`;
- `SSE_TRANSFER_MINIMUM_2010_01_01_TO_2015_07_31`.

The separate research-account net-versus-all-in commission choice still
requires an account contract or an explicit human research convention. No
third-party source was promoted and no strategy study was run.

## Immutable evidence

| Artifact | SHA-256 |
|---|---|
| SSE 2010 factbook | `ff1c1b811bba65e3f4051e7570eb01513b88dd37c0c940efa3311701535a266b` |
| SSE 2011 factbook (reviewed; exclusion note) | `77e4d1f8024f47456a608c119f2e634e3936f5ae1c245f4aefa45ba59f0d0bbe` |
| SSE 2012 factbook (reviewed; exclusion note) | `d1283b557d51b298300b3cb46c1125aabeac0ae86e94cea7ecb15de9befff0bb` |
| SSE 2013 factbook (reviewed; exclusion note) | `5971dc407dff2aefb15ef203b684fba056e56ac351034d0a8f483472278cc4ff` |
| ChinaClear 2015 notice | `27dfd05816a7962101ffa9d218669dd279d4b2096ef6adf299bffb85ecfecf85` |
| ChinaClear 2022 notice | `df193394f3e06b6adad9e01ceea796be470e59b41b718eaf129b6644b0977703` |
| Ministry of Finance 2008 notice | `4edaa053cbc7c2727e183a27f2e974aabb3534e4485522e3675f40ca7a6d8263` |
| State Tax Administration 2023 notice | `dc72b12d9f0c5fa20910a352c4c79f17ecf8fb24e1f3ac68466c98538d076dd9` |
| CSRC 2023 handling notice | `ace59eaf173a71279fe6008d85992418e3e94d782c558132eea558d64fb3866e` |
| Transaction-cost report v6 | `fabfe88adcbc77c3a3692958c2c2a0b27e00a68dfe308477739d159155d3e6f1` |
| Transaction-cost manifest | `fa46e42fb57ea91962c0def607741dd90420e09158e9a189f032b883aaa21dd7` |
| Full-source preflight v15 | `088cf724f2b4cc2aeea3f8733e1cb372f30894e3837eb6c11ca7f2e3c8381102` |
| Preflight manifest | `e60eb20f3547490c33f0f8465ba9b584f7342de6a2833c6e2119c52edda588fb` |

Source checksums and report generation repeat deterministically. New official
pages were retrieved between `2026-09-20T05:46:50Z` and
`2026-09-20T05:49:06Z`.
