# Crown Resorts Consult Failure — Workflow

**Interaction:** `351cc6b4-f189-4383-96bb-5fc235e6d22b`  
**Correlation:** `484961fc-1ef1-4a9b-9a54-89faba6c5f47`  
**Date:** 2026-07-09 05:13–05:27 UTC (15:13–15:27 AEST)

---

## 1. End-to-end incident workflow

```mermaid
flowchart TB
    subgraph Agent["Agent (Muralidharan)"]
        A1[Answers inbound call<br/>ANI 00410036402]
        A2[Clicks CONSULT → Dial Number 5927]
        A3[Waits ~10 min in consult UI]
        A4[Clicks TRANSFER ×3]
        A5[Clicks END CONSULT ×3]
        A6[Clicks CONFERENCE ×2]
        A7[Clicks RESUME — manual workaround]
    end

    subgraph Desktop["Agent Desktop"]
        D1[POST consult → DN 5927]
        D2[Receives AgentConsultCreated<br/>leg 6d35d7ca DN]
        D3[Receives AgentConsultCreated<br/>leg 0886edac EP-DN]
        D4[Transfer payload: to=empty]
        D5[POST consult/end → 202<br/>blocks 20s for AgentConsultEnded]
        D6[EndConsultError ×3<br/>Service.aqm.reqs.Timeout]
        D7[Conference payload: missing .to]
        D8[POST resume → customer unheld]
    end

    subgraph Routing["routing-api"]
        R1[Accept consult to 5927]
        R2[EP-DN remap → +61392925927]
        R3[Accept consult/end ×3 → 202]
        R4[Reject consult/transfer ×4 → 400<br/>empty to parameter]
        R5[Reject consult/conference ×2 → 400<br/>missing .to field]
    end

    subgraph UR["flowcontrol / UR"]
        U1[Create DN consult leg 6d35d7ca]
        U2[SIP 404 from CUCM on 5927]
        U3[Create EP-DN leg 0886edac<br/>GSC_CROWN_GIFTS_2025]
        U4[ConsultEnd closes 6d35d7ca only<br/>ConversationEnded wrong leg]
        U5[consultState stays consulting<br/>0886edac remains active]
        U6[AgentConsultEnded NOT generated]
    end

    subgraph Notifs["notifs / websocket"]
        N1[Deliver AgentConsultCreated ×2]
        N2[Deliver ContactUpdated]
        N3[No AgentConsultEnded delivered]
    end

    subgraph CUCM["Crown CUCM 10.80.2.69"]
        C1[No dial-peer for bare 5927]
        C2[Return SIP 404]
        C3[Accept outbound +61392925927]
    end

    subgraph Customer["Customer"]
        CU1[Connected to agent]
        CU2[Auto-held at consult start]
        CU3[On hold ~12 min]
        CU4[Resumed at 05:26:11]
    end

    A1 --> D1 --> R1 --> U1 --> C1 --> C2
    C2 --> U2
    U2 --> R2 --> U3 --> C3
    U3 --> N1 --> D2
    R2 --> N1 --> D3
    U1 --> CU2 --> CU3

    A4 --> D4 --> R4
    A5 --> D5 --> R3 --> U4 --> U5 --> U6
    U6 --> N3 --> D6
    A6 --> D7 --> R5
    A7 --> D8 --> CU4

    style U6 fill:#f96,stroke:#333
    style D6 fill:#f96,stroke:#333
    style R4 fill:#fc9,stroke:#333
    style CU3 fill:#f96,stroke:#333
```

---

## 2. Consult initiation workflow (5927 → EP-DN remap)

```mermaid
sequenceDiagram
    autonumber
    participant Agent
    participant Desktop
    participant Routing as routing-api
    participant UR as flowcontrol/UR
    participant CUCM as Crown CUCM
    participant Notifs
    participant Customer

    Agent->>Desktop: CONSULT → Dial Number 5927
    Desktop->>Routing: POST /consult {to: 5927, type: DN}
    Routing->>UR: Initiate DN consult
    UR->>Customer: Auto-hold customer
    UR->>CUCM: Dial 5927
    CUCM-->>UR: SIP 404 UNSUPPORTED_DESTINATION
    UR-->>Notifs: AgentConsultCreated (leg 6d35d7ca, DN, dest=5927)
    Notifs-->>Desktop: AgentConsultCreated

    Note over UR,CUCM: ~48s later — EP-DN remap (flag wxcc_consult_to_entry_point_dn=ON)

    UR->>UR: Map 5927 → EP 7a358913… → +61392925927
    UR->>CUCM: Dial +61392925927
    CUCM-->>UR: Call accepted → GSC_CROWN_GIFTS_2025 IVR
    UR-->>Notifs: AgentConsultCreated (leg 0886edac, EP-DN)
    Notifs-->>Desktop: AgentConsultCreated (2nd event)

    Note over UR: Zombie leg 6d35d7ca NOT torn down<br/>Active leg 0886edac in queue/IVR
```

---

## 3. Desktop freeze workflow (End Consult)

