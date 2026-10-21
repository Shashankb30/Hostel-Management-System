# Application Shell: Layout, Navigation and Role-Based Menus (SETUP.11 · Issue #12)

Traceability: NFR-02 (simple, consistent UI), NFR-06, NFR-07 · Test case: `UT_SETUP_09`

## What it provides

| Piece | File | Purpose |
|---|---|---|
| Common layout | `templates/base.html` | Top bar (user, role badge, logout), role menu on the left, content area. Every page extends it. |
| Role menus | `core/navigation.py` | One menu list per role. Items are looked up by URL name. |
| Role helpers | `core/roles.py` | `get_role(user)`, `role_required(...)` decorator for views. |
| Menu in every template | `core/context_processors.py` | Adds `nav_items`, `hms_role`, `hms_role_label`. |
| Placeholder dashboards | `core/views.py`, `templates/core/dashboard.html` | `/dashboard/student/`, `/dashboard/warden/`, `/dashboard/admin/` |
| Temporary login/logout | `config/urls.py`, `templates/registration/login.html` | So the shell can be used now. **FR-01 replaces these.** |

`/` sends each logged-in user to the dashboard for their role. A user with the wrong role gets a 403 page, and a user with no HMS account (or a locked one) gets a 403 page too.

## Menus by role

| Student | Warden | Administrator |
|---|---|---|
| Dashboard | Dashboard | Dashboard |
| My Profile | Rooms & Vacancy | Users & Roles |
| My Room | Room Allocation | Students |
| Fees & Payments | Complaints | Rooms |
| Complaints | Attendance | Fees |
| Attendance | Visitors | Notices |
| Leave | Leave Requests | Reports |
| Notices | Notices | Admin Site |

## How a module plugs in

1. Create the module's views and URLs with the **namespace and name** from the table below.
2. Include them in `config/urls.py`.
3. The menu item turns from greyed out ("Soon") to a working link automatically. No shell code changes.
4. Protect each view with `@role_required('warden')` (or the right roles) from `core.roles`.
5. Extend `base.html` in the module's templates.

| Menu item | Roles | URL name to register |
|---|---|---|
| My Profile | Student | `students:my_profile` |
| My Room | Student | `allocation:my_room` |
| Fees & Payments | Student | `fees:my_fees` |
| Complaints | Student / Warden | `complaints:my_complaints` / `complaints:manage` |
| Attendance | Student / Warden | `attendance:my_attendance` / `attendance:manage` |
| Leave | Student | `leave:my_leaves` |
| Leave Requests | Warden | `leave:review` |
| Notices | Student / Warden, Admin | `notices:board` / `notices:manage` |
| Rooms & Vacancy | Warden | `rooms:vacancy` |
| Room Allocation | Warden | `allocation:manage` |
| Visitors | Warden | `visitors:log` |
| Users & Roles | Admin | `accounts:users` |
| Students | Admin | `students:list` |
| Rooms | Admin | `rooms:manage` |
| Fees | Admin | `fees:manage` |
| Reports | Admin | `core:reports` |

To rename or add a menu item, edit `MENUS` in `core/navigation.py`.

## Try it

```bash
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```
Open <http://127.0.0.1:8000/> and log in as `stu1023` / `Pass@123`, `wdn05` / `Warden@12` and `admin01` / `Admin@12`.
