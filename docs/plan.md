# Confluence MCP Server — Plan

| | |
|---|---|
| **Document** | `plan.md` — architecture and approach |
| **Owner** | Claude drafts; a human approves at the Phase-2 gate |
| **Implements** | `spec.md` v1.0 (IDs cited throughout) |
| **Status** | §1 is the architecture **as built**. §5 onward is the plan for the TARGET requirements. |

---

## 1. Architecture as built

```
 MCP client (agent)
      |  streamable HTTP, stateless   POST /mcp/confluence    GET /mcp/confluence/health
      v
 ┌──────────────────────────── src/atlassian/ ─────────────────────────────┐
 │ servers/confluence_server.py   FastMCP(stateless_http), health route     │  FR-8 FR-9
 │        │ register_tools(mcp)                                              │
 │ tools/confluence_tool.py   4 @mcp.tool wrappers, error envelopes,        │  FR-1…4 FR-10…13 ERR-*
 │        │                   _resolve_context_params                        │  FR-18
 │ services/confluence_service.py   ConfluenceClient: validation, client    │  FR-14…17 SEC-3…5
 │        │                   cache, body→text, attachment extraction        │
 │ config/…   utils/log_helper.py   exceptions/confluence_exception.py      │  CFG-* NFR-4
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 │ atlassian-python-api  (synchronous, requests)
                                 v
                    Confluence Cloud  /wiki/rest/api/*
```

| Layer | File | Owns | Must not |
|---|---|---|---|
| **Server** | `servers/confluence_server.py` | App construction, health route, transport path | Contain tool or Confluence logic |
| **Tools** | `tools/confluence_tool.py` | MCP names, descriptions, argument schemas, tags, mapping exceptions → envelopes | Parse Confluence responses; touch `atlassian` |
| **Service** | `services/confluence_service.py` | Validation, connection, every Confluence call, body/attachment processing | Import FastMCP |
| **Config** | `config/` | App Configuration → env → default | Hold business rules |
| **Exceptions** | `exceptions/confluence_exception.py` | 11-class hierarchy under `ConfluenceError` | — |

Direction is one-way: **server → tools → service → config**. The service layer
knows nothing about MCP, so it is unit-testable. *Caveat found in verification:*
the existing tests replace the whole `Confluence` class with a `MagicMock`, so
they test our code against an imagined library rather than the real one (see
`REPORT.md` DEF-6).

### 1.1 Technology
Python ≥ 3.13 · FastMCP 2.12.2 · uvicorn · `atlassian-python-api` 4.0.7 (synchronous) ·
BeautifulSoup/lxml (body → text) · PyMuPDF and python-docx (attachment text) ·
Azure App Configuration + `azure-identity` · `uv` · pytest · ruff.
Container: `python:3.13-slim` + `uv`, `uvicorn` on 9001.
CD: GitHub Actions → ACR → Azure Container Apps. *(The repository also contains a GKE/Helm/Terraform/Cloud Build path — see Q-4.)*

### 1.2 Decisions that are not obvious from the code

| # | Decision | Why | Spec |
|---|---|---|---|
| D1 | **Failures are returned as an envelope, not raised.** | Agents branch on `error_code`; established contract. Kept (Q-9). | §5 |
| D2 | **Bodies are returned as plain text**, from storage → view → export_view. | Compact, model-friendly. Costs structure (tables, links, macros). | FR-14 |
| D3 | **Reads inline the text of every attachment.** | One call gives the agent the page *and* its PDFs. Needs bounds (NFR-6). | FR-15 |
| D4 | **Stateless HTTP.** | Horizontal scaling; no session affinity. | FR-8 |
| D5 | **One cached `Confluence` client per process**, verified with a `get_all_spaces` call on first use. | Avoid re-auth; fail early if credentials are wrong. | FR-8, CFG-6 |
| D6 | **`createPage` creates the page first, then attaches.** | Confluence needs a page ID to attach to. Hence the partial-success state (FR-19). | FR-4 |
| D7 | **Exceptions are domain-typed** (`NotFoundError`, `ValidationError`, `AttachmentError`…). | Tools map type → code without inspecting text. | ERR-* |
| D8 | **Configuration precedence: App Configuration first, skipped when unset.** | Local development needs no Azure. | CFG-1, 2 |
| D9 | **Page URL host is ignored by `readPageByUrl`.** | Prevents using the server as a fetch proxy; only the ID is used. | SEC-8 |

