# Confluence MCP Server — Tasks

| | |
|---|---|
| **Document** | `tasks.md` — ordered, checkable work list |
| **Owner** | Claude maintains; a human approves scope changes |
| **Source** | `spec.md` (requirements) · `plan.md` (milestones M0–M6) |
| **Rule** | Tick a box only when its **Done when** line is true *and* the evidence is in `REPORT.md`. Tests first. Fake Confluence at the **HTTP boundary** (`responses`), never by replacing `atlassian.Confluence`. |

Legend: ☑ done · ☐ open · **S/M/L** ≈ ½ day / 1–2 days / 3+ days · `[blocked: Q-n]` needs a human decision (spec §8).

---

## M0 — Baseline (as built on `feature/confluence_mcp_Phase2`)

- [x] **T-1** Scaffold: `src/atlassian/{config,servers,services,tools,utils,exceptions}`, `pyproject.toml`, `uv.lock`, `.env.example`. *(CFG-1, 2, NFR-4)*
- [x] **T-2** `ConfluenceClient`: validation helpers, cached client with smoke test, body → text, attachment text extraction, URL parsing. *(FR-14, 15, CFG-1)*
- [x] **T-3** Four tools registered with names, schemas, tags: `readPageById`, `readPageByTitle`, `readPageByUrl`, `createPage`. *(FR-1…4, 12)*
- [x] **T-4** Typed exception hierarchy + error envelopes. *(§5, D1, D7)*
- [x] **T-5** Server with stateless HTTP and `/mcp/confluence/health`; Dockerfile; GitHub Actions pipeline; 80 tests. *(FR-8, 9)*

---

## M1 — Safety  *(do first)*

- [ ] **T-6** `S` **Confine `createPage.attachment` and stop renaming it.** *(SEC-3, SEC-4 · DEF-1, DEF-2 · R1 · **High**)*
  - `CONFLUENCE_ATTACH_ROOT`: unset ⇒ parameter refused (`VALIDATION_ERROR`); set ⇒ `Path.resolve(strict=True)`, must be `is_relative_to(root.resolve())`, regular file, ≤ `CONFLUENCE_ATTACH_MAX_BYTES` (10 MB).
  - Filename = `Path(file).name` (remove `custom_filename = 'file1.pdf'`).
  - Tests first: `/etc/passwd`, `root/../../etc/passwd`, symlink escape, directory, oversize, valid file ⇒ uploaded as its own name. **AC-3, AC-4**
  - **Done when:** the five refusals cause zero upload calls and the valid case asserts the real filename.

- [ ] **T-7** `S` **Sanitise errors and prove no secrets leak.** *(SEC-2, SEC-7 · DEF-19)*
  - `error_details`: only `page_id` / `space_key`. Remove `title`, `page_title`, `attachment`, `file_path` echoes.
  - Library exception text goes to the log; the envelope carries a sanitised Confluence message.
  - Tests: a library error containing `Authorization: Basic …` and a file path never appears in the envelope; a grep-style test that `CONFLUENCE_API_TOKEN` is never formatted into a log or exception.

- [ ] **T-8** `M` **Timeouts, read-only retry, off the event loop.** *(NFR-1, 2, 3 · DEF-9 · R4)*
  - One `ConfluenceClient._call(fn, *args, retry: bool)`; `asyncio.to_thread`; timeouts `CONFLUENCE_CONNECT_TIMEOUT` (5) / `CONFLUENCE_READ_TIMEOUT` (30) passed to the library; `CONFLUENCE_MAX_RETRIES` (2).
  - Reads `retry=True`; `createPage`/upload `retry=False`, no override.
  - Tests: GET timeout×2 then 200 ⇒ success. `createPage` timeout ⇒ **exactly 1** POST. 503 ⇒ 1 call. Two concurrent tools while one call sleeps 3 s ⇒ the other finishes first. **AC-9, AC-10**
  - Remove `ASYNC230` from the ruff ignore list when done.

- [ ] **T-9** `S` **Delete the 17 `print()` calls and the context override.** *(NFR-5, FR-18 · DEF-8)*
  - Remove `_resolve_context_params` entirely (arguments are what the caller sent), or reduce to an explicit, documented allow-list if a human asks for it. Today it prints `dir(ctx)` and `ctx.__dict__` and lets context replace `space_key`/`page_title`.
  - Delete the four `_resolve_context_params` tests (two of them assert the override as a feature).
  - Add a static guard test: no `print(` under `src/`. **AC-7, AC-13**

