# CCPL Team Poll — Correct Format for Pollbot

The one-line `@pollbot create ...; team1; team2; ...` command **breaks** with 18 long names.
Use the **card wizard** instead (recommended).

---

## Step 1 — Start the wizard

In **CCPL space**, send exactly:

```
@pollbot create poll
```

Wait for Pollbot to post an **Adaptive Card** (form with buttons).

---

## Step 2 — Question (copy exactly)

```
Choose your CCPL team (select ONE only)
```

---

## Step 3 — Answers (add ONE per line / one field at a time)

Copy each line below as a **separate answer option** (do not paste all in one field):

```
Royal Ciscoians Bengaluru (RCB)
Slog Squad
Play Bold Xl
Aura Strikers
Cloud Chorus XI
Hit and Run
Data Warriors
Switch Hitters
The Dial-In XI
Sixco SuperStrikers
Sixco CC XI
Collab Ops Challengers
Cisco Super Kings (CSK)
Apex Strikers
Rising Stars
The Cluster XI
The Collab Knights
Collab Super Kings
```

**Rules:**
- No semicolons inside team names
- Use `Hit and Run` not `Hit & Run` (ampersand can break parsing)
- One team per answer field
- **Single answer only** (not multi-select)

---

## Step 4 — Publish settings

After the poll is created, send:

```
@pollbot public
```

```
@pollbot duration 72
```

---

## Step 5 — Announce (map short names if you used them)

If poll shows full team names, post:

```
🏏 TEAM SELECTION — vote in the poll above. Pick ONE team only.
Min 11 / Max 12 players per squad. Poll closes in 72 hours.
```

---

## If card wizard fails — use SHORT names (text command)

Only use this if the card UI does not work. **One message**, semicolons between items only:

```
@pollbot create Choose your CCPL team pick ONE; RCB; Slog Squad; Play Bold Xl; Aura Strikers; Cloud Chorus XI; Hit and Run; Data Warriors; Switch Hitters; Dial-In XI; Sixco SuperStrikers; Sixco CC XI; Collab Ops Challengers; CSK; Apex Strikers; Rising Stars; Cluster XI; Collab Knights; Collab Super Kings
```

Post this **team name key** right after the poll:

```
RCB = Royal Ciscoians Bengaluru | CSK = Cisco Super Kings | Dial-In XI = The Dial-In XI | Cluster XI = The Cluster XI | Collab Knights = The Collab Knights | Collab Super Kings = Collab Super Kings
```

---

## Common formatting mistakes

| Wrong | Right |
|-------|-------|
| Commas between options | Semicolons only (text command) OR one option per card field |
| All 18 teams in one paste block in card | Add each team as separate answer |
| `Hit & Run` | `Hit and Run` |
| Multiple questions in one text command | One poll per question |
| Forgetting `@pollbot` | Must @ mention the bot |

---

## Verify poll looks correct before announcing

Check the poll card shows:
- ✅ Clear question at top
- ✅ 18 separate clickable options
- ✅ Single-choice (radio buttons, not checkboxes)

If options look merged or cut off → `@pollbot stop` and recreate using card wizard.
