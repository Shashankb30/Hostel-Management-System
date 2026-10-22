# Seed / Test Data (SETUP.09 · Issue #10)

Traceability: NFR-06, NFR-07 · Test case: `UT_SETUP_07`

The Test Plan cases are written against fixed data (stu1023, Room A-101, ...).
`python manage.py seed_data` loads exactly that data so every case can be run as written.

## Usage

```bash
python manage.py migrate        # once, on an empty database
python manage.py seed_data      # load or reset the Test Plan data
```

- **Idempotent.** Each record is looked up by its natural key (username, roll number, hostel + room number, student + year + fee description) and updated, never duplicated. Run it as often as you like.
- **Resets the baseline.** Re-running puts the seeded users back to their documented password and unlocked state (or inactive/locked for `stu9999`) and the seeded rooms back to their documented capacity. It does **not** delete anything else, so allocations and payments made while testing stay.
- **Safety.** The command refuses to run when `DJANGO_DEBUG=0` unless you pass `--force`, so test passwords cannot be loaded into a production database by accident.

## Accounts

| Username | Password | Role | State | Used by |
|---|---|---|---|---|
| `stu1023` | `Pass@123` | Student | active | UT_02_Login, UT_03_Login |
| `wdn05` | `Warden@12` | Warden | active | IT_01_Login |
| `admin01` | `Admin@12` | Administrator | active | IT_02_Login |
| `stu9999` | `Pass@123` | Student | **inactive + locked** | IT_03_Login |
| `stu1024` | `Pass@123` | Student | active | owner of the Divya S. record |

Every seeded account has the email `<username>@hms.example`, so the password reset flow (FR-01.09) can be tried. In development the reset email is printed in the terminal.

## Students

| Roll No | Name | Phone | Account | Used by |
|---|---|---|---|---|
| `CSE2201` | Arjun Rao | 9876543210 | `stu1023` | UT_05_Reg, UT_06_Reg, IT_04_Reg, fee cases |
| `CSE2202` | Divya S. | 9000000002 | `stu1024` | UT_11_Alloc, UT_19_Att |

## Rooms (all start vacant, hostel `MAIN`)

| Room | Block | Type | Capacity | Used by |
|---|---|---|---|---|
| `A-101` | A | Triple | 3 | UT_07_Room, UT_08_Room, IT_08_Room |
| `B-204` | B | Double | 2 | UT_11_Alloc, IT_10_Alloc, IT_11_Alloc, IT_12_Alloc |
| `C-102` | C | Double | 2 | IT_11_Alloc, IT_12_Alloc |

## Fees

| Student | Year | Description | Amount due | Used by |
|---|---|---|---|---|
| Arjun Rao | 2026-27 | Hostel fee | Rs. 50,000 | UT_14_Fee, UT_15_Fee |

## Notes
- **UT_05_Reg** registers Arjun Rao (CSE2201) as a *new* student, but the seed already creates him so that UT_06_Reg (duplicate roll number) has its pre-condition. Run UT_05_Reg on a freshly migrated database *before* seeding, or use a different roll number.
- Scenarios that need a full room (IT_08_Room, IT_10_Alloc) or an existing allocation (IT_11_Alloc) are set up by the test itself, because the seed leaves every room vacant.
