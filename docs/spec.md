# Confluence MCP Server — Specification

| | |
|---|---|
| **Document** | `spec.md` — source of truth for requirements |
| **Owner** | Human (engineering + product). Claude proposes edits; a human approves them. |
| **Status** | v1.0 — baseline captured from branch `feature/confluence_mcp_Phase2`, plus a hardening target |
| **Companions** | `openapi.yaml` (contract) · `plan.md` (architecture) · `tasks.md` (work) · `REPORT.md` (verification) · `CLAUDE.md` (standing orders) |

> **How to read this spec.** The server already exists. This spec was written
> *from* the code, its tests and the running server, then extended with what
> production needs that the code does not yet do. Every requirement carries a **Status**:
>
> - **BASELINE** — implemented today.
> - **TARGET** — required, not yet implemented. Each has a task in `tasks.md`.
> - **DECISION** — cannot be written until a human answers a question in §8.
>
> Requirement IDs are permanent. Commits, tests and PRs cite them (`FR-4`,
> `SEC-3`). Never renumber; retire an ID by marking it `WITHDRAWN`.
>
> **Important:** what the repository *says* it does (README, default tool list)
> and what the server *does* differ. This spec follows the running server.
> `REPORT.md` §3 lists every difference.

---

## 1. Purpose and scope

### 1.1 What this is
An **MCP (Model Context Protocol) server** that lets an AI agent read and create
**Confluence Cloud** pages over streamable HTTP. It is an adapter: it translates a tool call into Confluence
REST calls (through the `atlassian-python-api` library) and returns structured
results. Confluence remains the single source of truth for pages, spaces,
permissions and versions.

```
MCP client (agent)
   |  streamable HTTP (stateless)   POST /mcp/confluence
   v
confluence_server.py -> confluence_tool.py -> ConfluenceClient -> atlassian.Confluence (requests)
                                                                      |  HTTPS, Basic auth
                                                                      v
                                                          Confluence Cloud  /wiki/rest/api/*
```

### 1.2 In scope
- The tools in §4, their inputs, outputs and failure behaviour.
- Configuration, logging, health route, container image, CI.
- Reading text out of page attachments (PDF, DOCX, TXT) for the agent.

### 1.3 Out of scope
- **Not a second Confluence.** No permission, versioning, macro or space rules are re-implemented. If a rule seems missing, it is in Confluence.
- Page **update**, **delete**, **move**, comments, labels, search by CQL (unless Q-1 adds search), whiteboards, databases.
- Confluence Server / Data Center — unless Q-3 says otherwise; today the code has an untested branch for it.
- Caller authentication (SEC-1; unresolved).
- Deployment infrastructure in `terraform-app-provision/`, `cloudbuild.yaml`, `Dockerfile.mcp-https` — present in the repository, **not described by this spec** (see DEF-14; Q-4 asks which is authoritative).

### 1.4 Actors
| Actor | Needs |
|---|---|
| **Agent** (LLM via an MCP client) | Predictable tool names, schemas and error codes it can act on; bounded response sizes. |
| **Operator** | One image for every environment; configuration only; health and logs; correct ports. |
| **Confluence admin** | One service account whose reach bounds everything the server can do. |
| **Reviewer / auditor** | Trace any line of code to a requirement ID. |

---

## 2. Glossary
| Term | Meaning |
|---|---|
| **Space key** | Short identifier of a space, e.g. `ENG`. Personal spaces use `~<accountId>`. |
| **Page ID** | Numeric identifier, e.g. `123456`. |
| **Storage format** | Confluence's XHTML-based native body format. |
| **Representation** | The format a body is submitted in: `storage`, `wiki` or `view`. |
| **Envelope (error)** | The result object `{error_code, error_message, error_details}` a tool returns instead of raising. |

---

## 3. Global requirements

