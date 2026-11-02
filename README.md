# EventHub — Event Management System

Flask frontend for a DBMS academic project. Mock data in `data.py`; wire to a real DB later.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Demo logins

| Email | Password | Role |
|-------|----------|------|
| admin@eventhub.edu | admin123 | Admin |
| priya@mit.edu | manager123 | Faculty Coordinator |
| ananya@student.edu | part123 | Participant |

Login has no role selector — role is read from user data and redirects automatically.