- [ ] **T-10** `M` **Validation that accepts real Confluence identifiers.** *(SEC-5 · DEF-3 · R5)*
  - New `src/atlassian/validation.py`: page id `^[0-9]{1,20}$`; space key `^(~[A-Za-z0-9:._-]+|[A-Za-z0-9]{1,255})$` (no whitespace); title non-blank, ≤ 255, no control characters.
  - Apply the same title rule to `createPage` (today it is checked differently from reads).
  - Tests, parametrised: `Release Notes v2.1`, `Q3 Plan: Budget`, `Design (draft)`, `R&D Overview`, `Café menu`, `Meeting - 2024.05.01` accepted; `~5b10…` accepted; `MY SPACE`, `../x`, empty, 10 000 chars, `\x00` refused. Replace `test_validate_page_title_invalid`/`valid`. **AC-1**

---

## M2 — Correctness

- [ ] **T-11** `M` **One error contract; real library errors mapped.** *(ERR-1…4 · DEF-6 · R6)*
  - `guarded` decorator + `map_confluence_error(status, message)` per plan §4, applied to all four tools; add the new codes to the enum in `openapi.yaml`.
  - Tests use `responses`: 404 ⇒ `PAGE_NOT_FOUND`, 401, 403, 429, 500, timeout, duplicate-title 400 ⇒ `CONFLICT`. Remove the `get_page_by_id.return_value = None` mocks, which the real library never produces. **AC-2, AC-15**
  - **Done when:** no tool can raise a non-envelope exception (a test injects `RuntimeError` and expects `UNKNOWN_ERROR`).

- [ ] **T-12** `S` **Honour `space_key` in `readPageById`.** *(FR-17 · DEF-7 · Q-5)* Compare the page's `space.key` (expand `space`) with the argument; mismatch ⇒ `PAGE_NOT_FOUND`. **AC-5**
- [ ] **T-13** `S` **Return a URL that works.** *(FR-16 · DEF-11)* Build from the response's `_links.base` + `_links.webui`; test that the result parses through `extract_page_id_from_url` to the same ID. **AC-6** *(Verify the real shape against a live site once — the one place this plan needs it.)*
- [ ] **T-14** `L` **Bound attachment inlining.** *(NFR-6, SEC-6 · DEF-10 · R7)* New `services/attachments.py`: ≤ 5 attachments, stream with a byte cap, extraction under a time limit in a worker thread, character cap per attachment and per response, `truncated` flag, `include_attachments` argument (Q-6). Stop swallowing errors with `except Exception: pass`. Tests: 12 attachments, one oversize, one corrupt PDF, one slow parse. **AC-11**
- [ ] **T-15** `S` **`createPage` partial-success status and `CONFLICT`.** *(FR-19, FR-4 · AC-14, AC-15)* Add `status: created|created_with_errors`; result message says the page exists when an attachment fails.

---

## M3 — Config & ops

- [ ] **T-16** `M` **One set of variable names; fail fast; refreshable client.** *(CFG-3…7 · DEF-5, 12, 18)*
  - Define `ENABLED_CONFLUENCE_TOOLS` in `config.py` (comma-separated; blank ⇒ unset).
  - Align code, `.env.example` (`CONFLUENCE_EMAIL`, `CONFLUENCE_PORT`, not `PORT`/`CONFLUENCE_USERNAME`), Dockerfile, README, `values-*.yaml`.
  - Cloud auth = email + token only; delete the username branch and the unreachable OAuth branch (Q-3). Normalise the URL; require `/wiki` on `atlassian.net`.
  - Startup validation naming the variable; blank = unset; `reset()` called on 401 so a rotated token works without a restart.
  - Tests: **AC-8**, **AC-12**.
- [ ] **T-17** `S` **Reproducible build, correct probes.** *(NFR-8, CFG-7 · DEF-13 · R8)*
  - CI `python-version: "3.13"`; Docker `uv sync --frozen --no-dev`; delete `requirements.txt` (pins `fastmcp==1.0`, lock has 2.12.2, file starts with a BOM).
  - Dockerfile `CMD`/`EXPOSE`/`HEALTHCHECK` from `CONFLUENCE_PORT`; the health check requests `/mcp/confluence/health`, not a bare TCP connect.
  - **Done when:** `uv sync --locked` passes on the CI interpreter and the container becomes healthy on a non-default port.