### 3.1 Transport and surface
| ID | Requirement | Status |
|---|---|---|
| **FR-8** | MCP endpoint is `POST /mcp/confluence`, streamable HTTP, **stateless** (no session or `initialize` handshake state kept between requests). | BASELINE |
| **FR-9** | `GET /mcp/confluence/health` returns `200 {"status":"healthy","service":"confluence-mcp-server"}`. It does **not** call Confluence (liveness only). | BASELINE — `test_server.py` |
| **FR-10** | The tool set is **exactly** what `spec.md` §4 lists as registered. The default registration list, the README and the tool descriptions must name the same set. | **TARGET** — default list names 6 tools, 2 do not exist, 1 existing tool is omitted (DEF-4) |
| **FR-11** | `ENABLED_CONFLUENCE_TOOLS` (comma-separated tool names) restricts the registered set; empty/unset ⇒ the full default set; an unknown name is logged and skipped. | **TARGET** — the code reads `config.ENABLED_CONFLUENCE_TOOLS` but `config.py` never defines it, so it cannot be set (DEF-5) |
| **FR-12** | Every tool carries tags `confluence` plus `read` or `write`. | BASELINE |

### 3.2 Behaviour shared by all tools
| ID | Requirement | Status |
|---|---|---|
| **FR-13** | **Results are structured objects** (not JSON strings). Success returns the documented fields; failure returns the **envelope** (§5). | BASELINE |
| **FR-14** | **Page bodies are returned as plain text** produced from the page's storage (else view, else export_view) format: `<script>`/`<style>` removed, tags stripped, blank lines collapsed. Structure (tables, macros, links) is lost. | BASELINE — the loss of structure is accepted until Q-2 is answered |
| **FR-15** | A read tool returns the page's attachments' **extracted text** inline (PDF, DOCX, TXT; others reported "Unsupported file type"). A per-attachment failure is reported inside that attachment's entry and never fails the read. | BASELINE (unbounded — see NFR-6) |
| **FR-16** | The `url` field is a link a human can open **and** that `confluence-readPageByUrl` accepts back. | **TARGET** — today `{base}/pages/{id}`, which neither (DEF-11) |
| **FR-17** | A page-scoped read given a `space_key` honours it: if the page is not in that space the call fails with `NOT_FOUND` (or the parameter is removed — Q-5). | **TARGET** — `space_key` is validated then ignored by `readPageById` (DEF-7) |
| **FR-18** | **Nothing in the request context silently overrides an argument the caller supplied.** | **TARGET** — `readPageByTitle` lets context attributes replace `space_key`/`page_title` (DEF-8) |
| **FR-19** | `createPage` reports partial success explicitly: `status` is `created` or `created_with_errors`; the page exists in both cases. | **TARGET** — success-shaped result today, status only per attachment |

### 3.3 Configuration
| ID | Requirement | Status |
|---|---|---|
| **CFG-1** | Precedence, highest first: **Azure App Configuration → OS env / `.env` → default**. | BASELINE |
| **CFG-2** | `AZURE_APPCONFIG_ENDPOINT` unset ⇒ App Configuration skipped entirely (no Azure call, no credential). Set ⇒ keys `"<APP_NAME>:*"` with label `<ENVIRONMENT>` are loaded, prefix trimmed. Defaults `APP_NAME=confluence-mcp`, `ENVIRONMENT=dev`. | BASELINE (loader untested — T-25) |
| **CFG-3** | **One documented set of variable names**, identical in code, `.env.example`, Dockerfile, README and deployment values: `CONFLUENCE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_PORT`, `LOG_LEVEL`, `ENABLED_CONFLUENCE_TOOLS`. | **TARGET** — `.env.example` ships `PORT` and `CONFLUENCE_USERNAME`; code reads `CONFLUENCE_PORT` and prefers `CONFLUENCE_EMAIL` (DEF-12) |
| **CFG-4** | **Authentication.** Confluence Cloud: email + API token (HTTP Basic), `cloud=True`. Any other combination is an error, not a silent fallback to another mode. The OAuth branch is removed unless Q-3 asks for it (no setting exists to drive it today). | **TARGET** (DEF-12, DEF-17) |
| **CFG-5** | `CONFLUENCE_URL` is the Cloud site **including** `/wiki`, normalised once (no trailing slash). A value missing `/wiki` on an `atlassian.net` host is rejected with a message saying so. | **TARGET** |
| **CFG-6** | **Fail fast:** missing/invalid `CONFLUENCE_URL`, `CONFLUENCE_EMAIL` or `CONFLUENCE_API_TOKEN` stops startup naming the variable. A **blank** value is treated as unset. | **TARGET** — today discovered on the first tool call (DEF-18) |
| **CFG-7** | The container listens on `CONFLUENCE_PORT` (default 9001). The Dockerfile `CMD`, `EXPOSE`, `HEALTHCHECK` and any orchestrator probe use that one value. | **TARGET** (DEF-12) |
| **CFG-8** | Nothing environment-specific, and no personal identifier, is committed to the repository. | **TARGET** (DEF-15) |

