# Phase 6 architecture

A browser request reaches `app.py`, which loads `.env`, configures Flask and
registers the role blueprints. `routes/decorators.py` checks the session role
before protected routes run. For example, `routes/admin.py:events()` calls
`data.get_events()` to display events and `data.save_event()` to create one.
The route passes the returned dictionaries to the existing Jinja templates.

`data.py` is the repository and the single mapping between MySQL and the
existing template keys. `data.cursor()` uses `database.transaction()` to open
a connection, commit successful operations, roll back exceptions and close it.
All values supplied by users are sent as parameters. Multi-table changes such as
an activity and its schedule, a club and its associations, a coordinator and
assignments, standings, or a registration and its selected activities share a
transaction. `database.new_id()` creates UUID-based IDs for all entities except
events. Event creation uses `data.next_event_id()` and a MySQL advisory lock held
until the insertion commits and its connection closes. It reads numeric `e` IDs
using a current locking read, ignores UUID-style IDs, and starts at `e4`. All
event writers must use the same lock for concurrent allocation to be safe.
The lock is local to one MySQL server and is not a distributed sequence. If the
highest numeric event is deleted, its ID can be reused; avoiding reuse requires
a durable sequence or counter, which this schema does not provide. Foreign-key
restrictions are retained; activity deletion removes its owned schedule inside
the same transaction and rolls back if other references prevent deletion.

| Application dictionaries | MySQL tables |
| --- | --- |
| Users, college, assigned events | `users`, `colleges`, `coordinator_events` |
| Events and `items` | `events`, `activities`, `venues`, `schedules` |
| Clubs and associations | `clubs`, `club_events`, `club_coordinators` |
| Registrations and `itemIds` | `registrations`, `registration_activities` |
| Activity results | `activity_results` |
| Overall results and entries | `event_results`, `event_standings`, `colleges` |

`routes/auth.py:login()` loads the user through the repository and verifies the
Werkzeug password hash. New or changed passwords are hashed in `data.save_user()`.
Existing participant registration by a coordinator retains the original demo
password behavior for newly created accounts; change this password after login.
Participant results use the repository's published-only queries. Coordinator
views are restricted to assigned events. The database is the source of truth;
there is no in-memory fallback.

Copy `.env.example` to `.env`, set `MYSQL_PASSWORD` and a long random
`FLASK_SECRET_KEY`, install `requirements.txt`, and run `python verify_mysql.py`
for read-only inventory before starting `python app.py`. The SQL in
`docs/database/` is reference material and must not be re-executed against the
existing database. `python -m unittest discover -s tests -v` uses mocks for
writes and does not modify MySQL.

To test persistence, create a clearly named event through the administrator UI,
restart Flask, and look for it on the events page. A read-only parameterized
query of `events` can independently confirm it. To test registration persistence,
create an activity for that event and register a participant through Data Entry,
then check `registrations` and `registration_activities`. Test records are real
records; obtain approval before deleting them.