```mermaid
flowchart TD
    Start([Agent clicks END CONSULT]) --> POST[Desktop POST consult/end]
    POST --> HTTP202{HTTP 202 Accepted?}
    HTTP202 -->|Yes| Block[UI blocks — wait for websocket<br/>AgentConsultEnded]
    HTTP202 -->|No| FailHTTP[Show HTTP error]

    Block --> Wait20[Wait up to ~20 seconds]
    Wait20 --> Event{AgentConsultEnded<br/>received?}

    Event -->|Yes| Success[Exit consult UI<br/>Resume normal controls]
    Event -->|No — all 3 attempts| Timeout[EndConsultError<br/>Service.aqm.reqs.Timeout]

    Timeout --> Stuck[UI remains in consult state<br/>Buttons still broken]
    Stuck --> Retry{Agent retries?}
    Retry -->|End Consult again| Start
    Retry -->|Transfer| T400[HTTP 400 — empty to]
    Retry -->|Conference| C400[HTTP 400 — missing .to]
    Retry -->|Resume| Resume[Customer unheld<br/>but consult state may persist]

    subgraph Backend["Why event never arrives"]
        B1[routing-api publishes ConsultEnd]
        B2[flowcontrol ends wrong leg 6d35d7ca]
        B3[Active leg 0886edac stays up]
        B4[consultState = consulting]
        B5[AgentConsultEnded never generated]
        B1 --> B2 --> B3 --> B4 --> B5
    end

    Block -.-> B1
    B5 -.-> Event

    style Timeout fill:#f96,stroke:#333
    style Stuck fill:#f96,stroke:#333
    style B5 fill:#f96,stroke:#333
```

---

## 4. Agent recovery attempts workflow (05:24–05:27)

```mermaid
flowchart LR
    subgraph Attempts["Agent actions (AEST)"]
        T1["15:24:21 TRANSFER"]
        T2["15:24:46 TRANSFER"]
        E1["15:24:49 END CONSULT #1"]
        E2["15:25:25 END CONSULT #2"]
        T3["15:25:48 TRANSFER"]
        R1["15:26:10 RESUME"]
        C1["15:26:18 CONFERENCE"]
        C2["15:26:24 CONFERENCE"]
        E3["15:26:26 END CONSULT #3"]
    end

    subgraph Results["Outcome"]
        F1["400 — empty to<br/>aa17f729"]
        F2["400 — empty to<br/>8a89ec03"]
        F3["20s freeze → timeout<br/>e54f6f04"]
        F4["20s freeze → timeout<br/>ffc38fd4"]
        F5["400 — empty to<br/>f60fe17f"]
        F6["Customer unheld ✓"]
        F7["400 — missing .to<br/>9e5647da"]
        F8["400 — missing .to<br/>f8ae05f0"]
        F9["20s freeze → timeout<br/>9b85370c"]
    end

    T1 --> F1
    T2 --> F2
    E1 --> F3
    E2 --> F4
    T3 --> F5
    R1 --> F6
    C1 --> F7
    C2 --> F8
    E3 --> F9
```

---

## 5. Dual consult leg state workflow

```mermaid
stateDiagram-v2
    [*] --> ActiveCall: Agent answers inbound

    ActiveCall --> CustomerHeld: Consult started 05:13:55

    CustomerHeld --> DNConsult: Leg 6d35d7ca created<br/>dest=5927, type=DN
    DNConsult --> DNFailed: CUCM SIP 404

    DNFailed --> EPConsult: EP remap 05:14:43<br/>Leg 0886edac created<br/>dest=+61392925927, type=EP-DN

    state DNConsult {
        [*] --> Zombie: 6d35d7ca
        Zombie --> ZombieDead: SIP 404 but NOT cleaned up
    }

    state EPConsult {
        [*] --> Active: 0886edac
        Active --> InIVR: Crown Gifts queue/IVR
    }

    EPConsult --> ConsultEndAttempt: Agent End Consult ×3

    ConsultEndAttempt --> WrongLegClosed: flowcontrol ends 6d35d7ca only
    WrongLegClosed --> StuckConsulting: 0886edac still active<br/>consultState=consulting

    StuckConsulting --> DesktopFreeze: No AgentConsultEnded<br/>UI blocked 20s per click

    StuckConsulting --> ManualResume: Agent clicks RESUME 05:26:10
    ManualResume --> CustomerActive: Customer off hold
    CustomerActive --> StuckConsulting: Consult UI may still show consulting
```

---

## 6. Responsibility workflow (defect routing)

```mermaid
flowchart TD
    Incident([Consult failure + desktop freeze<br/>+ customer 12 min hold])

    Incident --> Q1{CUCM SIP 404<br/>on 5927?}
    Q1 -->|Yes| Crown[Crown env — dial-plan / dial-peer<br/>for short code 5927]
    Q1 -->|Triggers| Q2{Dual consult legs<br/>after EP remap?}

    Q2 -->|Yes| UR[PRIMARY: flowcontrol / UR<br/>- Clean zombie leg<br/>- End correct leg on ConsultEnd<br/>- Emit AgentConsultEnded]

    Q2 --> D1{Desktop empty to<br/>on transfer/conference?}
    D1 -->|Yes| Desktop[SECONDARY: Agent Desktop<br/>- Populate to for EP-DN consults<br/>- Don't block UI 20s on missing event<br/>- Recover UI on timeout]

    UR --> NotifsCheck[notifs: no defect —<br/>no input event to deliver]
    RoutingCheck[routing-api: no defect —<br/>accepted consult/end, rejected bad payloads]

    style UR fill:#f96,stroke:#333
    style Desktop fill:#fc9,stroke:#333
    style Crown fill:#ff9,stroke:#333
```

---

## Key identifiers

| Item | Value |
|------|-------|
| Interaction ID | `351cc6b4-f189-4383-96bb-5fc235e6d22b` |
| DN consult leg | `6d35d7ca-0ca2-4d21-9880-8a0a1926e68c` |
| EP-DN consult leg | `0886edac-9801-4174-b293-872d893445e0` |
| EP ID (Crown Gifts) | `7a358913-645d-4bb7-a1bd-91ed6cd2e0b2` |
| End Consult tracking | `e54f6f04`, `ffc38fd4`, `9b85370c` |
| Transfer 400 tracking | `aa17f729`, `8a89ec03`, `f60fe17f` |