### 3.4 Non-functional
| ID | Requirement | Status |
|---|---|---|
| **NFR-1** | Every outbound Confluence call has connect and read timeouts. | **TARGET** — none (DEF-9) |
| **NFR-2** | Reads retry on connection failure/timeout only (bounded, back-off). **Writes (`createPage`) never retry**; a response that reached Confluence is never retried. Structural, not configurable — a retried `createPage` is a duplicate page. | **TARGET** |
| **NFR-3** | Blocking library calls run off the event loop (`asyncio.to_thread`), so one slow Confluence call does not stall every other agent. | **TARGET** — `async def` tools call a synchronous client directly (DEF-9) |
| **NFR-4** | Logs are UTC, `LOG_LEVEL`-controlled. | BASELINE — `log_helper.py` |
| **NFR-5** | All diagnostics use `logging`. **No `print()` in `src/`.** Page bodies, titles, attachment text and context objects are never logged at INFO or printed. | **TARGET** — 17 `print()` calls (DEF-8) |
| **NFR-6** | A read response is bounded: max attachments inspected (default 5), max bytes per attachment (default 5 MB), max characters of extracted text per attachment and per response; truncation is flagged (`truncated: true`). Attachment extraction is **opt-in** (`include_attachments`, default `true` to preserve behaviour — see Q-6). | **TARGET** (DEF-10) |
| **NFR-7** | Line coverage ≥ **85%**, every tool and public service method exercised, enforced in CI. | **TARGET** — 73% |
| **NFR-8** | Builds are reproducible: CI and Docker use the lockfile (`--locked`/`--frozen`) on the Python version `pyproject.toml` requires. One dependency manifest (`uv.lock`); no stale `requirements.txt`. | **TARGET** — CI is configured for a Python the project forbids (DEF-13) |

