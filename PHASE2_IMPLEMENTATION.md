# Aether Phase 2 A/B/C implementation

Faculty Coordinator uses the existing `manager` role, routes, demo credentials and assigned-event permissions. The interface now calls this role Faculty Coordinator. Coordinators can view their associated clubs and those clubs' event details; that view does not grant additional registration or event access.

Administrators can create, edit, view and delete clubs, and associate each club with events and coordinators. Names are required and checked case-insensitively for duplicates. A club with associated existing events cannot be deleted. Club names appear on event pages. Deleting an event or coordinator removes its club associations.

Administrators can manage venues and select a venue when creating or editing an event, including through Data Entry. Venue names are required and checked for duplicates. A venue in use by an event or activity cannot be deleted. Renaming a venue updates matching event and activity names. Activities retain their independent free-text locations.

The provisional `CLUBS` and `VENUES` lists in `data.py` exist only in the running Python process. Club records contain lists of existing event and coordinator identifiers; venue references remain names to match existing sample data. Initial venues are derived from sample events and activities. Data resets on restart and is not shared between processes. These are application-level assumptions, not a proposed relational design. The database team must design and implement persistence, relationships, constraints, migration and concurrency handling independently.

Files changed: `data.py`; `routes/admin.py`, `routes/manager.py`, `routes/participant.py`; admin club, venue, event, data-entry, dashboard and coordinator templates; manager club, event and dashboard templates; participant home and sidebar templates; `README.md`; and `tests/test_phase2.py`. No SQL files or database connections were added.

Validation: run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v`. The focused Flask client tests cover demo logins, role restrictions, club and venue CRUD, associations, venue selection, activity editing, registrations, schedules and result page rendering. Browser interaction and MySQL persistence are not covered. Existing sample data and manager assignment behavior remain in use. The existing application uses development-only authentication and in-memory storage; production security and durability require separate work.
