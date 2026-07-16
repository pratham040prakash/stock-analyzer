# Interaction Investigator

**Vendor-agnostic contact center log investigation** — upload logs, get a unified timeline and evidence-backed RCA report.

Built for escalation engineers, NOC teams, and partners who today juggle Splunk exports, PCAP notes, and manual timestamp correlation.

> **Important if you work at a contact-center vendor:** Use only **exported, anonymized logs** on personal time. Do not use employer confidential data, internal APIs, or customer identifiers. Check your employer's Outside Business Activities policy before selling services.

## Quick start

```bash
cd interaction-investigator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional — for AI RCA
streamlit run app.py
```

Open http://localhost:8501 → click **Load demo sample** → **Investigate**.

## What it does

| Step | Output |
|------|--------|
| Upload / paste logs | Parses timestamps, errors, journey keywords |
| Timeline | Customer → Carrier → SBC → IVR → … → Disconnect |
| RCA | Ranked hypothesis + evidence + customer draft |
| Export | Markdown report for Jira / email |

**Without OpenAI:** rule-based RCA (still useful for demos).  
**With OpenAI:** structured AI reasoning on the timeline.

## LinkedIn sales playbook

### Positioning (use this on posts)

> I help contact center teams cut escalation time. Upload your interaction logs — get a unified timeline and RCA in minutes, not hours. Vendor-agnostic. No system access required.

### Offer ladder

| Offer | Price | Deliverable |
|-------|-------|-------------|
| **Free demo** | $0 | 15-min screen share on sample logs |
| **Single RCA** | $299–$499 | One interaction, report in 24h |
| **Starter pack** | $1,499/mo | 10 investigations + tool access |
| **Team license** | $499/seat/mo | Self-serve tool + email support |

### First 5 LinkedIn posts

1. **Pain post** — "Every escalation engineer opens 20 tabs. Here's the workflow I automated."
2. **Demo GIF** — screen record: demo sample → timeline → RCA export (30 sec)
3. **Before/after** — "2 hours manual correlation → 8 minutes with Interaction Investigator"
4. **FAQ** — "Works with any platform that exports text logs"
5. **CTA** — "DM me INTERESTED for a free sample RCA on anonymized logs"

### DM script

```
Thanks for reaching out. I run interaction log investigations for contact center teams.

Send (anonymized):
- interaction ID (optional)
- symptom in one sentence
- exported logs (.txt / .log)

I'll return a timeline + RCA report within 24h.
First sample: free. Ongoing: $X per incident or monthly pack.
```

### What NOT to post

- Real customer names, org IDs, or internal defect IDs  
- Screenshots from employer systems  
- "Built for Cisco WxCC" (keep it vendor-neutral publicly)

## Project layout

```
interaction-investigator/
  app.py                 # Streamlit UI
  investigator/
    parser.py            # Generic log parsing
    timeline.py          # Journey stages
    rca.py                 # Rule + optional AI RCA
    report.py              # Markdown export
  samples/demo_interaction.log
```

## Deploy (optional)

Host on Streamlit Community Cloud or a $5 VPS:

```bash
streamlit run app.py --server.port 8501
```

Gate with a simple password (Streamlit secrets) before taking paid customers.

## Roadmap (charge for these later)

- [ ] Splunk / JSON log format adapters
- [ ] PDF export with logo
- [ ] Multi-file correlation by interaction ID
- [ ] Similar-incident clustering
- [ ] Auth + Stripe billing

## License

Your choice when you productize — recommend proprietary for SaaS.