### 3.5 Security
| ID | Requirement | Status |
|---|---|---|
| **SEC-1** | **Caller authentication — unresolved.** The server holds one service-account credential; anyone who can reach `/mcp/confluence` acts with its rights (read every space it can see, create pages anywhere it may). Until decided (Q-7) it **must not** be internet-reachable. | UNRESOLVED |
| **SEC-2** | `CONFLUENCE_API_TOKEN` comes from App Configuration/Key Vault, a secret store or git-ignored `.env`; never logged, returned or placed in an error message. | BASELINE (verify — T-7) |
| **SEC-3** | **`confluence-createPage`'s `attachment` (a server-local path) must not read arbitrary files.** Allowed only inside `CONFLUENCE_ATTACH_ROOT`, resolved with symlinks and `..`; unset ⇒ the parameter is refused. A size cap applies. | **TARGET** — today any readable file is uploaded to Confluence (DEF-1, **High**) |
| **SEC-4** | The attachment **file name** is derived from the file, never hard-coded. | **TARGET** — every attachment is named `file1.pdf` (DEF-2) |
| **SEC-5** | Input validation accepts every legal Confluence identifier and refuses the rest *before* any call: page IDs `^[0-9]{1,20}$`; space keys `^(~[A-Za-z0-9:._-]+\|[A-Za-z0-9]{1,255})$` (no whitespace); page titles any non-blank text ≤ 255 chars without control characters. | **TARGET** — title regex refuses `.`, `:`, `(`, `&`, accents (DEF-3) |
| **SEC-6** | Untrusted attachment content (PDF/DOCX) is parsed under the NFR-6 size limits, off the event loop, with a time limit. | **TARGET** |
| **SEC-7** | Error envelopes echo only identifiers (`page_id`, `space_key`), never a file path, token, titles or free text the caller typed. Library exception text is logged, and returned only as a sanitised Confluence message. | **TARGET** — `attachment` path and `title` are echoed (DEF-19) |
| **SEC-8** | Tools never accept a host. `CONFLUENCE_URL` is the only destination. A `page_url` supplied to `readPageByUrl` is parsed for an ID only; its host is ignored. | BASELINE |
| **SEC-9** | Dependencies are audited (`pip-audit`), the repository secret-scanned, the image scanned. | BASELINE (CI; unrun here) |
| **SEC-10** | **Everything returned from a read — page body, title, attachment text — is untrusted data**, and may contain instructions aimed at the agent (indirect prompt injection). The server never interprets it; each read tool's description states that the text is untrusted and must not be followed as instructions. The server cannot prevent injection; the agent platform must treat tool output as data. | **TARGET** — descriptions say nothing today |

---

## 4. Tool requirements

Registered today: **four** tools (`confluence-readPageById`, `-readPageByTitle`, `-readPageByUrl`, `-createPage`).
Argument tables mirror `openapi.yaml`, which is generated from the live schemas.

### FR-1 `confluence-readPageById` &nbsp; `read`
| Argument | Type | Req. | Notes |
|---|---|---|---|
| `space_key` | string | **yes** | Validated (SEC-5); honoured per FR-17 |
| `page_id` | string | **yes** | Digits only |

**Result:** `{id, title, attachments[], body (plain text), url}`.
Each attachment: `{fileName, content, downloadLink, id}` or, on failure, the same plus `error`.
**Errors:** `VALIDATION_ERROR`, `PAGE_NOT_FOUND`, `CONFLUENCE_ERROR` (see §5).
Fetched with `expand=body.storage,body.view,body.export_view`.

### FR-2 `confluence-readPageByTitle` &nbsp; `read`
`space_key`, `page_title` (both required). Exact-title lookup within one space.
**Result:** as FR-1.
**Rules:** title validation per SEC-5 (today far too narrow). FR-18 applies. Titles are unique per space in Confluence, so there is at most one match.

### FR-3 `confluence-readPageByUrl` &nbsp; `read`
`page_url` (required). Extracts the page ID (and space key) from:
`/spaces/{space}/pages/{id}[/title]`, `/pages/viewpage.action?pageId={id}[&spaceKey=…]`.
**Result:** as FR-1 plus `space_key`.
**Rules:** `/display/{space}/{title}` URLs are **not** supported (the extractor recognises them but the tool then refuses); the error must say so and name the supported forms. The URL's host is ignored (SEC-8). If the space is absent from the URL it is fetched from the page.

### FR-4 `confluence-createPage` &nbsp; `write`
| Argument | Type | Req. | Notes |
|---|---|---|---|
| `space_key` | string | **yes** | SEC-5 |
| `title` | string | **yes** | Non-blank; trimmed |
| `body` | string | **yes** | In `representation` |
| `attachment` | string \| null | no | **Server-local path.** SEC-3 |
| `representation` | `storage`\|`wiki`\|`view` | no (`storage`) | Anything else ⇒ `VALIDATION_ERROR` |

