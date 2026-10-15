# Software Architecture Document

Hostel Management System | Version 1.1 (draft) | 15 October 2026

Course: Software Engineering (UE23CS341A) | Team: Shashankb30, abhijeetcyalgi

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture of the Hostel Management System (HMS): how the system is decomposed into components, how those components interact, and why the main architectural decisions were made. It is the blueprint for Sprint 1 and Sprint 2 and gives a path from the SRS requirements to the code. Its structure follows the architecture-document outline taught in Unit 2 (Software Design vs. Architecture).

### 1.2 Scope

The document covers the web application used by three roles (Student, Warden, Administrator) and the ten functional modules FR-01 to FR-10 of the SRS, together with the non-functional requirements that shape the architecture. Class-level design is out of scope. The data model is described in the companion file ER\_DIAGRAM\_AND\_SCHEMA.md.

### 1.3 Definitions, acronyms and abbreviations

| Term | Meaning |
| --- | --- |
| HMS | Hostel Management System |
| SRS / SAD | Software Requirements Specification / Software Architecture Document |
| FR / NFR | Functional / Non-Functional Requirement |
| MVC / MVT | Model-View-Controller / Django's Model-Template-View variant of it |
| ORM | Object-Relational Mapper (Django ORM) |
| ADR | Architecture Decision Record |
| CI | Continuous Integration (GitHub Actions) |
| WSGI | Python web server gateway interface used by Django |

### 1.4 References

1. HMS Software Requirements Specification (SRS\_Document.docx)
2. HMS Use Case Flow and Use Case Diagram
3. HMS Test Plan Document and TEST\_PLAN\_MATRIX.md
4. ADR 0001: Technology stack and architecture (docs/adr/0001-tech-stack.md)
5. ER Diagram and Relational Schema (docs/design/ER\_DIAGRAM\_AND\_SCHEMA.md)
6. Course material: Software Engineering, Unit 2, Software Design vs. Architecture (PES University)

## 2. Architectural representation

The architecture is described through the views below. Each view answers one question and is kept to one page, as the course guidelines recommend.

| View | Question it answers | Section |
| --- | --- | --- |
| Use-case view | Which scenarios drive the architecture? | 4 |
| Logical view | How is the system decomposed into subsystems and layers? | 5.1 |
| Process view | What runs at run time and how do the parts cooperate? | 5.2 |
| Deployment view | Where does each part run? | 6 |

Notation: boxes and arrows at subsystem level (Django apps, not classes). Legend used in all diagrams:

| Symbol | Meaning |
| --- | --- |
| Box | A subsystem (Django app), a layer or a runtime node |
| Solid arrow A to B | A calls or depends on B (B never depends back on A) |
| Dashed arrow | A uses the shared notification service in core |
| Cylinder | Database |

## 3. Architectural goals and constraints

### 3.1 Goals

| Goal | Source | Architectural response |
| --- | --- | --- |
| Secure login, role-based access, safe password and session handling | NFR-01 | Django authentication, groups and permission checks; custom lockout backend; framework protection against CSRF, XSS and SQL injection |
| Response time of about 3 seconds or less for normal operations | NFR-03 | Indexed lookups, derived values computed with single queries, paginated lists |
| Backup and restore of data | NFR-04 | Single database with a documented dump and restore procedure |
| Data integrity enforced on the server | NFR-05 | Database constraints (unique, check, partial unique) plus service-layer rules |
| Modular structure with independent modules | NFR-06 | One Django app per SRS module; communication only through services and foreign keys |
| Support for more than one hostel or block | NFR-07 | Hostel entity at the top of the data model; hostel-owned records carry a hostel reference |
| Traceability from requirements to code and tests | Course / assignment | Backlog issue to module to test mapping; ADR and design documents in the repository |

### 3.2 Constraints

| Constraint | Effect on the architecture |
| --- | --- |
| Team of two, two one-week sprints (19 to 23 Oct and 26 to 30 Oct 2026) | Prefer a framework that provides authentication, ORM and migrations; avoid separate front-end and API projects |
| Work must follow the submitted SRS and Test Plan | Module list and rules mirror the SRS; deviations are recorded in section 9 |
| Delivery through GitHub (issues, pull requests, Actions) | Repository layout and CI pipeline are part of the architecture |
| Must run on a student laptop with no paid services | SQLite for development; schema kept portable to PostgreSQL |

## 4. Use-case view

Actors: Student, Warden, Administrator. The use cases below are the architecturally significant ones, meaning they force a structural decision rather than just adding a screen.