---

## 2. Requirement → module map

| Requirement | Module(s) |
|---|---|
| FR-1…4 | `confluence_tool.py` (surface) · `ConfluenceClient.get_page_content_by_id/_title/_url`, `create_page_with_content` |
| FR-5 | `confluence_tool._register_health_check` (unregistered) |
| FR-8, FR-9 | `confluence_server.py` |
| FR-10, FR-11, FR-12 | `confluence_tool.register_tools` · `config.py` |
| FR-14, FR-15 | `html_to_plain_text`, `list_attachments`, `extract_file_content` |
| FR-16 | `get_page_content_by_*` (URL construction) · `extract_page_id_from_url` |
| FR-17 | `get_page_content_by_id` |
| FR-18 | `_resolve_context_params` |
| ERR-* | `confluence_tool.py` (4× duplicated `try/except`) → **new** `guarded` decorator + `map_confluence_error` |
| CFG-* | `config.py`, `config_reader.py` |
| NFR-1…3 | **new** `ConfluenceClient._call` wrapper (timeout, retry flag, `to_thread`) |
| NFR-6, SEC-6 | **new** `src/atlassian/services/attachments.py` |
| SEC-3, 4, 5 | **new** `src/atlassian/validation.py` |

---

## 3. Contracts and state
No database. Contracts:
- **Inbound:** MCP JSON-RPC 2.0 — `openapi.yaml` (generated from the live schemas; contract test in T-26).
- **Outbound:** Confluence Cloud REST — upstream calls per tool under `x-mcp-tools[*].upstream`.
- **State:** one in-process `Confluence` client. Safe to lose. Must be refreshable (T-16).

---

## 4. Error model (target)

```
tool function  (wrapped by @guarded)
   ├─ ValidationError           → VALIDATION_ERROR
   ├─ NotFoundError             → PAGE_NOT_FOUND
   ├─ ApiError / HTTPError(status)  → map_confluence_error(status):
   │      400 title-exists→CONFLICT · 400→VALIDATION_ERROR · 401→AUTHENTICATION_ERROR
   │      403→AUTHORIZATION_ERROR · 404→PAGE_NOT_FOUND · 409→CONFLICT
   │      429→RATE_LIMITED · 5xx→CONFLUENCE_SERVICE_ERROR
   ├─ requests.Timeout / ConnectionError → TIMEOUT / CONNECTION_ERROR
   ├─ AttachmentError / CreatePageError  → ATTACHMENT_ERROR / CREATE_PAGE_ERROR
   └─ anything else             → UNKNOWN_ERROR (logged with stack; message generic)
```
Envelope detail follows SEC-7: identifiers only. `functools.wraps` is load-bearing: FastMCP derives the tool schema from the wrapped signature.

## 5. Timeout, retry and threading model (target)

| Call | Timeout | Retry |
|---|---|---|
| Reads | connect 5 s, read 30 s (`CONFLUENCE_CONNECT_TIMEOUT`, `CONFLUENCE_READ_TIMEOUT`) | Transport failure only, ≤ `CONFLUENCE_MAX_RETRIES` (2), back-off + jitter |
| Attachment download | same, plus a streamed byte cap (NFR-6) | None |
| `createPage` and attachment upload | same | **Never** |
| Any response that arrived (4xx/5xx/429) | — | **Never** |

All library calls go through one `_call(fn, *args, retry: bool)` that runs
`asyncio.to_thread`. `retry` is a parameter of the call site, not a setting.
PDF/DOCX parsing also runs in a worker thread under a time limit (SEC-6).

---

## 6. Phased delivery

Claude stops after each phase and waits for `proceed`.

| Phase | Output | Status |
|---|---|---|
| **1 Specify** | `spec.md`, `openapi.yaml` | ✅ |
| **2 Plan** | this file | ✅ awaiting approval |
| **3 Tasks** | `tasks.md` | ✅ awaiting approval |
| **4 Implement** | code + tests, milestone by milestone | **M0 done. M1–M6 open.** |
| **5 Verify** | `REPORT.md` | ✅ baseline written; re-run each milestone |