**Result:** `{id, title, url, space_key, attached_files:[{file_path, filename, status, attachment_id|error}]}` plus FR-19's `status`.
**Rules:**
- The page is created **first**; the attachment is attempted afterwards. If the attachment fails the page still exists (FR-19) and the agent must be told so in plain words.
- A duplicate title in the space is a `CONFLICT`, not a generic error.
- Created page is **not** deduplicated or retried (NFR-2).
- *Today* the attachment is uploaded under the name `file1.pdf` (SEC-4).

### FR-5 `confluence-health` &nbsp; `read` &nbsp; **DECISION (Q-8)**
Implemented, **not registered by default**. Checks the live Confluence connection (`get_all_spaces`) and returns `{status, service, confluence_url, spaces_accessible, timestamp}`. Distinct from the HTTP route (FR-9) which never calls Confluence.
Decision: register as a readiness tool, or delete. Default if unanswered: register only when listed in `ENABLED_CONFLUENCE_TOOLS`.

### FR-6 `confluence-searchPages` &nbsp; **DECISION (Q-1)**
Advertised in the README and the default registration list; **does not exist**.
If wanted: `query` (text, required), `space_key` (optional), `limit` (default 10, max 50); returns `{results:[{id,title,space_key,url,excerpt}], total}`. Implemented with Confluence CQL built **by the server** from escaped inputs — the agent never supplies raw CQL. Otherwise delete every mention.

### FR-7 `confluence-uploadAttachment` &nbsp; **DECISION (Q-1)**
Advertised; **does not exist**. If wanted: `page_id` + exactly one of `content_base64`+`filename` (preferred) or `file_path` (SEC-3). Otherwise delete every mention.

---

## 5. Error contract

Every failure is returned as the **envelope** (an object, not a raised error) so
agents get a code they can branch on:

```json
{"error_code": "PAGE_NOT_FOUND",
 "error_message": "Page id 999 not found",
 "error_details": {"page_id": "999", "space_key": "ENG"}}
```

| ID | Requirement | Status |
|---|---|---|
| **ERR-1** | **No failure escapes as a raw exception.** Today only `ConfluenceError` subclasses are caught; the library's own `ApiError`/`HTTPError`/`requests` exceptions pass through all four tools. | **TARGET** (DEF-6) |
| **ERR-2** | Codes: existing — `PAGE_NOT_FOUND`, `VALIDATION_ERROR`, `CREATE_PAGE_ERROR`, `ATTACHMENT_ERROR`, `CONFLUENCE_ERROR`, `HEALTH_CHECK_ERROR`, `UNKNOWN_ERROR`; to add — `AUTHENTICATION_ERROR`, `AUTHORIZATION_ERROR`, `CONFLICT`, `RATE_LIMITED`, `TIMEOUT`, `CONNECTION_ERROR`, `CONFLUENCE_SERVICE_ERROR`. Existing codes keep their spelling (compatibility). | **TARGET** |
| **ERR-3** | HTTP mapping from Confluence: 400→`VALIDATION_ERROR` (title-exists→`CONFLICT`), 401→`AUTHENTICATION_ERROR`, 403→`AUTHORIZATION_ERROR`, 404→`PAGE_NOT_FOUND`, 409→`CONFLICT`, 429→`RATE_LIMITED`, 5xx→`CONFLUENCE_SERVICE_ERROR`. | **TARGET** |
| **ERR-4** | `error_details` follows SEC-7. | **TARGET** |

Note: the envelope is a normal MCP result (`isError=false`). That is the
current contract and is kept; clients must read `error_code`. Aligning with the
Jira server's raised-`ToolError` style is Q-9.

---

## 6. Acceptance criteria (Given / When / Then)

