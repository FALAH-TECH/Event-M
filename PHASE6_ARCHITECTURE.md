# Phase 6 integration status

Phase 6 is **not yet integrated**. The currently active browser request path is
`app.py` → a blueprint in `routes/` → `data.py`'s in-memory collections → a
Jinja template in `templates/`. A Flask restart discards changes. Authentication
also still uses the Phase 2 plaintext demo data. Do not use this implementation
as a persistent or production service.

The new `database.py` is preparatory infrastructure and is not yet called by
the blueprints. Its `connect()` reads MySQL settings from environment variables;
`transaction()` commits successful work and rolls back exceptions. The intended
path is browser → Flask blueprint → explicit data-access functions →
`database.connect()` or `database.transaction()` → MySQL → template. All
existing list reads and mutations need to be replaced before that path is active.

`verify_mysql.py` loads `.env` and performs only `SELECT DATABASE()`, `SHOW
TABLES`, and fixed count queries. Copy `.env.example` to `.env`, configure the
local values, install `requirements.txt`, and run `python verify_mysql.py`.
The password and Flask secret must remain private. The reference SQL in
`docs/database/` must not be executed against the existing database.

Persistence testing is pending integration: after implementation, create an
event through the admin UI, note its name, stop and restart Flask, and confirm
the event is present both in the UI and with a parameterized read-only MySQL
query. Do not delete the test event without the owner's approval.