- [ ] **T-18** `S` **Remove dead code and noise.** *(DEF-17)* Unused `MCPResponse`/`PageData`/`CreatePageData`; uninstalled shutdown/signal handlers; the `stateless_http` constructor deprecation (pass it to `http_app`/`run`); UTF-8 BOMs in three files.
- [ ] **T-19** `S` **Deployment assets and committed identifiers.** `[blocked: Q-4]` *(CFG-8 · DEF-14, 15 · R9)* Mark or delete the non-authoritative path (`Dockerfile.mcp-https` points at a file that doesn't exist; `cloudbuild.yaml` and Helm hard-code GCP project/service-account IDs). Remove the real e-mail and tenant URL from `values-dev.yaml`; align `containerPort`/probe with `CONFLUENCE_PORT`. A human decides whether git history must be rewritten and whether the exposed e-mail/tenant need action.

---

## M4 — Tool surface

- [ ] **T-20** `S` **Make the default set honest.** *(FR-10, 11, 12, SEC-10 · DEF-4 · R10)* Default list = the registered tools, derived from the registry dict (single source). Remove `searchPages`/`uploadAttachment` from defaults and README unless T-21/22 land. Add the SEC-10 "untrusted content" sentence to each read tool's description. Test: `tools/list` names == `x-mcp-tools` names.
- [ ] **T-21** `M` **`confluence-searchPages`** `[blocked: Q-1]` *(FR-6)* Server-built, escaped CQL; `limit` ≤ 50. Test CQL escaping (`"`, `\`, operators).
- [ ] **T-22** `M` **`confluence-uploadAttachment`** `[blocked: Q-1]` *(FR-7)* Prefer `content_base64`; `file_path` only under SEC-3.
- [ ] **T-23** `S` **Register or delete `confluence-health`** `[blocked: Q-8]` *(FR-5)*

---

## M5 — Tests & CI

- [ ] **T-24** `L` **Replace mock-the-library tests with HTTP-boundary tests.** *(NFR-7 · R11)* Add `responses`; cover: 404/403/401/duplicate title, real `get_page_by_title` empty result, page with attachments (PDF/DOCX/TXT/unsupported/corrupt), `createPage` with and without attachment, URL formats, `readPageByUrl` without a space in the URL. Remove tests that pin wrong behaviour (`validate_page_title` rejecting `.`/`:`; context overrides).
- [ ] **T-25** `S` **Coverage gate.** `--cov-fail-under=85` in CI; cover `config_reader.py` (20–37), `log_helper.py` (53–55). Never lower it to get green.
- [ ] **T-26** `M` **Contract test.** Commit `scripts/gen_openapi.py`; a test regenerates in memory and fails on drift; another validates with `openapi-spec-validator`.
- [ ] **T-27** `S` **CI hardening.** Run on `pull_request` (CI job only); pin `trufflehog` and `trivy-action` to a release/SHA; review the per-file `ruff` ignores (`BLE001`, `S110`, `F841`, `ASYNC230`, `RUF013`) and remove each one that no longer applies; stop shipping the test runner's ignore list as policy.

---

## M6 — Docs & decisions  `[needs a human]`

- [ ] **T-28** `S` **Rewrite `README.md`.** It currently contains unresolved git merge-conflict markers, describes files that don't exist (`conftest.py`, `test_confluence_client.py`, `run_tests.py`), claims 1,200+ tests (actual: 80), documents `SECRET_KEY`/CORS/rate-limiting/OAuth that the code doesn't have, and gives the health route as `/health`. Replace with: layout, run locally, tool table, config precedence, security note, Docker, links to these documents. *(DEF-16)*
- [ ] **T-29** `S` **Decide and record** Q-1…Q-9 and **SEC-1** (Q-7); flip statuses in `spec.md`.

---

## Dependency order

```
T-8 ─┬─> T-11 ─┬─> T-12, T-13, T-15
     │         └─> T-24 ─> T-25 ─> T-27
T-10 ┘
T-6, T-7, T-9, T-10  (independent; do first)
T-14 after T-8        T-16 ─> T-17 ─> T-19        T-20 after T-16
T-26 after T-11 and T-20      T-28, T-29 last
```

## Progress

| Milestone | Tasks | Done |
|---|---|---|
| M0 Baseline | T-1…5 | **5 / 5** |
| M1 Safety | T-6, 7, 8, 9, 10 | 0 / 5 |
| M2 Correctness | T-11…15 | 0 / 5 |
| M3 Config & ops | T-16…19 | 0 / 4 |
| M4 Tool surface | T-20…23 | 0 / 4 |
| M5 Tests & CI | T-24…27 | 0 / 4 |
| M6 Docs & decisions | T-28, 29 | 0 / 2 |
| **Total** | **29** | **5 / 29** |
