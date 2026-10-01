# POC_Cloudcruise

Python + SQLite POC that fires CloudCruise autofill workflows from a small
practitioner directory.

## What it does

1. **Workflow Mappings tab** — pair a *target URL* (the site you want CloudCruise
   to fill) with a CloudCruise `workflow_id`.
2. **Practitioners tab** — 10 records per page. Each row has an
   *Autofill → CloudCruise* button.
3. Clicking Autofill prompts for the target URL. The backend:
   - looks up the `workflow_id` from the mapping table for that URL,
   - `GET /workflows/{workflow_id}/metadata` to pull the input schema,
   - matches the schema keys against the practitioner columns (they share
     names, so this is dynamic — new fields work with no code change),
   - `POST /run` with `run_input_variables` built from the practitioner,
   - persists an `autofill_sessions` row with status + CloudCruise session id/url.
4. **Sessions tab** — history of every attempt with success/failure status.

The CloudCruise `cc-key` is only read in `backend/cloudcruise.py` from the
`CC_KEY` env var (loaded from `.env`). It never reaches the browser.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (via `httpx` for CloudCruise calls)
- **Frontend:** static HTML + vanilla JS served by FastAPI (no build step)
- **Storage:** `poc_cloudcruise.db` (created on first run)

## Setup

```bash
# 1. Create a virtualenv (Windows / Git Bash)
python -m venv .venv
source .venv/Scripts/activate    # or .venv\Scripts\activate.bat in cmd

# 2. Install deps
pip install -r requirements.txt

# 3. Configure the CloudCruise key
cp .env.example .env
# then edit .env and set CC_KEY=sk_...

# 4. Seed demo data (25 practitioners + 1 workflow mapping)
python -m backend.seed

# 5. Run the app
python run.py
```

Open <http://localhost:8000>.

## Environment variables

| var          | default                          | notes                                        |
|--------------|----------------------------------|----------------------------------------------|
| `CC_KEY`     | (empty)                          | CloudCruise secret. Required for live calls. |
| `CC_BASE_URL`| `https://api.cloudcruise.com`    |                                              |
| `CC_DRY_RUN` | `true`                           | Forwarded as `dry_run.enabled` on `/run`.    |
| `DATABASE_URL`| `sqlite:///./poc_cloudcruise.db`|                                              |

## API surface

| Method | Path                              | Purpose                                   |
|--------|-----------------------------------|-------------------------------------------|
| GET    | `/api/mappings`                   | List workflow ↔ URL mappings              |
| POST   | `/api/mappings`                   | Create a mapping                          |
| PUT    | `/api/mappings/{id}`              | Update a mapping                          |
| DELETE | `/api/mappings/{id}`              | Delete a mapping                          |
| GET    | `/api/practitioners?page=&page_size=` | Paginated list (10/page)              |
| GET    | `/api/practitioners/{id}`         | Full practitioner record                  |
| POST   | `/api/autofill`                   | `{practitioner_id, target_url}` → runs it |
| GET    | `/api/sessions`                   | Autofill session history                  |

Swagger docs live at `/docs`.

## How the dynamic mapping works

CloudCruise workflows expose an `input_schema` (JSON-Schema-style) via
`/workflows/{id}/metadata`. The keys of `input_schema.properties` are the
contract. Our `practitioners` table's column names are chosen to match those
keys 1:1, so `backend/mapper.py` builds `run_input_variables` by walking the
schema properties and pulling matching values off the practitioner row.

- Values are coerced to the schema's declared `type` (string / int / bool).
- If a `required` field is empty on the practitioner, the run is not attempted
  and the session is recorded as `failed` with the missing fields listed.
- New workflows with different fields work without code changes — extend the
  `practitioners` table (or replace it with a JSON column) and the mapper picks
  the new keys up automatically.

## Roadmap — Prompt Registry & Versioning

Today a mapping row is `(target_url → workflow_id)`. The `workflow_id` was
produced in CloudCruise's UI by pasting a natural-language *prompt* into their
authoring panel — that prompt is the real source of truth, but it lives outside
this repo, so onboarding a new URL is a manual tribal-knowledge exercise and we
can't reliably re-generate a workflow if CloudCruise's runtime changes.

Goal: treat **prompt + input schema** as the versioned source of truth, and
treat `workflow_id` as a **build artifact** produced by compiling a specific
prompt+schema pair. The mapping table then answers *"what artifact should we
run for this URL right now?"*.

### Data model changes

Add two tables and one FK:

**`prompt_templates`** — the human-authored spec for a target site.

