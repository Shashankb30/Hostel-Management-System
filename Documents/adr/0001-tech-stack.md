# ADR 0001: Technology stack and high-level architecture

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-19 |
| Deciders | Shashank B Jain (@Shashankb30), Abhijeet Cyalgi (@abhijeetcyalgi) |
| Issue | #7 (SETUP.06) |
| Requirements | NFR-06 (modularity), NFR-07 (scalability: more hostels, students, rooms) |
| Related | `Documents/Software Architecture Document - Hostel Management System.md`, `SAD.md` |

## 1. Context

HMS is a university hostel system with three roles (Student, Warden, Administrator) and ten functional modules (FR-01 to FR-10). The constraints are:

- Two developers and a 2-week delivery (two 1-week sprints).
- It must run on a student laptop with no paid services.
- Modules must stay independent (NFR-06), and extra hostels or modules must be addable without redesign (NFR-07).
- Security basics are required: authentication, RBAC, lockout, CSRF/XSS/SQL-injection protection (NFR-01).

## 2. Decision

| Concern | Decision |
|---|---|
| Architecture style | **Modular monolith**, layered (Presentation, Application, Domain, Data), client-server |
| Back end | **Python 3.12 + Django 5.2** (MVT) |
| Front end | **Django templates + Bootstrap 5** (server-rendered, no separate SPA) |
| Database | **SQLite** in development, **PostgreSQL** in production; same schema and migrations on both |
| Access control | Django authentication, **Groups** (Student, Warden, Admin) and permission decorators |
| Testing | Django test runner (`python manage.py test`), `tests.py` per app |
| CI | GitHub Actions: `manage.py check`, migrations check, tests on every PR |
| Deployment | WSGI (gunicorn) behind a reverse proxy with HTTPS; `runserver` for development |

## 3. Module boundaries (one Django app per SRS module)

| App | SRS module | Responsibility | May depend on |
|---|---|---|---|
| `core` | Shared | Hostel entity, notification service, role-based navigation, dashboard | none |
| `accounts` | FR-01 | Users, roles, login, lockout, session | core |
| `students` | FR-02 | Student records and profile | core, accounts |
| `rooms` | FR-03 | Rooms, capacity, occupancy and vacancy | core |
| `allocation` | FR-04 | Allocations, transfers, waiting list | core, students, rooms |
| `fees` | FR-05 | Fee records, payments, receipts, dues | core, students |
| `complaints` | FR-06 | Complaints, severity, demerit points | core, students |
| `attendance` | FR-07 | Check-in and check-out | core, students |
| `visitors` | FR-08 | Visitor log | core, students |
| `leave` | FR-09 | Leave applications and approval | core, students |
| `notices` | FR-10 | Notices by audience and expiry | core |

### Boundary rules
1. Business rules live in each app's `services.py` and models, never in views or templates.
2. Apps talk to each other only through **service functions and foreign keys**. No app writes another app's tables directly.
3. Dependencies point one way (see the table above). **No cyclic dependencies.**
4. Only `students`, `rooms` and `core` are shared by the other apps.
5. Cross-module notifications go through `core.notify()`.

## 4. How the design supports NFR-06 and NFR-07

- **New module** (NFR-06): add a new app and register it, depending only on `core`, `students` or `rooms`. No existing module changes.
- **Change to a module** (NFR-06): the change stays inside one app because the other apps only see its service interface.
- **More hostels** (NFR-07): `core.Hostel` is at the top of the data model and every hostel-owned record carries a `hostel_id`. A new hostel is a row of data, not a code change.
- **More students and rooms** (NFR-07): the ORM and migrations let the database move from SQLite to PostgreSQL unchanged, and indexed foreign keys keep queries fast.

## 5. Alternatives considered

| Option | Why not chosen |
|---|---|
| Node.js/Express + React SPA + REST API | Two codebases and a build chain for two developers; auth, admin, ORM, CSRF and migrations would all be built by hand |
| Spring Boot + Thymeleaf | More boilerplate and a heavier setup; the team is faster in Python |
| Flask | Lightweight, but auth, permissions, admin and migrations need extra libraries that Django ships with |
| Microservices | One database, one deployment and two developers; the overhead is not justified. A module can be split out later because of the boundary rules |
| MySQL | No advantage over PostgreSQL here; SQLite is simpler for development |

## 6. Consequences

**Positive**
- Auth, RBAC, ORM, migrations, forms and CSRF protection come built in, so there is more time for features.
- A single deployment unit is simple to demo and test.
- The boundary rules are checkable in code review.

**Negative / risks**
- A monolith scales as one unit. This is acceptable for hundreds of students.
- Boundary rules are enforced by convention and review, not by the compiler. Mitigation: review every PR against section 3.
- Server-rendered pages are less interactive than an SPA. Mitigation: Bootstrap plus small amounts of JavaScript where needed.

## 7. Follow-ups
- SETUP issues create the Django project and the app skeletons exactly as listed in section 3.
- Update `.github/workflows/ci.yml` to use Python 3.12 (it currently says 3.11) and to run `check`, `makemigrations --check` and `test` once the project exists.
