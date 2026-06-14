# 🏥 Clinexa AI — Setup, Run & Extend Guide
*by JillaniSofTech*

This guide covers how to run the project cleanly, which files changed in this
enhancement, and exactly how to expand the data.

---

## 1. Where each file goes

```
clinexa-ai/
├── agents/
│   ├── booking_agent.py          # unchanged
│   └── save_langgraph_flow.py    # unchanged
├── data/
│   ├── db.py                     # ⬅ REPLACE with the new db.py
│   └── clinic.db                 # auto-upgrades on first run (see §4)
├── services/
│   ├── booking_service.py        # unchanged
│   └── doctor_service.py         # ⬅ REPLACE with the new doctor_service.py
├── ui/
│   └── chat_ui.py                # unchanged
├── app.py                        # unchanged
├── requirements.txt              # ⬅ add
├── .env                          # ⬅ create from .env.example
└── index.html                    # ⬅ standalone showcase UI (run separately)
```

The two Python files to swap in are `data/db.py` and `services/doctor_service.py`.
Everything else keeps working as-is.

---

## 2. Run the app (Streamlit)

```bash
# from the project root
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env                 # then paste your real OpenAI key into .env

streamlit run app.py
```

The database is created and seeded automatically on first run — no manual step.

> Always run from the **project root** (`streamlit run app.py`), not from inside
> a subfolder. The imports use `from data.db import …` / `from services… import …`,
> which only resolve from the root.

---

## 3. Run the showcase UI (`index.html`)

This is a self-contained front end for screenshots and demos — no server needed.

- **Just double-click `index.html`** (opens in any browser), or
- serve it locally for a cleaner URL:
  ```bash
  python -m http.server 8000
  # open http://localhost:8000/index.html
  ```

It mirrors the real roster (60 doctors, 9 specialities) and the same profile
numbers the app generates, so screenshots match the running product.

---

## 4. The database upgrade is automatic

The `doctors` table gained six new columns
(`experience_years`, `rating`, `consultation_fee`, `qualification`,
`languages`, `room_no`).

On startup, `init_db()` checks whether your `clinic.db` already has the new
columns. If it has the old 4-column schema, it rebuilds **only the doctors
table** (static seed data) and reseeds 60 doctors. Your `customers` and
`bookings` rows are never touched.

So you do **not** need to delete `clinic.db` — but if you ever want a clean
slate, deleting it and re-running is perfectly safe.

---

## 5. Common issues & fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: data` / `services` | Ran from a subfolder | Run `streamlit run app.py` from the project root |
| `openai.AuthenticationError` | Missing/invalid key | Put a valid `OPENAI_API_KEY` in `.env` |
| `sqlite3.OperationalError: no such column` | Old `clinic.db` from another tool | Handled automatically now; if it persists, delete `data/clinic.db` and rerun |
| Icons missing in `index.html` | n/a | Icons are inlined as SVG — they render offline, no CDN needed |
| Streamlit shows a blank doctor list | DB not seeded | Run `python data/db.py` once to seed manually |

---

## 6. What's expandable (and how)

Everything below lives in **`data/db.py`** unless noted.

**Add a new doctor**
Append a row to `SEED_DOCTORS`:
```python
("D61", "Dr. Sana Iqbal", "Cardiologist", "09:00-13:00"),
```
The rating, experience, fee, qualification, languages and room are generated
automatically from the doctor id — nothing else to fill in.

**Add a new speciality**
1. Add an entry to `SPECIALITY_META` (its base fee + qualification):
   ```python
   "Urologist": {"fee": 70, "qual": "MBBS, FCPS (Urology)"},
   ```
2. Add some doctors for it in `SEED_DOCTORS`.
3. (Showcase UI) add a matching `{name, icon, fee, qual}` line to
   `SPECIALITIES` inside `index.html` and pick an icon id from the sprite
   (e.g. `stethoscope`).

**Change how profiles are generated**
Edit `_enrich()` in `db.py` — e.g. widen the experience range or change the
fee logic. It's pure, deterministic, and used for every doctor.

**Add a brand-new column** (e.g. `next_available`)
1. Add it to the `CREATE TABLE doctors` statement and to `DOCTOR_COLUMNS`.
2. Return it from `_enrich()` (and add it to the `INSERT` column list).
3. Surface it in `services/doctor_service.py` → `_to_dict()`.
Because `init_db()` detects the schema change, the table rebuilds itself.

---

## 7. Do the other Python files need changes? (No)

- `services/booking_service.py` — **no change.** It only reads
  `doctor_id`, `office_timing`, etc., which still exist.
- `agents/booking_agent.py` — **no change required.** The richer fields are now
  in the doctor dict, so you *can* show them in chat if you like (optional):

  In `select_date_node`, replace the `title = (...)` block with:
  ```python
  title = (
      f"Great! **{doctor['doctor_name']}** ({speciality}) is available.\n\n"
      f"⭐ {doctor.get('rating','—')}  ·  🧑‍⚕️ {doctor.get('experience_years','—')} yrs exp  ·  "
      f"💵 {doctor.get('fee_display','—')}  ·  🏠 Room {doctor.get('room_no','—')}\n\n"
      f"Which date works for you?\n"
      f"- **Today** ({today_s})\n"
      f"- **Tomorrow** ({tom_s})"
  )
  ```
  Safe to skip — it's purely cosmetic for the Streamlit chat.

- `ui/chat_ui.py`, `app.py`, tests, `save_langgraph_flow.py` — **no change.**

---

*Clinexa AI · 60 doctors · 9 specialities · LangGraph + GPT-4o-mini · JillaniSofTech*