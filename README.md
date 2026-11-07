# EventHub — Event Management System

A web-based college event management application built using Python and Flask.

EventHub provides a centralized platform for administrators, team managers, and participants to manage college events, registrations, schedules, and competition results.

> **Project Status:** Academic microproject demo — currently being upgraded into a secure, database-backed, deployable web application.

## Overview

EventHub was originally developed as a DBMS microproject to demonstrate the workflow of a college event management system.

The existing application provides role-based dashboards, event management, participant records, registration workflows, schedules, and result management.

The current version uses in-memory Python data structures instead of a persistent relational database.

The next stage of development focuses on improving the application architecture, implementing a real database, strengthening security, adding automated testing, and deploying the application.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask 3 |
| Frontend | HTML, CSS, JavaScript |
| Templates | Jinja2 |
| Current data storage | Python lists and dictionaries (`data.py`) |
| Session management | Flask sessions |
| Version control | Git and GitHub |

**Planned additions:** SQLAlchemy, Flask-Migrate, PostgreSQL, pytest, Docker, Gunicorn, and GitHub Actions.

These additions are part of the development roadmap and have not yet been implemented.

## Current Features

### Administrator

- Access the administrator dashboard.
- Create, view, update, and delete events.
- Manage competition items within events.
- Create and manage team manager accounts.
- Assign events to team managers.
- Manage participant records and registrations.
- Enter and publish competition results.
- Manage account profile information.

### Team Manager

- Access a dedicated team manager dashboard.
- View assigned events and competition schedules.
- Register participants for assigned events.
- View participants and their registrations.
- View competition results.
- Manage account profile information.

### Participant

- Create a participant account.
- Log in to a dedicated participant dashboard.
- View events and competition schedules.
- View registered competition items.
- View published competition results.
- Update account profile information.

**Note:** Participant self-registration for individual competition items, including capacity validation and scheduling conflict checks, is planned for a later development phase.

## Project Structure

```text
Event-M/
├── app.py
├── data.py
├── requirements.txt
├── README.md
│
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── auth_utils.py
│   ├── decorators.py
│   ├── admin.py
│   ├── manager.py
│   └── participant.py
│
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── admin/
│   ├── manager/
│   ├── participant/
│   ├── layouts/
│   └── partials/
│
└── static/
    ├── css/
    ├── js/
    └── img/
```

This shows the main application files and folders. Generated cache files and local development files are omitted.

## Local Development Setup

### Prerequisites

- Python 3
- Git
- pip
- A terminal
- A code editor such as Visual Studio Code

### 1. Clone the repository

```bash
git clone https://github.com/FALAH-TECH/Event-M.git
cd Event-M
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate the environment on Linux or WSL:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
python app.py
```

### 5. Open the application

Visit:

http://127.0.0.1:5000

The Flask development server runs locally on port 5000.

**Important:** This setup is intended for local development only. The application is not yet ready to be exposed to the public internet.

## Authentication

The current application uses demonstration accounts stored in `data.py`.

Authentication and role-based navigation are implemented using Flask sessions and custom route decorators.

This implementation is suitable for exploring the application locally but is not production-ready.

Planned authentication improvements include:

- Database-backed user accounts.
- Secure password hashing.
- Stronger server-side validation.
- Secure session configuration.
- Role-based authorization checks.
- CSRF protection.
- Secure administrator account creation.
- Password reset functionality.

Default login credentials are intentionally not documented here.

**Security notice:** Existing demonstration passwords and the development secret key are still present in the current source code. They must be replaced as part of the security upgrade before public deployment.

## Current Limitations

The application is still in its demonstration stage.

### 1. In-memory data storage

The application currently stores users, events, registrations, and results using Python data structures.

Changes to this data are not permanently saved and may be lost when the application process restarts.

### 2. Authentication security

The existing demonstration authentication system uses plaintext passwords and requires security improvements.

### 3. Database integration

A persistent relational database has not yet been integrated into the current GitHub version.

### 4. Automated testing

An automated test suite has not yet been implemented.

### 5. Production deployment

The application has not yet been configured for production hosting, HTTPS, persistent storage, and production-grade application serving.

## Development Roadmap

The project is being upgraded in structured phases.

| Phase | Focus | Status |
|---|---|---|
| 0 | Repository hygiene and documentation | In progress |
| 1 | Application structure and configuration | Planned |
| 2 | Relational database and migrations | Planned |
| 3 | Authentication and security | Planned |
| 4 | Registration and event management improvements | Planned |
| 5 | Automated testing and CI | Planned |
| 6 | Docker and production deployment | Planned |
| 7 | Final documentation and project release | Planned |

### Phase 0 — Repository Hygiene

Clean up generated files, configure Git exclusions, introduce environment configuration templates, and improve repository documentation.

### Phase 1 — Application Architecture

Refactor the Flask application using an application factory pattern, centralized configuration, and reusable application extensions.

### Phase 2 — Database Integration

Replace in-memory data structures with a relational database.

Planned database entities include:

- Users
- Events
- Competition items
- Manager assignments
- Registrations
- Competition results

Implement database relationships, constraints, migrations, and persistent CRUD operations.

### Phase 3 — Security

Introduce password hashing, secure authentication, authorization rules, CSRF protection, and validated form submissions.

### Phase 4 — Feature Improvements

Implement participant self-registration, registration capacity limits, scheduling conflict detection, waitlists, and automatically calculated leaderboards.

### Phase 5 — Testing and Continuous Integration

Introduce pytest-based automated testing and GitHub Actions workflows for validating changes.

### Phase 6 — Deployment

Prepare the application for deployment using Docker, Gunicorn, a persistent PostgreSQL database, and an HTTPS-enabled hosting platform.

### Phase 7 — Documentation and Release

Complete the technical documentation, database ER diagram, setup instructions, screenshots, deployment guidance, and release checklist.

## Project Goals

The main goals of this project are to:

1. Transform an academic demonstration into a functional web application.
2. Apply relational database design and normalization principles.
3. Understand backend architecture and application structure.
4. Implement secure authentication and authorization.
5. Learn database migrations and transaction handling.
6. Develop reliable backend features and business logic.
7. Write automated tests and introduce continuous integration.
8. Understand containerization and web application deployment.
9. Build practical software engineering experience through hands-on development.

## Development Approach

Development follows a step-by-step, learning-focused workflow:

**Understand → Design → Implement → Test → Review → Commit**

Each development phase is completed and verified before proceeding to the next.

The project prioritizes maintainable code, clear architecture, and practical understanding rather than unnecessary complexity.

## Future Scope

After the core application becomes stable, possible improvements include:

- QR-code-based participant check-in.
- Activity and audit logs.
- Competition result exports.
- Event participation certificates.
- Improved search and filtering.
- Administrative reporting.

These features are optional and are not part of the current implementation.

## Project Repository

GitHub: https://github.com/FALAH-TECH/Event-M

## Maintainer

**FALAH-TECH**

GitHub: https://github.com/FALAH-TECH

---

**EventHub is an ongoing learning and development project, progressing from an academic DBMS demonstration toward a secure, reliable, and deployable web application.**