### 6.1 Milestones

| M | Theme | Closes | Why this order |
|---|---|---|---|
| **M0** | Baseline | FR-1…4 as built | Done. |
| **M1** | **Safety** | SEC-3/4, SEC-2/7, NFR-1/2/3, NFR-5/FR-18, SEC-5 | One High finding (file exfiltration); a blocking, timeout-less client can freeze every agent; title validation makes the main read tool unusable for most titles. |
| **M2** | **Correctness** | ERR-1…3, FR-16/17/19, NFR-6, SEC-6 | Needs M1's `_call` and exceptions. Real Confluence 404s currently surface as raw errors. |
| **M3** | **Config & ops** | CFG-3…8, NFR-8 | A fresh clone, the CI pipeline and the container probe each fail or mis-point today. |
| **M4** | **Tool surface** | FR-10/11, FR-5…7, SEC-10 | Needs human answers (Q-1, Q-8); makes docs, defaults and reality agree. |
| **M5** | **Tests & CI** | NFR-7, contract test | Realistic fakes come first because they change what "passing" means. |
| **M6** | **Docs & decisions** | README, SEC-1, Q-1…9 | Needs humans. |

### 6.2 Method for every fix
1. Write the failing test that cites the requirement (`# FR-2 / AC-1`).
2. Make it pass with the smallest change in the right layer.
3. Run ruff, pytest, coverage; regenerate `openapi.yaml` if a schema changed.
4. Tick the task; put the ID in the commit.

**Test-realism rule (new):** mock at the **HTTP boundary** (`responses`), not by replacing
`atlassian.Confluence`. The library's real behaviour — `ApiError` on 404, its URL building —
is part of what the server does.

---

## 7. Risk register

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | **Arbitrary file read** via `createPage.attachment` uploads server files (secrets, mounted tokens) into Confluence. | M | **H** | T-6 first. Interim: don't expose `createPage`, or run the container with no readable secrets beyond its own env. |
| R2 | **Every caller reads every space the service account can see** (SEC-1). Higher impact than a write-only server: Confluence holds the organisation's knowledge. | M | **H** | Network isolation now; decide Q-7; consider a space allow-list (`CONFLUENCE_ALLOWED_SPACES`) as a cheap structural limit. |
| R3 | **Indirect prompt injection:** a page or PDF can carry instructions aimed at the agent. | M | M | SEC-10 (description text); size/format bounds; agent-side treatment of tool output as data. Not fully preventable here. |
| R4 | Blocking client in `async def` + no timeouts: one slow Confluence stalls all agents. | H | M | T-8. |
| R5 | `readPageByTitle` rejects most real titles; agents conclude the page doesn't exist. | H | M | T-10. |
| R6 | Raw library exceptions leak through all tools (404/403/duplicate title). | H | M | T-11. |
| R7 | Unbounded attachment inlining → huge responses, memory spikes, parser exposure (PyMuPDF/docx on untrusted bytes). | M | M | T-14. |
| R8 | CI cannot succeed (Python 3.11 vs ≥3.13); container probe/helm probe point at the wrong port. | H | M | T-16, T-17. |
| R9 | Real e-mail, tenant URL and GCP project IDs committed in Helm values. | H | L | T-19 (rotate/remove; history clean-up is a human call). |
| R10 | Docs promise tools/features that don't exist (search, upload, OAuth, rate limiting); README has merge-conflict markers. | H | L | T-20, T-28. |
| R11 | 73% coverage built on mocks that disagree with the real library: green tests, wrong behaviour. | H | M | T-24 before anything else in M5. |

---

## 8. Definition of Done (per milestone)

- [ ] Every requirement touched has ≥ 1 test citing its ID.
- [ ] Library behaviour is faked at the HTTP boundary, not by replacing `Confluence`.
- [ ] `ruff check .` clean; **no new** per-file ignores in `pyproject.toml`.
- [ ] `pytest` green; coverage not lower than before; ≥ 85% at M5.
- [ ] No `print()`; no page content, token, path or context object in logs or errors.
- [ ] `openapi.yaml` regenerated; contract test green.
- [ ] `REPORT.md` updated with real command output.
- [ ] `spec.md` TARGET → BASELINE for what shipped.
