"""Read-only inventory of the configured Aether database; never runs SQL scripts."""
import sys

from dotenv import load_dotenv

import database

EXPECTED = {"users": 8, "events": 2, "activities": 8, "registrations": 8,
            "registration_activities": 16, "activity_results": 8, "event_standings": 5}
# These are literal, fixed identifiers, never supplied by a user.
COUNT_SQL = " UNION ALL ".join(
    "SELECT '" + name + "' AS entity, COUNT(*) AS rows_count FROM `" + name + "`"
    for name in EXPECTED
)


def main():
    load_dotenv()
    connection = database.connect()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT DATABASE()")
            print("Database:", cursor.fetchone()[0])
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            print("Tables:", len(tables), ", ".join(tables))
            cursor.execute(COUNT_SQL)
            for name, count in cursor.fetchall():
                print(f"{name}: {count} (reference seed: {EXPECTED[name]})")
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Avoid printing connector errors that could expose connection details.
        print(f"Read-only verification failed ({type(exc).__name__}); check MySQL configuration and connectivity.", file=sys.stderr)
        sys.exit(1)
