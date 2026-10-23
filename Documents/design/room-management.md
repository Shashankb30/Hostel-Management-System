# Room Management (FR-03 · Issues #39 to #51)

Traceability: FR-03 (R3), UC-03 · NFR-05 (data integrity), NFR-07 (more hostels and rooms) · Test Plan: `UT_07_Room`, `UT_08_Room`, `UT_09_Room`, `IT_07_Room`, `IT_08_Room`, `IT_09_Room`, `ST_05_Room`, `ST_06_Room`, plus `UT_ROOM_10`, `UT_ROOM_11`, `IT_ROOM_12`, `UT_ROOM_13`, `IT_ROOM_14`

The data model already existed (`core.Room`, `core.Allocation`), so there are **no migrations**. Two small apps were added: `rooms` (this module) and `allocation`, which for now only holds the student's *My Room* page. FR-04 will add the allocation and transfer screens to it.

## What was built

| Issue | Story | Where |
|---|---|---|
| #40 | Add a room with number, capacity and type; a new room is Vacant | `rooms/forms.py`, `rooms/services.py`, `rooms/views.py` |
| #41 | Duplicate room number rejected (`Room number already exists`) | `rooms/forms.py` |
| #42 | Capacity must be a whole number from 1 to 100 | `rooms/forms.py` |
| #43 | Edit number, capacity, type, block and floor with the same checks | `rooms/views.py` `room_edit` |
| #44 | Occupancy, vacancy and status come from the allocations | `rooms/selectors.py` |
| #45 | Full and unavailable rooms are left out of allocation lists | `rooms/selectors.py` `open_for_allocation` |
| #46 | Room changes show up on the student's room page | `allocation/views.py` (reads live data) |
| #47 | Student sees their own room, roommates and an empty state | `allocation/views.py`, `templates/allocation/my_room.html` |
| #48 | Filter rooms: All, Vacant only, Full | `rooms/selectors.py` `filter_by_vacancy` |
| #49 | Occupied rooms cannot be deleted; unoccupied rooms can be deleted or made unavailable | `rooms/services.py` |
| #50 | Warden's *Rooms & Vacancy* page, with availability updates | `rooms/views.py` `room_vacancy` |
| #51 | Capacity cannot drop below the students currently in the room | `rooms/services.py` `check_capacity` |
| #39 | Epic: close it when everything above is merged | |

## Who can do what

| | Administrator | Warden | Student |
|---|---|---|---|
| See rooms with occupancy and vacancy | all hostels | own hostel | |
| Add, edit, delete rooms | yes | no | |
| Make a room unavailable / available | yes | yes (own hostel) | |
| See own room | | | yes |

## Rules worth knowing

- **Status is never stored.** A room is *Vacant* (nobody in it), *Partially occupied* or *Full*. This is worked out from the active allocations each time the list is shown, so it can never go out of date after an allocation, transfer or vacating. The list does it with one query, however many rooms there are.
- **Room numbers are unique per hostel**, ignoring case and spaces, so `A-101` can exist in two different hostels. The database also enforces this, so two people saving the same number at once get the same message instead of an error page.
- **Capacity** must be a whole number from 1 to 100. On edit it also cannot be lower than the number of students in the room now.
- **A room cannot move to another hostel** once created.
- **Delete is only for rooms that were never used.** A room with people in it must have them reassigned first. A room that has only *past* residents is kept for the records; make it unavailable instead.
- **Making a room unavailable** (for example, under repair) is refused while people live in it. Unavailable rooms are hidden from allocation lists and from the *Vacant only* filter, and can be made available again.
- **"Vacant only"** means rooms that are available and have at least one free bed, so a half-full room is included. This is the same list the allocation screens will offer.
- `rooms.selectors.open_for_allocation()` is the single place that decides which rooms can be offered. The FR-04 screens should build their vacant-room lists from it.

## Try it

```bash
python manage.py seed_data
python manage.py runserver
```

1. As `admin01` / `Admin@12` open **Rooms**, add room `D-301` (capacity 3, Triple) and note the status Vacant.
2. Try `A-101` again, then capacity `-2`, then `0`.
3. Edit a room and try to lower its capacity below its occupants (allocate students with the Django shell until FR-04 is built).
4. Use the **Vacant only** filter, then make a room unavailable and delete an unused one.
5. As `wdn05` / `Warden@12` open **Rooms & Vacancy** and make a room unavailable.
6. As `stu1023` / `Pass@123` open **My Room** (it shows the empty state until a room is allocated).

## Running the tests

```bash
python manage.py test rooms allocation
python scripts/update_test_matrix.py rooms allocation students accounts core
```