| Use case | Module | Why it is architecturally significant |
| --- | --- | --- |
| Log in, lock account after repeated failures, redirect by role | FR-01 | Defines the security architecture: custom authentication backend, session handling, role-based menus |
| Register a student and create the login | FR-02 | Links the user account to the student record; duplicate checks must be enforced by the database |
| Allocate or transfer a room | FR-04 | Must never exceed room capacity or give a student two rooms, even with simultaneous requests; touches rooms, students and notifications |
| Record a fee payment | FR-05 | Paid, outstanding and status values must always agree with the payment records, so they are derived, not stored |
| Submit and approve a leave application | FR-09 | Cross-module workflow with a notification back to the student |
| Raise a complaint and assign demerit points | FR-06 | Points accumulate per student and are derived from complaint records |
| Post a notice for an audience | FR-10 | Audience targeting by role and hostel |

## 5. Logical view

### 5.1 Architecture overview: package and subsystem layering

HMS is a modular monolith that combines three well-known architectural patterns from the course:

- **Client-server:** browsers (clients) send requests; one server process holds the business logic, security and data.
- **Layered:** presentation, application (services), domain (models) and data layers, each calling only the layer below it.
- **Model-View-Controller (Django MVT):** models hold data and rules, templates present, views mediate between them.

Why not microservices or event-driven? The system has one database, one deployment and two developers. A monolith with strict module boundaries gives the same modularity at a fraction of the cost, and a module can still be split out later.

#### Layers

| Layer | Components | Responsibility | May call |
| --- | --- | --- | --- |
| Presentation | Django templates, Bootstrap, role-based navigation (core/navigation.py) | Render pages, forms and menus | Application layer |
| Application | URL routing, views, forms, service modules (services.py) | Control flow, business rules, permission checks, notifications | Domain layer |
| Domain | Models, constraints, derived properties | Data, invariants and calculated values | Data layer |
| Data | Django ORM, migrations, SQLite or PostgreSQL | Persistence | None |

#### Subsystems

| Subsystem (Django app) | SRS module | Main responsibility |
| --- | --- | --- |
| core | Shared | Hostel entity, notification service, role-based navigation, dashboard |
| accounts | FR-01 | Users, roles, login, lockout, session |
| students | FR-02 | Student records and profile |
| rooms | FR-03 | Rooms, capacity, derived occupancy and vacancy |
| allocation | FR-04 | Allocations, transfers, requests and waiting list |
| fees | FR-05 | Fee records, payments, receipts, dues |
| complaints | FR-06 | Complaints, severity, demerit points, status |
| attendance | FR-07 | Student check-in and check-out |
| visitors | FR-08 | Visitor log |
| leave | FR-09 | Leave applications and approval |
| notices | FR-10 | Notices by audience and expiry |

#### Design principles applied

| Principle (from the course) | How HMS applies it |
| --- | --- |
| High cohesion | Each app has one purpose; for example all fee rules live in fees and nowhere else |
| Loose coupling | Apps depend on students, rooms and core only, through foreign keys and service calls; no app edits another app's tables directly |
| Modularity | A change to one SRS module is local to one app; errors cannot spread through shared state |
| Separation of concerns | Rules in services and models, not in templates or views |
| Abstraction | Other modules call core.services.notify(user, message) and do not know how notifications are stored |

### 5.2 Process view

#### 5.2.1 Processes

| Process | Description |
| --- | --- |
| P1 Browser | Client of the Student, Warden or Administrator; sends HTTP requests and renders HTML |
| P2 Web application | One Django process behind WSGI; each request is handled in its own thread and passes through middleware, URL routing, view, service and model |
| P3 Database engine | SQLite file in development, PostgreSQL in production; executes transactions and enforces constraints |
| P4 CI runner | GitHub Actions job on every pull request: system check, migration check and test run (not part of the run-time system) |
| P5 Seed command | python manage.py seed\_data, a one-off process that loads demo and test data |

#### 5.2.2 Process to design elements

P2 contains the subsystems in section 5.1. Every request follows the same path: middleware (session, CSRF, authentication), then URL routing, then a view, then a service or model, then the database, then a template that renders the response.

#### 5.2.3 Process model to design: key flows

**Login with lockout (FR-01).** The login form first checks whether the account is inactive or locked and shows a clear message. The authentication backend then refuses locked or inactive accounts. A failed attempt increases a counter; reaching the limit (5 attempts) locks the account for 15 minutes; a successful login resets the counter.

**Allocate a room (FR-04).** The warden selects a student and a room. The allocation service starts a database transaction, locks the room row, checks that the room is available and below capacity, creates an ACTIVE allocation and calls notify() for the student. A partial unique index on the allocation table ensures one active room per student even if two requests arrive together. On SQLite the database serialises writes; on PostgreSQL the row lock does the same job.

