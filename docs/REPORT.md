# Confluence MCP Server — Verification Report

| | |
|---|---|
| **Document** | `REPORT.md` — Phase 5 (Verify) |
| **Subject** | `pdlc-confluence-mcp-server`, branch `feature/confluence_mcp_Phase2` |
| **Verified against** | `spec.md` v1.0 · `openapi.yaml` v1.0.0 |
| **Type** | **Baseline report.** No code was changed. It records what the code does today against the spec. |
| **Re-run** | After every milestone; replace the numbers, keep the structure. |

## 1. Verdict

**Not production-ready. The server's own tests pass, but they pass partly because they test an imagined library.**

- **One High finding:** `confluence-createPage` uploads any file on the server's disk to Confluence if the caller names its path (DEF-1) — *reproduced*.
- **The headline tool set is smaller than advertised.** Four tools are registered. The README and the default list advertise six; `searchPages` and `uploadAttachment` do not exist, and `confluence-health` is not registered (DEF-4) — *reproduced*.
- **The main read-by-title tool rejects almost every real title.** `Release Notes v2.1`, `Q3 Plan: Budget`, `Design (draft)`, `R&D Overview`, `Café menu` and `Meeting - 2024.05.01` are all refused (DEF-3) — *reproduced*.
- **A real 404 is not handled.** The Atlassian library raises `ApiError`; the tools catch only the project's own exceptions, and the tests mock a `None` return the library never gives (DEF-6) — *library behaviour reproduced*.
- **CI cannot succeed as written**: it requests Python 3.11; the project requires ≥ 3.13 (DEF-13) — *reproduced*.
- Good: ruff is clean, the layering is sound, the exception hierarchy is typed, attachment text extraction and HTML-to-text are well tested, and the health route is tested.

| | Count |
|---|---|
| Requirements in spec | 7 tool FRs + 12 cross-cutting FRs + 8 CFG + 8 NFR + 10 SEC + 4 ERR = **49** |
| ✅ Verified by a behavioural test | **3** (FR-9, FR-12, FR-14) |
| 🟡 Implemented, partly tested | **12** |
| ⚪ Implemented, no behavioural test | **2** |
| ❌ Not implemented / not as specified | **32** |
| Defects found | **19** — 1 High · 12 Medium · 6 Low |

A high ❌ count is expected: this spec's TARGET section is large because the baseline is thin. It is a measurement, not a verdict on the team.

## 2. Evidence

**Environment.** Python 3.13.16 (project requires ≥ 3.13), dependencies installed from `uv.lock` with `--frozen` (`fastmcp 2.12.2`, `atlassian-python-api 4.0.7`, `PyMuPDF 1.26.4`). Real Confluence was **not** contacted.

```text
$ pytest tests/ -q --cov=src --cov-report=term-missing
80 passed, 6 warnings in 4.62s

Name                                               Stmts   Miss  Cover   Missing
src/atlassian/config/config.py                        13      0   100%
src/atlassian/config/config_reader.py                 15      4    73%   20-37
src/atlassian/servers/confluence_server.py            43      4    91%   20-22, 80
src/atlassian/services/confluence_service.py         305    105    66%   72-73, 86-117, 186-189, ...
src/atlassian/tools/confluence_tool.py               156     33    79%   75-76, 169-176, 208, ...
src/atlassian/utils/log_helper.py                     15      3    80%   53-55
TOTAL                                                559    149    73%

$ ruff check .          → All checks passed!
$ uv lock --check       → Resolved 94 packages
$ uv sync --locked --python 3.11   (what the CI workflow requests)
error: The requested interpreter resolved to Python 3.11.17, which is incompatible
       with the project's Python requirement: `>=3.13`
```

**Defects reproduced by executing the code** (probe script, mocked HTTP only):

