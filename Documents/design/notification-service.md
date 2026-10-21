# In-App Notification Service (SETUP.13 · Issue #14)

Traceability: NFR-06, NFR-07 · Used by FR-04 (allocation), FR-06 (complaints), FR-09 (leave) · Test case: `UT_SETUP_11`

## API (`core/notifications.py`)

| Function | Purpose |
|---|---|
| `notify(student, category, message)` | Save an unread notification and return it |
| `get_notifications(user, unread_only=False)` | A user's notifications, newest first |
| `unread_count(user)` | How many are unread |
| `mark_read(user, notification_id)` / `mark_unread(...)` | Change one notification; returns `False` if it is not that user's |
| `mark_all_read(user)` | Mark all read; returns how many changed |

`student` / `user` can be a `Student` or a `UserAccount` (for example a warden).
`category` is the notification type: `ALLOCATION`, `FEE`, `LEAVE`, `COMPLAINT` or `NOTICE`
(upper or lower case). Bad input raises a `ValidationError` using the standard messages from
`core/error_messages.py` (for example `Message is required`).

## How modules call it

```python
from core.notifications import notify

notify(allocation.student, 'ALLOCATION', f'You have been allocated room {room.room_no}')   # FR-04
notify(complaint.student, 'COMPLAINT', 'Your complaint was marked Resolved')               # FR-06
notify(leave.student, 'LEAVE', 'Your leave application was approved')                      # FR-09
```
Call it from the module's service function, after the main change succeeded.
Modules must not read or write the `Notification` table directly.

## Data

Table `core_notification` (matches `Documents/design/schema.sql`): `recipient` (FK to `UserAccount`),
`category`, `message` (max 255), `is_read` (default false), `created_at`, `updated_at`.
Index `ix_notification_unread` on `(recipient, is_read)` keeps the unread count fast.

## Migration note

`0001_initial` creates tables from the live model registry, so a brand-new database already gets the
notification table from it. `0002_notification` creates the table only when it is missing, so it works
both on new databases and on databases created before this issue. Reversing `0002` does nothing;
reversing `0001` removes all core tables.

## Not in this issue
The notification list page, the unread badge in the header and "mark as read" buttons are screen work.
Add them with the module that first needs them, using `get_notifications`, `unread_count` and `mark_read`.