**Record a payment (FR-05).** The fee service validates a positive numeric amount, checks that the total paid does not exceed the fee, saves the payment with a unique receipt number and then notifies the student. Fee status is calculated from the payments each time it is shown, so it cannot drift out of sync.

#### 5.2.4 Model dependencies

Dependencies point from the dependent module to the module it needs. There are no cycles.

| Module | Depends on |
| --- | --- |
| accounts | core (hostel) |
| students | accounts, core |
| rooms | core |
| allocation | students, rooms, accounts, core (notify) |
| fees | students, accounts, core (notify) |
| complaints | students, accounts |
| attendance | students, accounts |
| visitors | students, accounts |
| leave | students, accounts, core (notify) |
| notices | core, accounts, core (notify) |

#### 5.2.5 Processes to the implementation

| Element | Where it lives in the repository |
| --- | --- |
| Settings, middleware, installed apps | config/settings.py |
| Root URL routing | config/urls.py |
| Role-based menu | core/navigation.py and core/context\_processors.py |
| Notification service | core/services.py and core/models.py |
| Authentication backend, lockout, signals | accounts/backends.py, accounts/signals.py, accounts/forms.py |
| Models and constraints | models.py in each app, with migrations under migrations/ |
| Page layout | templates/base.html |
| Seed data | core/management/commands/seed\_data.py |
| Tests | tests.py in each app, run with python manage.py test |
| CI pipeline | .github/workflows/ci.yml |

## 6. Deployment view

| Node | Software | Notes |
| --- | --- | --- |
| User device | Web browser (desktop or phone) | Loads Bootstrap from a public CDN; no installation needed |
| Application server | Python 3.12, Django 5.2, WSGI server | Development: manage.py runserver on a laptop. Production: a WSGI server such as gunicorn behind a reverse proxy with HTTPS |
| Database server | SQLite (development) or PostgreSQL (production) | Same schema and migrations on both |
| GitHub | Repository, project board, Actions runners | Every pull request runs checks and tests before the repository owner merges |

Connections: browser to application server over HTTP or HTTPS; application server to database through the ORM; GitHub Actions runs the test suite on its own runner with a temporary database.

## 7. Performance

- **Target:** normal operations respond in about 3 seconds or less (NFR-03); the baseline is to be measured under backlog issue NFR.06.
- **Indexed lookups:** roll number, email, room number and receipt number are unique, so searches on them use indexes.
- **Derived values** (occupancy, fee status, demerit total) are computed with single aggregate queries, avoiding stored copies that need updating.
- **Lists** (students, payments, complaints, visitors) are paginated and use select\_related to avoid repeated queries.
- **Scale assumption:** one hostel with hundreds of students and a handful of concurrent users; this is well within the capacity of SQLite and Django.

## 8. Quality

| Quality attribute | Tactics | Verified by |
| --- | --- | --- |
| Security (NFR-01) | Salted password hashing, sessions, CSRF tokens, automatic output escaping, ORM parameterised queries, lockout after repeated failures, role-based menus and permission checks | Login and lockout tests; security checks in the Test Plan |
| Integrity (NFR-05) | Unique, check and partial-unique constraints in the database plus service-layer rules | Unit tests for duplicates, capacity, payments and one active room per student |
| Modifiability and modularity (NFR-06) | One app per module, service interfaces, no cyclic dependencies | Code review of each pull request against section 5.2.4 |
| Extensibility (NFR-07) | Hostel entity and hostel references on owned records | Seed data with a hostel; extra hostels are data, not code |
| Testability | Service layer separated from views; seed command gives repeatable data | Automated unit, integration and system tests run by GitHub Actions |
| Maintainability | Documented structure, ADR, migrations in version control | ADR and design documents in the repository |
| Reliability and recoverability (NFR-04) | Single backup point (the database), transactions for multi-step changes | Backup and restore procedure (backlog issue NFR.08) |

## 9. Architectural decisions, deviations and open items

**Decisions.** The technology and structure decisions are recorded in ADR 0001: Python with Django, server-rendered templates with Bootstrap, SQLite for development with a PostgreSQL-compatible schema, one Django app per SRS module, and GitHub Actions for CI.

**Deviations from the previously submitted SAD.** Any difference between this document and the SAD submitted in Part 1 must be listed here and explained in the final demo. Entries to be completed by the team before the demo:

| Item | Submitted SAD | Implemented | Reason |
| --- | --- | --- | --- |
| (add rows as they arise) |  |  |  |

**Open items to confirm with the team:**

1. Demerit points per severity (suggested: minor 1, moderate 3, major 5) against the Test Plan.
2. Allocation priority rule (suggested: senior year first).
3. One fee record per student per academic year.
4. Final choice of production database (SQLite for the demo, PostgreSQL optional).
