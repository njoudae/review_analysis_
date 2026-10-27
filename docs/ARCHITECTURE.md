# Architecture

## Runtime components

1. **Next.js dashboard** renders Arabic RTL management views. Reads run on the server, and mutations use Server Actions so the backend API key never reaches the browser. Production access is protected by server-side Basic authentication at the routing boundary and revalidated in the data-access layer; a deployment can later replace this gate with SSO without exposing the backend key.
2. **FastAPI API** owns validation, CRUD, metrics, issue management and run enqueueing.
3. **PostgreSQL** is the source of truth for organizations, branches, employees, review sources, reviews, analysis, issues, runs and notification attempts.
4. **Database-backed worker** claims queued runs using `SELECT ... FOR UPDATE SKIP LOCKED`. Collection and analysis do not run inside HTTP requests.
5. **Apify integration** builds input from active database review sources, not `apify_input.json`.
6. **OpenAI integration** uses Structured Outputs validated by Pydantic.
7. **Telegram integration** creates one persisted logical report per run, splits long messages, tracks attempts and retries failed delivery.

## Reliability boundaries

Reviews are persisted with an explicit processing state. A failure changes a review to `FAILED_ANALYSIS`; it does not make the review disappear. A failed run can be reset to `STARTED` through the retry endpoint and is claimed again by the worker. Telegram reports are unique by run ID and are never marked sent before Telegram confirms success.

## Data semantics

- Reviewer counts are distinct non-null Google reviewer names. They are not labeled customers.
- Sentiment metrics include only reviews with a stored analysis.
- Period filters use review publication time in UTC boundaries.
- Employee references are mentions, not performance ratings.
- Nationality alone never selects an employee. Responsibility remains unconfirmed unless changed through an authorized internal process.
- Gender is required and restricted to `F` or `M`; it is never inferred.

## Legacy preservation

The original script remains at the repository root. `backend/scripts/migrate_legacy_sqlite.py` opens the old SQLite database in read-only mode and copies reviews into a selected organization/branch/source. It never deletes or modifies the legacy database.
