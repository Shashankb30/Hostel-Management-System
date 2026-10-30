# Fee Management (FR-05 · Epic #66, Issues #67 to #79)

Traceability: FR-05 (R5), UC-05 · NFR-01 (security), NFR-02 (simple UI) · Test Plan: `UT_13_Fee` to `UT_15_Fee`,
`IT_13_Fee` to `IT_15_Fee`, `ST_09_Fee`, `ST_10_Fee`, plus `UT_FEE_04` to `UT_FEE_07`, `IT_FEE_04`, `ST_FEE_03`

All of FR-05 lives in the `fees` app. It adds **no database tables and no migration**: it uses `core.FeeRecord`
(the fee a student owes) and `core.Payment` (each payment against it).

## Who can do what

| Screen | Address | Administrator | Student | Warden |
|---|---|---|---|---|
| Fee Management (all students) | `/fees/` | yes | no | no |
| One student's fees, payments, history | `/fees/student/<id>/` | yes | no | no |
| Define or edit a fee | `/fees/student/<id>/fees/new/`, `/fees/fees/<id>/edit/` | yes | no | no |
| Record a payment | `/fees/fees/<id>/pay/` | yes | no | no |
| Receipt | `/fees/payments/<id>/receipt/` | any | own only | no |
| My fees and payment history | `/fees/my/` | no | yes | no |
| Outstanding dues report (+ CSV) | `/fees/dues/` | yes | no | no |

## What was built, by issue

| Issue | Story | Where |
|---|---|---|
| #67 | Define and edit a student's fee (year, description, amount, due date) | `fees/forms.py` `FeeForm`, `fees/services.py` `define_fee`, `update_fee` |
| #68 | See total fee, amount paid and outstanding balance | `services.student_summary`, `templates/fees/student_fees.html` |
| #69, #70 | Record a full or a partial payment | `services.record_payment` |
| #71 | Reject a payment larger than the balance | `record_payment` (fee row is locked while the balance is checked) |
| #72 | Reject negative, zero or non-numeric amounts | `PaymentForm` with the shared `NumericValidator` |
| #73 | Status: Due, Partially Paid, Paid | `services.status_of` |
| #74 | Receipt for every payment | `services.receipt_number`, `balance_after`, `templates/fees/receipt.html` |
| #75, #76 | Student sees own fees and history, oldest first | `views.my_fees`, `services.payment_history` |
| #77 | No duplicate payment from a double click or resubmit | one-time form code + 30-second identical-payment guard |
| #78 | Choose a payment mode | `Payment.MODE_CHOICES` on `PaymentForm` |
| #79 | Outstanding dues report | `services.dues_report`, `templates/fees/dues_report.html` |

## Rules worth knowing

- **Money.** Amounts have at most two decimal places and at most 99,999,999.99. They are shown as `Rs. 50,000`
  (paise only when there are some).
- **Status** comes from the numbers, never from a stored flag: nothing paid = **Due**, something paid = **Partially Paid**,
  everything paid = **Paid**. A fee cannot be overpaid, so the balance never goes below zero.
- **One fee per student, year and description.** The same combination is rejected (ignoring capital letters). A fee
  cannot be edited to less than what has already been paid.
- **Receipt number** is `RCP-` plus the payment id (for example `RCP-000123`). It is unique and never changes, and it
  needs no extra column.
- **Duplicate protection.** Each payment form has a one-time code kept in the session. Saving the same form a second
  time is refused with a warning; a mistake such as a bad amount does not use the code up. An identical payment (same
  fee, amount, mode and date) within 30 seconds is also refused, even from a new form.
- **History order** is by payment date, then by the order the payments were entered. "Balance after" follows that
  same order.
- **Dues report** lists fees with a balance for active students, largest first, flags fees past their due date as
  Overdue, can show overdue only, and downloads as CSV.
- **Deleting.** Fees and payments cannot be deleted from these screens, so the money trail stays complete.

## Try it

```bash
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

1. Log in as `admin01` / `Admin@12` and open **Fees**. Arjun Rao (`CSE2201`) owes Rs. 50,000.
2. Open him, click **Record payment**, enter 20000, choose Online, save. The receipt opens; he is now Partially Paid
   with Rs. 30,000 outstanding.
3. Try 40000 (more than the balance), -500 and `abc`, and a blank mode. Each is refused with a message.
4. On the receipt page press Back and save again: the warning "already submitted" appears and no second payment is made.
5. Log in as `stu1023` / `Pass@123`, open **Fees & Payments**: the same status, balance, history and receipt.
6. As `admin01`, open **Outstanding dues report** from Fee Management, try *Overdue only* and *Download CSV*.

Run `python manage.py seed_data` afterwards to put Arjun's fee back to Rs. 50,000 unpaid (the seed only resets the fee,
so delete test payments in the admin site first if you want a fully clean start).

## Running the tests

```bash
python manage.py test fees                          # all fee tests
python scripts/update_test_matrix.py fees           # run them and fill in TEST_PLAN_MATRIX.md
```