```text
tools/list (default config)  : 4 tools
hasattr(config, "ENABLED_CONFLUENCE_TOOLS") : False
validate_page_title: "Release Notes v2.1" False · "Q3 Plan: Budget" False · "Design (draft)" False
                     "R&D Overview" False · "Café menu" False · "Meeting - 2024.05.01" False
validate_space_key : "ENG" True · "~5b10ac8d82e0…" (personal space) False · "MY SPACE" True · "../x" False
createPage attachment=/tmp/tmpXXXX.env (contains TOKEN=…):
   attach_file called with filename='/tmp/tmpXXXX.env', name='file1.pdf'
   result.attached_files = [{'filename': 'file1.pdf', 'status': 'success', ...}]
readPageById(space_key="WRONGSPACE", page_id="9") → returned the page; get_page_by_id received only ('9',)
returned url                  : https://x.atlassian.net/wiki/pages/9
  → fed to extract_page_id_from_url → (None, None)   (canonical /spaces/ENG/pages/9/Title → ('9','ENG'))
atlassian.Confluence.get_page_by_id on HTTP 404 (mocked with `responses`) → RAISED ApiError
print( in confluence_tool.py   : 17        timeout under src/ : none        to_thread / executor : none
```

`tools/list` printed the four real names: `confluence-createPage`, `confluence-readPageById`, `confluence-readPageByTitle`, `confluence-readPageByUrl`.

**Not run:** Docker build, container health probe, Helm/Terraform, Cloud Build, Trivy, pip-audit, trufflehog, the Azure deploy, and any call to a real Confluence site. Findings marked **R** below come from reading the code, not executing it. The one thing worth confirming on a live site is the correct page-URL shape (T-13).

## 3. Traceability — requirement → code → test

**Key:** ✅ behavioural test · 🟡 partly tested · ⚪ implemented, no behavioural test · ❌ not implemented or not as specified.

### 3.1 Tools

| ID | Tool | Code | Test evidence | Result |
|---|---|---|---|---|
| FR-1 | `readPageById` | `get_page_content_by_id` | Service success; tool success / validation / Confluence-error / **not-found via a `None` mock the real library never returns**. Attachments inline path, `space_key` use untested | 🟡 |
| FR-2 | `readPageByTitle` | `get_page_content_by_title` | Service and tool success; not-found via `None` mock. Title validation test **pins the over-narrow rule as correct** | 🟡 |
| FR-3 | `readPageByUrl` | `get_page_content_by_url`, `extract_page_id_from_url` | Tool-level success and validation error with the service mocked. **`extract_page_id_from_url` and `get_page_content_by_url` have no direct test**; the URL-build test asserts `/pages/123`, i.e. pins DEF-11 | 🟡 |
| FR-4 | `createPage` | `create_page_with_content`, `attach_file_to_page` | Success, validation errors, create/attachment error paths (mocked). No test for path confinement, file name, partial success, duplicate title | 🟡 |
| FR-5 | `confluence-health` | `_register_health_check` | 4 tests (success, no spaces, Confluence error, unknown error). **Not registered by default** | 🟡 |
| FR-6 | `confluence-searchPages` | — | Does not exist | ❌ |
| FR-7 | `confluence-uploadAttachment` | — | Does not exist | ❌ |

### 3.2 Cross-cutting

