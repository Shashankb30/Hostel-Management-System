# Architecture Diagram

Layered, modular monolith (Python / Django). Draft: compare with the submitted SAD and record any difference as a deviation.

## 1. High-level architecture

```mermaid
flowchart TB
    subgraph Users
        S[Student]
        W[Warden]
        A[Administrator]
    end

    subgraph Presentation["Presentation layer"]
        T[Django templates + Bootstrap]
        N[Role-based navigation]
    end

    subgraph Application["Application layer: one Django app per SRS module"]
        L[accounts<br/>FR-01 Login]
        ST[students<br/>FR-02]
        R[rooms<br/>FR-03]
        AL[allocation<br/>FR-04]
        F[fees<br/>FR-05]
        C[complaints<br/>FR-06]
        AT[attendance<br/>FR-07]
        V[visitors<br/>FR-08]
        LV[leave<br/>FR-09]
        NO[notices<br/>FR-10]
        CO[core<br/>hostel + notification service]
    end

    subgraph Data["Data layer"]
        ORM[Django ORM + migrations]
        DB[(SQLite / PostgreSQL)]
    end

    CI[GitHub Actions<br/>check, migrations, tests]

    S --> T
    W --> T
    A --> T
    T --> N
    T --> L
    T --> ST
    T --> R
    T --> AL
    T --> F
    T --> C
    T --> AT
    T --> V
    T --> LV
    T --> NO

    AL --> R
    AL --> ST
    F --> ST
    C --> ST
    AT --> ST
    V --> ST
    LV --> ST

    AL -. notify .-> CO
    F -. notify .-> CO
    LV -. notify .-> CO
    NO -. notify .-> CO

    L --> ORM
    ST --> ORM
    R --> ORM
    AL --> ORM
    F --> ORM
    C --> ORM
    AT --> ORM
    V --> ORM
    LV --> ORM
    NO --> ORM
    CO --> ORM
    ORM --> DB

    CI -. tests every PR .-> Application
```

## 2. Request flow (example: allocate a room)

```mermaid
sequenceDiagram
    actor Warden
    participant UI as Template / View
    participant Svc as allocation service
    participant DB as Database
    participant Ntf as core.notify

    Warden->>UI: Select student and vacant room
    UI->>Svc: allocate(student, room)
    Svc->>DB: Check room is available and not full (locked transaction)
    DB-->>Svc: OK
    Svc->>DB: Create ACTIVE allocation
    Svc->>Ntf: notify(student, "Room allocated")
    Ntf->>DB: Save notification
    Svc-->>UI: Success
    UI-->>Warden: Confirmation message
```

## 3. Roles and access

| Role | Main modules |
|---|---|
| Student | Own room, own fees, complaints, leave, notices |
| Warden | Room allocation, attendance, visitors, leave approval, complaints, notices |
| Administrator | Students, rooms, fees, visitors, accounts, reports |

## 4. Design rules

1. Business rules live in each app's service layer, not in the views.
2. Modules interact through services and foreign keys only.
3. Every hostel-owned record carries a `hostel_id` (NFR-07).
4. Role checks use Django groups and permission decorators (NFR-01).
5. Database constraints back up every validation rule (NFR-05).
