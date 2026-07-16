# CCPL Team Selection Poll — Webex Setup

## Step 1 — Add Pollbot to CCPL space

1. Open Webex → **Apps** (or App Hub)
2. Search **Pollbot** (Cisco official): https://apphub.webex.com/applications/pollbot-cisco-systems-12150-78220-99857
3. Click **Add to Space** → select **CCPL - Collab Cricket Premier League**
4. Confirm Pollbot appears in the space member list

---

## Step 2 — Create polls (3 polls in CCPL space)

Pollbot usually runs **one active poll at a time** per space. Create all three using `@pollbot create poll` (multi-question card), **or** run them one after another.

---

### Poll 1 — Team selection (required for all players)

```
@pollbot create poll
```

- **Question:** Choose your CCPL team (pick ONE)
- **Options:** All 18 team names (list below)
- **Single answer** · Public · 72 hours

**One-line alternative:**

```
@pollbot create Choose your CCPL team (pick ONE); Royal Ciscoians Bengaluru (RCB); Slog Squad; Play Bold Xl; Aura Strikers; Cloud Chorus XI; Hit & Run; Data Warriors; Switch Hitters; The Dial-In XI; Sixco SuperStrikers; Sixco CC XI; Collab Ops Challengers; Cisco Super Kings (CSK); Apex Strikers; Rising Stars; The Cluster XI; The Collab Knights; Collab Super Kings
```

---

### Poll 2 — Umpire interest (all space members)

```
@pollbot create poll
```

- **Question:** Are you interested in volunteering as a CCPL umpire?
- **Options:**
  - Yes — I can umpire on match days
  - Yes — occasionally / backup only
  - No — not interested in umpiring
- **Single answer** · Public · 72 hours

**One-line alternative:**

```
@pollbot create Are you interested in volunteering as a CCPL umpire?; Yes - I can umpire on match days; Yes - occasionally / backup only; No - not interested in umpiring
```

---

### Poll 3 — Volunteer activities (all space members)

```
@pollbot create poll
```

- **Question:** Which CCPL volunteer activities are you interested in? (pick all that apply — use multi-answer if available)
- **Options:**
  - Scoring / Scoreboard
  - Match logistics / Ground setup
  - Registration & check-in
  - Photography / Social media
  - Refreshments / Hospitality
  - Planning / Coordination support
  - Not interested in volunteering
- **Multi-answer if supported** · Public · 72 hours

**One-line alternative (single choice fallback):**

```
@pollbot create Which CCPL volunteer activity interests you most?; Scoring / Scoreboard; Match logistics / Ground setup; Registration & check-in; Photography / Social media; Refreshments / Hospitality; Planning / Coordination support; Not interested in volunteering
```

---

### Poll settings (after each poll)

```
@pollbot public
@pollbot duration 72
```

**Tip:** Use `@pollbot create poll` card UI to add **multiple questions in one poll** (team + umpire + volunteer) if you want everyone to answer all three at once.

---

## Squad size rules (mandatory)

| Rule | Detail |
|------|--------|
| **Minimum** | **11 members** per team (including captain) |
| **Maximum** | **12 members** per team — **only 1 extra** beyond minimum |
| **Playing XI** | 11 on field; 12th member is **one substitute only** |

**Pollbot cannot auto-block** when a team hits 12 — enforce after `@pollbot results` (see Step 4).

---

## Step 3 — Announcement (post before/after polls)

```
🏏 CCPL Polls are LIVE — please complete ALL polls below

1️⃣ Team selection — pick ONE team (min 11, max 12 per squad)
2️⃣ Umpire interest — let us know if you can help officiate
3️⃣ Volunteer activities — scoring, logistics, registration, etc.

📋 Squad rules
• Minimum: 11 members per team (including captain)
• Maximum: 12 members — only 1 substitute allowed

✅ Players — vote for your team in Poll 1
✅ Everyone — answer Poll 2 & 3 even if you are not playing
⏰ Polls close in 72 hours

Questions? Reply in this thread.
— Pratham
```

---

## Step 4 — After poll closes

```
@pollbot results
```

**Validation checklist (planning team + captains):**

| Team | Count | Status |
|------|-------|--------|
| (each team) | ___ | ✅ 11–12 · ⚠️ <11 · ❌ >12 |

- **< 11** → captain recruits or planning team assigns unassigned players
- **> 12** → move excess to teams that are under 11 (planning team decides)
- **11–12** → confirmed ✅

---

## 18 poll options (for manual card entry)

1. Royal Ciscoians Bengaluru (RCB)
2. Slog Squad
3. Play Bold Xl
4. Aura Strikers
5. Cloud Chorus XI
6. Hit & Run
7. Data Warriors
8. Switch Hitters
9. The Dial-In XI
10. Sixco SuperStrikers
11. Sixco CC XI
12. Collab Ops Challengers
13. Cisco Super Kings (CSK)
14. Apex Strikers
15. Rising Stars
16. The Cluster XI
17. The Collab Knights
18. Collab Super Kings

---

## Notes

- Pollbot is **not yet added** to CCPL space (checked 2026-07-16)
- Pollbot auto-includes **all space members** in group polls
- Each person can vote once (single choice)
- Cannot create poll via REST API without a hosted bot + webhooks