| column                | notes                                                          |
|-----------------------|----------------------------------------------------------------|
| `id`                  | PK                                                             |
| `name`                | e.g. "KY Medicaid Provider Enrollment"                         |
| `slug`                | stable identifier used across versions (`ky-medicaid-enroll`)  |
| `version`             | monotonically increasing integer per slug                      |
| `prompt_body`         | the natural-language prompt (Markdown), free-form              |
| `prompt_hash`         | SHA-256 of `prompt_body`, for dedup and change detection       |
| `notes`               | changelog line for this version                                |
| `created_at`, `author`|                                                                |

Uniqueness on `(slug, version)`. Same `slug` can have many versions; you never
edit an existing row in place — new content = new version.

**`schema_versions`** — the JSON input schema associated with a compiled artifact.

| column               | notes                                                                 |
|----------------------|-----------------------------------------------------------------------|
| `id`                 | PK                                                                    |
| `prompt_template_id` | FK → `prompt_templates.id`                                            |
| `schema_hash`        | SHA-256 of canonical-JSON of the schema                               |
| `schema_json`        | the full `input_schema` snapshot at compile time                      |
| `version`            | monotonically increasing per `prompt_template.slug`                   |
| `cc_workflow_id`     | the CloudCruise workflow_id returned by compiling this prompt/schema  |
| `compiled_at`        |                                                                       |

**`workflow_mappings`** — evolve to point at a *specific* schema version:

| column               | notes                                                        |
|----------------------|--------------------------------------------------------------|
| `id`, `target_url`, `name` | (as today)                                             |
| `schema_version_id`  | FK → `schema_versions.id` (replaces the bare `workflow_id`)  |
| `pinning`            | `pinned` (locked to this version) or `latest` (auto-follow)  |

At autofill time we resolve `target_url → mapping → schema_version → cc_workflow_id + schema_json`, and the mapper reads from `schema_json` — no live `/metadata` call needed in the hot path (still available as a "refresh schema" action).

### Versioning rules

- **Prompt versioning is append-only.** You never rewrite a prompt row; editing
  the prompt produces a new `prompt_templates` row with `version = max+1`.
  Enables diffs and rollback.
- **Schema versioning is derived.** Whenever a prompt is (re)compiled against
  CloudCruise, snapshot `/metadata`'s `input_schema` into a new
  `schema_versions` row, recording `schema_hash`. If the schema hash matches
  the previous version, don't bump — just reuse.
- **Breaking-change detection.** Before promoting a new `schema_version` to a
  mapping using `pinning=latest`, compare the new schema against the previous:
  - **compatible** — new optional fields only → auto-promote.
  - **breaking** — `required` field added / renamed / removed / enum narrowed
    → block promotion, require a human ACK. Practitioner data will not fill a
    field that no longer exists (or is now required but empty).
- **Immutable artifacts.** `cc_workflow_id` values are never deleted; historical
  sessions must remain re-openable in CloudCruise.

### Autofill session lineage

`autofill_sessions` gains `schema_version_id` (and by transitivity
`prompt_template_id` + `prompt_version`). Every session is traceable to the
exact prompt+schema that produced it — needed for compliance replays and for
answering "why did this practitioner's fax field end up blank last quarter?"

### Backfill

Existing rows in `workflow_mappings` get migrated by:

1. Creating a synthetic `prompt_templates` row with `prompt_body =
   "[imported — original prompt unknown]"` and `version = 1`.
2. Fetching `/metadata` once for the existing `cc_workflow_id`, storing it as
   the first `schema_versions` row.
3. Rewriting the mapping to point at that `schema_version_id`.

### Compile flow (when / if CloudCruise ships a compile API)

`POST /api/prompt-templates/{id}/compile`:
1. read the prompt body,
2. call CloudCruise "compile" endpoint (hypothetical today),
3. poll until the resulting `workflow_id` reports a stable `/metadata` schema,
4. write a new `schema_versions` row with `cc_workflow_id` + schema snapshot,
5. run schema-diff against the previous version; auto-promote `latest`
   mappings only if the diff is compatible.

Until that API exists, the compile step is manual (paste into CC UI, copy the
`workflow_id` back into a form on the Mappings tab) — but everything downstream
(schema snapshot, hash, diff, session lineage) already runs.

### Non-goals

- Storing the *rendered* workflow (CC's DOM script) locally — that's their
  build output, not ours.
- Runtime prompt evaluation — prompts compile at authoring time, not per run.
  Runs always execute a pre-compiled `workflow_id`.

