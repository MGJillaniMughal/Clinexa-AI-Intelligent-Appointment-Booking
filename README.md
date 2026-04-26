# 🏥 Clinexa AI — Intelligent Appointment Booking
### by [JillaniSofTech](https://jillanisoftech.com/) · Built with LangGraph + OpenAI + Streamlit

> **Clinexa AI** is a production-grade, conversational appointment booking agent for modern multi-specialty clinics. It combines LangGraph state machines, GPT-4o-mini LLM routing, and a real-time Streamlit UI to deliver an agentic booking experience from greeting to confirmed appointment — entirely through natural conversation.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 Conversational Booking | Full end-to-end booking via natural language |
| 🧠 LLM-Only Routing | GPT-4o-mini handles all intent classification & entity extraction — zero regex |
| 🔀 LangGraph State Machine | Robust multi-node agentic graph with interrupt/resume pattern |
| 🩺 Multi-Specialty Support | 54 doctors across 9 specialities with random doctor assignment |
| 📅 Date-Aware Slots | Slot availability checked per doctor per selected date |
| 🛡️ Off-Topic Guardrail | LLM-based guardrail redirects non-medical conversations |
| 💬 Session History | Past bookings and conversations saved in sidebar |
| 👨‍⚕️ Doctor Availability | Live availability indicator per doctor for today |
| 🗃️ SQLite Persistence | All bookings, customers and doctors stored in local DB |
| 🎨 Agentic Dark UI | Claude/ChatGPT-style dark UI with progress tracker |

---

## 🗂️ Project Structure

```
clinexa-ai/
├── agents/
│   ├── booking_agent.py           # LangGraph agent — nodes, routing, state
│   └── save_langgraph_flow.py     # Export LangGraph graph as PNG
├── data/
│   ├── clinic.db                  # SQLite database (auto-created)
│   └── db.py                      # All DB operations
├── services/
│   ├── booking_service.py         # Booking logic — slot availability, confirm
│   └── doctor_service.py          # Doctor lookup, time slot generation
├── test/
│   ├── test_agent.py              # Agent unit tests
│   └── test_service.py            # Service unit tests
├── ui/
│   └── chat_ui.py                 # Streamlit UI — sidebar, chat, session history
├── app.py                         # Entry point
├── requirements.txt               # Python dependencies
├── .env                           # API keys (never commit this)
└── README.md
```

---

## ⚙️ Setup

### 1. Clone & install
```bash
git clone https://github.com/yourrepo/clinexa-ai.git
cd clinexa-ai
pip install -r requirements.txt
```

### 2. Configure environment
```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run
```bash
streamlit run app.py
```
The app auto-initializes the SQLite database on first run.

---

## 🔄 Conversation Flow

```
User says "Hi"
    │
    ▼
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Greeting  │────▶│ Select Speciality│────▶│ Select Doctor │
└─────────────┘     └──────────────────┘     └───────┬───────┘
                                                      │
                    ┌─────────────────────────────────▼──────┐
                    │             Select Date                  │
                    └─────────────────────────────────┬───────┘
                                                      │
          ┌───────────────────────┐         ┌────────▼───────┐
          │   Collect Details     │◀────────│  Select Slot   │
          └───────────┬───────────┘         └────────┬───────┘
                      │                              │
                      │                    ┌─────────▼──────┐
                      │                    │    Confirm      │
                      │                    └─────────────────┘
                      ▼
              ┌───────────────┐
              │   Completed   │  ──▶  Booking ID saved to DB
              └───────────────┘
```

---

## 🧠 LLM Architecture

### Routing (`llm_router`)
Every node transition is decided by GPT-4o-mini with stage-specific prompts. A deterministic **keyword fast-path** runs before the LLM for critical transitions (e.g. confirm/cancel) to prevent misrouting.

### Guardrail (`is_on_topic`)
A lightweight LLM classifier checks if user input is on-topic for the current booking stage. Off-topic messages get a polite redirect without breaking the flow.

### Entity Extraction
Each node uses a dedicated extraction prompt to pull structured values (speciality name, date, time slot) from free-form user input, with fallback handling for unrecognised values.

---

## 🗄️ Database Schema

```sql
-- Doctors (54 pre-seeded across 9 specialities)
doctors (doctor_id, doctor_name, speciality, office_timing)

-- Auto-created on booking
customers (customer_id, name, phone)

-- Each confirmed appointment
bookings (booking_id, doctor_id, customer_id,
          appointment_date, appointment_time, status)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph 0.2+ |
| LLM | OpenAI GPT-4o-mini |
| UI | Streamlit |
| Database | SQLite via `sqlite3` |
| State Checkpointing | LangGraph `MemorySaver` |
| Env Management | `python-dotenv` |

---

## 🚀 Roadmap

- [ ] Multi-doctor selection UI (let user pick from all doctors in a speciality)
- [ ] SMS / Email confirmation via Twilio / SendGrid
- [ ] Admin dashboard — view all bookings, cancel, reschedule
- [ ] LoRA fine-tuned routing model to replace GPT-4o-mini
- [ ] Docker deployment config
- [ ] Persistent session storage (PostgreSQL / Redis)

---

## 👤 Built by JillaniSofTech

**JillaniSofTech** specializes in production-grade AI systems — RAG pipelines, LangGraph agents, LLM integrations, and enterprise automation.

- 🌐 [jillanisoftech.com](https://jillanisoftech.com/)
- 💼 [LinkedIn](https://www.linkedin.com/in/jillanisofttech/)
- ⭐ Top Rated Plus on Upwork · 20+ Production AI Deployments