| ID | Result | Evidence / note |
|---|---|---|
| FR-8 | 🟡 | Module-setup tests; statelessness is a constructor flag, untested (and deprecated in this FastMCP — warning seen) |
| FR-9 | ✅ | `test_health_check_returns_healthy_status` |
| FR-10 | ❌ | Default list names 6 tools; 2 absent, health omitted (DEF-4). A test (`test_register_tools_default_set`) documents the *intersection* rather than fixing it |
| FR-11 | ❌ | `config.ENABLED_CONFLUENCE_TOOLS` is never defined; test sets it with `raising=False` (DEF-5) |
| FR-12 | ✅ | `test_register_tools_tool_tags` |
| FR-13 | 🟡 | Structured dicts; per-tool tests |
| FR-14 | ✅ | 5 `html_to_plain_text` tests (valid, scripts, empty, invalid type, complex) |
| FR-15 | 🟡 | `extract_file_content` (txt/pdf/docx/unsupported/empty/bad decode/exception) and `list_attachments` tested; the inline download-and-extract loop in the read methods is not; unbounded (DEF-10) |
| FR-16, 17, 18, 19 | ❌ | DEF-11, 7, 8, 20 (see "Also noted") |
| CFG-1 | 🟡 | `config.py` 100% by import; precedence not asserted |
| CFG-2 | ⚪ | `config_reader.py` lines 20–37 (the Azure branch) untested |
| CFG-3…8 | ❌ | DEF-12, 12, 18, 12, 15 |
| NFR-1, 2, 3 | ❌ | DEF-9 |
| NFR-4 | 🟡 | `log_helper.py` 80% |
| NFR-5, 6, 7, 8 | ❌ | DEF-8; DEF-10; 73% < 85%; DEF-13 |
| SEC-1 | ❌ | Unresolved by design (Q-7) |
| SEC-2 | 🟡 | Token passed to the client constructor, not logged (read); no leak test |
| SEC-3, 4, 5, 6, 7, 10 | ❌ | DEF-1, 2, 3, —, 19, — |
| SEC-8 | ⚪ | True by construction (only the ID is used); no test |
| SEC-9 | 🟡 | `pip-audit`, trufflehog, Trivy are in CI; not run here |
| ERR-1…4 | ❌ | DEF-6, 19 |

## 4. Defects

Severity: **High** = exploitable or data-exposing · **Med** = wrong result or reliability · **Low** = hygiene.
"How": **X** = executed here · **R** = read in code.

