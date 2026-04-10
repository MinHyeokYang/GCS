# Assignment 1.1 - GCS-PULSE (Snippet API) CLI vs MCP

> Token usage is estimated with ceil(characters / 4) for request/response payloads.

## Per-case comparison

| Path | Case | Input Tokens(est) | Output Tokens(est) | Total Tokens(est) | Duration(ms) |
|---|---|---:|---:|---:|---:|
| CLI | List meeting rooms | 10 | 1136 | 1146 | 2947 |
| MCP | List meeting rooms | 14 | 1033 | 1047 | 788 |
| CLI | List room #1 reservations today | 22 | 94 | 116 | 583 |
| MCP | List room #1 reservations today | 23 | 110 | 133 | 944 |
| CLI | List room #2 reservations today | 22 | 1 | 23 | 484 |
| MCP | List room #2 reservations today | 23 | 15 | 38 | 474 |

## Averages

| Path | Avg Input | Avg Output | Avg Total | Avg Duration(ms) |
|---|---:|---:|---:|---:|
| CLI | 18 | 410.33 | 428.33 | 1338 |
| MCP | 20 | 386 | 406 | 735.33 |

## Experience notes

- CLI path is straightforward for scripts and CI (powershell -File ...).
- MCP path is better when integrating the same operations into agent tool-calling workflows.
- For read-only operations in this run, token/latency differences are small; MCP has extra protocol overhead.