**AC-1 (FR-2, SEC-5)** Given a page titled `Release Notes v2.1`, when `readPageByTitle` is called with that title, then the page is returned (today: `VALIDATION_ERROR`).
**AC-2 (ERR-1, DEF-6)** Given Confluence answers 404 (the real library raises `ApiError`), when `readPageById` is called, then the result is `PAGE_NOT_FOUND`, not an exception.
**AC-3 (SEC-3)** Given `CONFLUENCE_ATTACH_ROOT=/data/attach`, when `createPage` is called with `attachment=/etc/passwd` or `/data/attach/../../etc/passwd`, then the file is **not** uploaded and `ATTACHMENT_ERROR`/`VALIDATION_ERROR` is returned; the page's disposition follows FR-19.
**AC-4 (SEC-4)** Given a valid attachment `report.docx`, when uploaded, then Confluence receives the name `report.docx`.
**AC-5 (FR-17)** Given page 9 is in space `ENG`, when `readPageById(space_key="OPS", page_id="9")` is called, then `PAGE_NOT_FOUND`.
**AC-6 (FR-16)** Given a page is read, then its `url` parses through `readPageByUrl` to the same page ID.
**AC-7 (FR-18)** Given a request context carrying `confluence_space_key="OTHER"`, when `readPageByTitle(space_key="ENG", …)` is called, then `ENG` is used.
**AC-8 (FR-10/11)** Given `ENABLED_CONFLUENCE_TOOLS=confluence-readPageById,bogus`, then exactly one tool is registered and a warning names `bogus`; with the variable unset the registered set equals the documented set.
**AC-9 (NFR-3)** Given a Confluence call that takes 5 s, when two other tools are called concurrently, then they complete without waiting.
**AC-10 (NFR-1/2)** Given a `GET` times out twice then succeeds, then it succeeds; given `createPage` times out, then **exactly one** POST was made.
**AC-11 (NFR-6)** Given a page with 12 attachments of 50 MB, when read, then ≤ 5 are inspected, none above the byte cap is downloaded fully, and `truncated:true` is set.
**AC-12 (CFG-3/6/7)** Given `.env.example` copied unchanged, when the server starts, then it starts (or names the missing variable) and listens on `CONFLUENCE_PORT`; the image `HEALTHCHECK` targets that port.
**AC-13 (NFR-5)** Given a page body containing a marker string, when any read runs at `LOG_LEVEL=DEBUG`, then the marker is in no log line or stdout.
**AC-14 (FR-19)** Given the attachment fails after the page is created, then `status="created_with_errors"`, `id` is present, and the message says the page exists.
**AC-15 (FR-4)** Given a title that already exists in the space, then `CONFLICT`.

---

## 7. Traceability
`REPORT.md` §3 maps every requirement to code and test. A requirement with no test is a finding, not a pass.
Commits use Conventional Commits with the ID: `fix(sec): confine attachment paths (SEC-3)`.

---

## 8. Open questions (human decisions)

| ID | Question | Default if unanswered |
|---|---|---|
| **Q-1** | Implement `searchPages` and `uploadAttachment` (FR-6, FR-7), or remove every mention? | Remove mentions now; add later as a new, specified tool. |
| **Q-2** | Should a read be able to return richer content (`format = plain \| storage \| markdown`), given FR-14 drops tables, macros and links? | Add `format`, default `plain` (no behaviour change). |
| **Q-3** | Is Confluence Server/Data Center in scope (the `cloud=False` and OAuth branches)? | No — remove both (CFG-4). |
| **Q-4** | Which deployment path is authoritative: Azure Container Apps (the CI workflow) or GKE (Helm/Terraform/`cloudbuild.yaml`)? | CI workflow; mark the rest legacy. |
| **Q-5** | Keep `space_key` on `readPageById` (and enforce it) or remove the parameter? | Keep and enforce (FR-17); no schema change. |
| **Q-6** | Should attachment extraction be on by default for reads? | On, bounded (NFR-6), with `include_attachments=false` to skip. |
| **Q-7** | SEC-1: how does caller identity reach Confluence — network isolation, gateway authoriser, per-user tokens? | Network-only; document as accepted risk. |
| **Q-8** | Register `confluence-health` (FR-5)? | Only when explicitly enabled. |
| **Q-9** | Align the error style with the Jira server (raised tool errors) or keep envelopes? | Keep envelopes; share the *code names*. |
