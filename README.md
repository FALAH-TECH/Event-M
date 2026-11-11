# EventHub — College Event Management System

EventHub is a Flask prototype for a college event management system. I forked [the original Event-M project](https://github.com/siinnuu/Event-M) for my DBMS coursework to study how a web app handles requests, user roles, and data.

## What I explored

- Traced how Flask routes handle page requests and form submissions.
- Followed how login stores a user’s role in the session and redirects them to the appropriate page.
- Verified that changes to in-memory data survive a page refresh but are lost when the server restarts.

## Current status

The app uses mock data from `data.py`. MySQL is not connected in this version. The next step is to design the relational schema and replace the in-memory data with database-backed operations.

## Run locally

From the repository folder, install the dependencies and start the Flask app:

```bash
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Demo logins

These accounts are for the local demo only.

| Email | Password | Role |
|---|---|---|
| `admin@eventhub.edu` | `admin123` | Admin |
| `priya@mit.edu` | `manager123` | Team Manager |
| `ananya@student.edu` | `part123` | Participant |

There is no role selector on the login form. The app reads the role from the demo account and redirects the user automatically.