| ID | Sev | Finding | Where | How | Spec | Task |
|---|---|---|---|---|---|---|
| **DEF-1** | **High** | `createPage.attachment` is a server-local path opened with no confinement. A caller names `/proc/self/environ`, a mounted secret or a `../` path; the server uploads it to a Confluence page the caller (or anyone with page access) can read back. | `create_page_with_content` → `attach_file_to_page` | **X** | SEC-3 | T-6 |
| DEF-2 | Med | Every attachment is uploaded as `file1.pdf` regardless of its real name or type (`custom_filename = 'file1.pdf'`). | `create_page_with_content` | **X** | SEC-4 | T-6 |
| DEF-3 | Med | `validate_page_title` allows only `[A-Za-z0-9 _-]`: realistic titles are refused, so the agent concludes the page doesn't exist. Space keys: personal spaces (`~…`) refused, whitespace accepted. `createPage` checks titles differently from reads. | `validate_page_title`, `validate_space_key` | **X** | SEC-5 | T-10 |
| DEF-4 | Med | Four tools registered; README and default list advertise `searchPages`, `uploadAttachment` (don't exist; logged as "Unknown tool requested"); `confluence-health` exists but isn't in the default list. | `register_tools`, `README.md` | **X** | FR-10 | T-20 |
| DEF-5 | Med | `ENABLED_CONFLUENCE_TOOLS` is read with `getattr(config, …)` but `config.py` never defines it: tool selection cannot be configured from the environment or App Configuration. | `confluence_tool.py`, `config.py` | **X** | FR-11 | T-16 |
| DEF-6 | Med | On 404 the library raises `ApiError` (it never returns `None`). Tools catch only `ConfluenceError`, so `NotFoundError`/`PAGE_NOT_FOUND` is unreachable in production and a raw exception reaches the agent; the same applies to 401/403/duplicate-title/timeouts. Tests mock `None` and so miss it. | all four tools; `test_service.py:380-425` | **X** (library) · R (tools) | ERR-1 | T-11, T-24 |
| DEF-7 | Med | `readPageById` validates `space_key` and never uses it: the page is returned from whatever space holds the ID. | `get_page_content_by_id` | **X** | FR-17 | T-12 |
| DEF-8 | Med | `_resolve_context_params` (used by `readPageByTitle`) makes 5 context-lookup attempts, **prints** `dir(ctx)`, `ctx.__dict__` and every hit, and lets context attributes replace the caller's `space_key`/`page_title`. 17 `print()` calls in total. Two tests assert the override as intended. *(Override reproduced with a stand-in context object; whether a real FastMCP `Context` carries those attributes was not established. The prints run unconditionally.)* | `confluence_tool.py` | **X** | FR-18, NFR-5 | T-9 |
| DEF-9 | Med | Tools are `async def` but call the synchronous library and `requests` directly: one slow Confluence call blocks the event loop for every agent. No timeout exists anywhere in `src/`. `ruff` is configured to ignore `ASYNC230`. | service and tools | **X** (grep) · R | NFR-1…3 | T-8 |
| DEF-10 | Med | Every read downloads and parses **all** (≤ 50) attachments inline with no count, size or time bound — PDFs through PyMuPDF — and then `except Exception: pass` swallows failures. Unbounded response size and memory; untrusted bytes parsed on the request thread. | `get_page_content_by_id/_title`, `list_attachments` | R | NFR-6, SEC-6 | T-14 |
| DEF-11 | Med | The page URL returned is `{client.url}/pages/{id}`. It does not match any URL form the server's own parser accepts, so it can't be given back to `readPageByUrl`. (A mocked response in the tests carries `_links.webui`, which is ignored.) | read methods | **X** | FR-16 | T-13 |
| DEF-12 | Med | **Names and ports disagree.** `.env.example` ships `PORT=8080` and `CONFLUENCE_USERNAME`; the code reads `CONFLUENCE_PORT` and prefers `CONFLUENCE_EMAIL`; with only a username the client is built `cloud=False` (Server/DC mode) against a Cloud site. The Dockerfile `CMD` hard-codes 9001, its `HEALTHCHECK` reads `PORT` (8080 if the example is used) and does a bare TCP connect; Helm declares `containerPort` and probe port 8080. `CONFLUENCE_URL` example omits `/wiki`; Helm includes it. | `.env.example`, `config.py`, `Dockerfile`, Helm values | R | CFG-3…7 | T-16, T-17 |
| DEF-13 | Med | CI uses `python-version: "3.11"`; `requires-python >=3.13` — `uv sync --locked` fails (reproduced). Dockerfile runs `uv sync --no-dev` without `--frozen`. `requirements.txt` is stale (`fastmcp==1.0` vs locked 2.12.2) and starts with a BOM. | CI workflow, `Dockerfile`, `requirements.txt` | **X** | NFR-8 | T-17 |
| DEF-14 | Low | Competing/stale deployment assets: `Dockerfile.mcp-https` runs `src/mcp_server_https.py`, which does not exist; `cloudbuild.yaml` and Helm target GKE and GCP project/service-account IDs; the CI workflow targets Azure Container Apps. | repo root, `terraform-app-provision/` | R | Q-4 | T-19 |
| DEF-15 | Low | Real e-mail address, company tenant URL and GCP identifiers committed in `values-files/values-dev.yaml`; secret defaults of `"DUMMY"`. | Helm values | R | CFG-8 | T-19 |
| DEF-16 | Low | README: **unresolved git merge-conflict markers**; describes `conftest.py`, `test_confluence_client.py`, `run_tests.py` (absent) and "1,200+ tests" (actual 80); documents `SECRET_KEY`, CORS, rate limiting, OAuth (none exist); health route given as `/health` (actual `/mcp/confluence/health`). | `README.md` | **X** (markers counted: 2) | — | T-28 |
| DEF-17 | Low | Dead code: `MCPResponse`/`PageData`/`CreatePageData` models, shutdown/signal handlers that are never installed, an OAuth branch driven by settings that don't exist; `stateless_http` constructor argument is deprecated (warning seen); UTF-8 BOMs in `confluence_server.py`, `requirements.txt`, `run_all_tests.py`. | various | **X** | — | T-18 |
| DEF-18 | Low | No startup validation: bad config surfaces on the first tool call. The client is cached for the process; `reset()` is never called, so a rotated token needs a restart. First-use creation is unguarded against concurrent callers. | `get_confluence` | R | CFG-6 | T-16 |
| DEF-19 | Low | Error envelopes echo `title`, `page_title` and the attachment **file path** (a server path disclosure); attachment errors embed raw library text. | tools | R | SEC-7 | T-7 |

### Also noted (not numbered defects)
- **DEF-20 (design gap, FR-19):** `createPage` creates the page, then attaches. If the attachment fails the result still looks successful (only the per-file entry says `error`) and the page exists. Retried by an agent it creates a duplicate title.
- **Indirect prompt injection (SEC-10):** page bodies and attachment text go straight to the agent; no tool description warns that it is untrusted.
- **Blast radius (SEC-1):** this is a *read* server over an organisation's wiki. Any caller reaching it can read every space the service account can.
- `ruff` passing means less than it appears: per-file ignores cover `BLE001` (broad `except`), `S110` (`except: pass`), `F841`, `ASYNC230` — exactly the patterns in DEF-6, 9, 10.
- Registration test and README disagree openly; the test documents the intersection ("only the tools present in both…"), so the team has seen DEF-4.

## 5. Acceptance criteria status

| AC | Covers | Status | Basis |
|---|---|---|---|
| AC-1 | Real titles readable | ❌ | DEF-3, executed |
| AC-2 | 404 → `PAGE_NOT_FOUND` | ❌ | DEF-6, library behaviour executed; tool catch by reading |
| AC-3 | Attachment confinement | ❌ | DEF-1, executed |
| AC-4 | Real attachment name | ❌ | DEF-2, executed |
| AC-5 | `space_key` enforced | ❌ | DEF-7, executed |
| AC-6 | URL round-trips | ❌ | DEF-11, executed |
| AC-7 | No context override | ❌ | DEF-8, stand-in |
| AC-8 | Registered set == documented; env-settable | ❌ | DEF-4, 5, executed |
| AC-9 | Concurrency | ❌ | DEF-9, read |
| AC-10 | Retry rules | ❌ | none implemented, read |
| AC-11 | Attachment bounds | ❌ | DEF-10, read |
| AC-12 | `.env.example` works; probe on right port | ❌ | DEF-12, read; container not run |
| AC-13 | No content in logs | ❌ | DEF-8, read |
| AC-14 | Partial-success status | ❌ | DEF-20, read |
| AC-15 | Duplicate title → `CONFLICT` | ❌ | DEF-6, read |

**0 of 15 pass.** The ACs describe the *target* behaviour; the baseline's own behaviour is what the existing 80 tests cover. Each failing AC is the starting test of its task, not a regression.

## 6. Contract check (`openapi.yaml`)
- Valid OpenAPI 3.1; 4 tools, 15 schemas.
- Tool names and required-argument lists were generated from the live server and match.
- Result and envelope schemas were written from reading the code; they are **not** machine-checked against real output until T-26.
- `x-mcp-unregistered` records the three tools that don't exist as registered tools.
- `x-target-*` marks constraints the spec requires and the code does not yet enforce.

## 7. Recommended next step

Approve `plan.md` and `tasks.md`, then say `proceed` to start **M1**. Order inside M1: **T-6 → T-8 → T-10 → T-9 → T-7**. Before M2, do T-24's HTTP-boundary test harness so that "green" starts meaning something.

**Interim mitigations if M1 can't start soon:**
1. Don't expose `confluence-createPage` (DEF-1) — or ensure the container can read nothing sensitive beyond its own environment.
2. Keep the server off the internet and off any network agents don't need (SEC-1).
3. Fix the CI Python version (one line) so the pipeline can run at all (DEF-13).

Decisions waiting on a human: **Q-1** search/upload · **Q-2** richer content · **Q-3** Server/DC in scope · **Q-4** authoritative deployment path · **Q-5** `space_key` semantics · **Q-6** attachments on by default · **Q-7/SEC-1** caller identity · **Q-8** health tool · **Q-9** error style vs Jira. Separately: the real e-mail and tenant URL in `values-dev.yaml` (DEF-15) need a human call on whether any rotation or history clean-up is needed.

## 8. Sign-off

| Gate | Approver | Date | Decision |
|---|---|---|---|
| Spec accepted | | | |
| Plan accepted | | | |
| Baseline accepted | | | |
