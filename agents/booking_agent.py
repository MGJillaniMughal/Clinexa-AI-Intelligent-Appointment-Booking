"""Clinexa AI · Appointment Booking — LangGraph booking agent · JillaniSofTech"""

import os
from typing import TypedDict, Annotated, List, Optional, cast
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from services.doctor_service import get_specialities_list, get_doctor_info, generate_time_slots
from services.booking_service import confirm_booking

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL          = "gpt-4o-mini"
HISTORY_WINDOW = 6          # messages kept for routing/guardrail context
MAX_RETRIES    = 2          # LLM call retries on exception

SYSTEM_BASE = (
    "You are Clinexa AI · Appointment Booking, an intelligent medical appointment booking assistant "
    "for a modern multi-specialty clinic. You are built by JillaniSofTech "
    "(https://jillanisoftech.com/). Be concise, warm, and professional."
)

# ── State ─────────────────────────────────────────────────────────────────────
class BookingState(TypedDict):
    messages:             List[dict]
    stage:                str
    selected_speciality:  Optional[str]
    selected_doctor:      Optional[dict]
    selected_date:        Optional[str]
    selected_slot:        Optional[str]
    customer_name:        Optional[str]
    customer_phone:       Optional[str]
    booking_id:           Optional[str]
    available_options:    List[str]
    last_interrupt_message: Optional[str]
    retry_count:          int          # tracks per-node retry attempts


def create_initial_state() -> BookingState:
    return {
        "messages":              [],
        "stage":                 "greeting",
        "selected_speciality":   None,
        "selected_doctor":       None,
        "selected_date":         None,
        "selected_slot":         None,
        "customer_name":         None,
        "customer_phone":        None,
        "booking_id":            None,
        "available_options":     [],
        "last_interrupt_message": None,
        "retry_count":           0,
    }


# ── LLM helper ────────────────────────────────────────────────────────────────
def call_llm(
    system_prompt: str,
    user_prompt:   str,
    *,
    model:       str   = MODEL,
    temperature: float = 0.0,
    max_tokens:  int   = 60,
) -> str:
    """Centralized, retry-aware LLM caller."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = (resp.choices[0].message.content or "").strip()
            return content
        except Exception as e:
            print(f"[LLM] attempt {attempt+1} failed: {e}")
    return ""


def _snippet(messages: List[dict], k: int = HISTORY_WINDOW) -> str:
    """Return last-k messages as a formatted string for LLM context."""
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in messages[-k:]
    )


# ── Guardrail ─────────────────────────────────────────────────────────────────
STAGE_CONTEXT = {
    "greeting":          "booking a medical appointment",
    "select_speciality": "choosing a medical speciality",
    "select_doctor":     "assigning a doctor",
    "select_date":       "choosing an appointment date",
    "select_slot":       "choosing an appointment time slot",
    "confirm":           "confirming an appointment",
    "collect_details":   "collecting patient details for the appointment",
}

def is_on_topic(snippet: str, stage: str) -> bool:
    if not snippet:
        return True
    ctx = STAGE_CONTEXT.get(stage, "booking a medical appointment")
    result = call_llm(
        system_prompt=(
            "You are an intent classifier for a medical clinic booking system.\n"
            "Respond ONLY with 'yes' if the user is discussing medical topics, symptoms, "
            "doctors, appointment details, dates, times, or their name/phone.\n"
            "Respond ONLY with 'no' if completely off-topic (politics, sports, finance, etc.)."
        ),
        user_prompt=(
            f"Current context: {ctx}\n\n"
            f"Recent conversation:\n{snippet}\n\n"
            "On-topic for a clinic booking?"
        ),
        max_tokens=5,
    )
    return result.strip().lower() == "yes"


# ── Routing ───────────────────────────────────────────────────────────────────
VALID_ROUTES: dict[str, set] = {
    "greeting":          {"greeting", "select_speciality", "cancelled"},
    "select_speciality": {"select_speciality", "select_doctor"},
    "select_doctor":     {"select_date"},
    "select_date":       {"select_date", "select_slot"},
    "select_slot":       {"select_slot", "confirm"},
    "confirm":           {"confirm", "collect_details", "cancelled", "select_slot", "select_speciality"},
    "collect_details":   {"collect_details", "completed"},
}

def llm_router(state: BookingState) -> str:
    stage    = state.get("stage", "greeting")
    messages = state.get("messages", [])
    snippet  = _snippet(messages)

    # ── Fast-path state-based bypasses ──
    if stage == "select_speciality" and state.get("selected_speciality"):
        return "select_doctor"
    if stage == "select_date" and state.get("selected_date"):
        return "select_slot"
    if stage == "select_slot" and state.get("selected_slot"):
        return "confirm"

    # ── Fast-path keyword check for confirm (avoids LLM confusion with emoji buttons) ──
    if stage == "confirm" and messages:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        clean = last_user.lower().replace("✅","").replace("❌","").replace("🔄","").strip()
        if any(kw in clean for kw in ["confirm", "yes", "ok", "sure", "proceed", "book", "go ahead"]):
            return "collect_details"
        if any(kw in clean for kw in ["cancel", "no", "stop", "don't", "nope"]):
            return "cancelled"
        if any(kw in clean for kw in ["change slot", "different slot", "another slot", "reschedule"]):
            return "select_slot"
        if any(kw in clean for kw in ["another doctor", "different doctor", "change doctor", "other doctor", "another specialist", "switch doctor"]):
            return "select_speciality"

    # ── Off-topic guardrail ──
    if messages and not is_on_topic(snippet, stage):
        redirect = call_llm(
            system_prompt=(
                f"{SYSTEM_BASE}\n"
                "When users go off-topic, politely redirect them back to the booking flow. "
                "1-2 sentences max."
            ),
            user_prompt=f"User went off-topic:\n{snippet}\nRedirect response:",
            max_tokens=60,
        ) or "I can only help with clinic bookings. Shall we continue with your appointment?"
        state["messages"].append({"role": "assistant", "content": redirect})
        return stage

    # ── Stage-specific routing prompts ──
    prompts = {
        "greeting": (
            f"Conversation:\n{snippet}\n\n"
            "Does the user want to book an appointment or continue?\n"
            "Reply ONLY: 'select_speciality' | 'cancelled' | 'greeting'"
        ),
        "select_speciality": (
            f"Conversation:\n{snippet}\n"
            f"State speciality: {state.get('selected_speciality') or 'None'}\n\n"
            "Has a valid speciality been identified?\n"
            "Reply ONLY: 'select_doctor' | 'select_speciality'"
        ),
        "select_date": (
            f"Conversation:\n{snippet}\n"
            f"State date: {state.get('selected_date') or 'None'}\n\n"
            "Has a date been chosen?\n"
            "Reply ONLY: 'select_slot' | 'select_date'"
        ),
        "select_slot": (
            f"Conversation:\n{snippet}\n"
            f"State slot: {state.get('selected_slot') or 'None'}\n\n"
            "Has a time slot been chosen?\n"
            "Reply ONLY: 'confirm' | 'select_slot'"
        ),
        "confirm": (
            f"User's latest response:\n{snippet}\n\n"
            "Does the user confirm, cancel, or want to change the slot?\n"
            "Reply ONLY: 'collect_details' | 'cancelled' | 'select_slot' | 'confirm'"
        ),
    }

    if stage not in prompts:
        return stage

    raw = call_llm(
        system_prompt="You are a routing classifier. Always reply with ONLY the exact route name.",
        user_prompt=prompts[stage],
        max_tokens=20,
    )
    route = raw.strip().lower().strip("'\"")
    valid = VALID_ROUTES.get(stage, {stage})
    if route not in valid:
        print(f"[Router] Invalid route '{route}' for '{stage}'. Valid: {valid}")
        return stage
    return route


# ── Nodes ─────────────────────────────────────────────────────────────────────
def greeting_node(state: BookingState) -> BookingState:
    state["stage"] = "greeting"
    default_msg    = "👋 Welcome to Clinexa AI by JillaniSofTech! Would you like to book an appointment?"

    if state["messages"] and state["messages"][-1]["role"] == "user":
        snippet = _snippet(state["messages"], k=2)
        reply   = call_llm(
            system_prompt=(
                f"{SYSTEM_BASE} "
                "Respond naturally to the user's greeting, introduce yourself as Clinexa AI, "
                "and ask if they'd like to book an appointment. 1-2 sentences."
            ),
            user_prompt=f"Conversation:\n{snippet}\nAssistant:",
            max_tokens=80,
        )
        if reply:
            default_msg = reply

    if not state["messages"] or state["messages"][-1]["role"] != "assistant":
        state["messages"].append({
            "role": "assistant",
            "content": default_msg,
            "options": ["Book Appointment"],
        })

    user_input = interrupt({
        "role": "assistant",
        "content": default_msg,
        "available_options": ["Book Appointment"],
    })
    state["messages"].append({"role": "user", "content": user_input})
    return state


def select_speciality_node(state: BookingState) -> BookingState:
    state["stage"] = "select_speciality"
    specialities   = get_specialities_list()
    msg            = "Please choose a medical speciality:"

    last = state["messages"][-1]["content"] if state["messages"] else ""
    if last != msg and "didn't recognize" not in last.lower():
        state["messages"].append({
            "role": "assistant",
            "content": msg,
            "options": specialities,
        })

    raw = interrupt({
        "role": "assistant",
        "content": msg,
        "available_options": specialities,
    })

    extracted = call_llm(
        system_prompt="Extract information precisely. Return ONLY the match or 'UNKNOWN'.",
        user_prompt=(
            f'Extract the medical speciality from: "{raw}"\n'
            f"Available: {', '.join(specialities)}\n"
            "Return ONLY the exact name from the list or 'UNKNOWN'."
        ),
        max_tokens=30,
    )

    selected = next(
        (s for s in specialities
         if s.lower() in extracted.lower() or extracted.lower() in s.lower()),
        None
    )

    if selected:
        state["selected_speciality"] = selected
        state["messages"].append({"role": "user", "content": raw})
        state["retry_count"] = 0
    else:
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["messages"].append({
            "role": "assistant",
            "content": (
                f"I didn't recognise that speciality. Please choose from:\n"
                f"{', '.join(specialities)}"
            ),
            "options": specialities,
        })
    return state


def select_doctor_node(state: BookingState) -> BookingState:
    speciality = state["selected_speciality"] or ""
    doctor     = get_doctor_info(speciality)

    if not doctor:
        state["messages"].append({
            "role": "assistant",
            "content": f"Sorry, no doctor is available for **{speciality}** right now. Please choose another speciality.",
            "options": get_specialities_list(),
        })
        state["stage"] = "select_speciality"
        state["selected_speciality"] = None
        return state

    state["selected_doctor"] = doctor
    state["stage"]           = "select_date"
    return state


def select_date_node(state: BookingState) -> BookingState:
    state["stage"] = "select_date"
    doctor         = state.get("selected_doctor")
    speciality     = state.get("selected_speciality")

    if not doctor or not speciality:
        state["stage"] = "select_speciality"
        return state

    today    = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_s  = today.strftime("%Y-%m-%d")
    tom_s    = tomorrow.strftime("%Y-%m-%d")
    dates    = ["Today", "Tomorrow"]

    title = (
        f"Great! **{doctor['doctor_name']}** ({speciality}) is available.\n\n"
        f"Which date works for you?\n"
        f"- **Today** ({today_s})\n"
        f"- **Tomorrow** ({tom_s})"
    )

    if not state["messages"] or state["messages"][-1]["content"] != title:
        state["messages"].append({"role": "assistant", "content": title, "options": dates})

    raw = interrupt({
        "role": "assistant",
        "content": title,
        "available_options": dates,
    })

    if "today" in raw.lower():
        selected = today_s
    elif "tomorrow" in raw.lower():
        selected = tom_s
    else:
        extracted = call_llm(
            system_prompt="Extract dates from text. Return ONLY YYYY-MM-DD or 'UNKNOWN'.",
            user_prompt=(
                f'Extract date from: "{raw}"\n'
                f"Today={today_s}, Tomorrow={tom_s}\n"
                "Reply ONLY with YYYY-MM-DD or 'UNKNOWN'."
            ),
            max_tokens=20,
        )
        selected = None if extracted.upper() == "UNKNOWN" else extracted

    if selected:
        state["selected_date"] = selected
        state["messages"].append({"role": "user", "content": raw})
        state["retry_count"] = 0
    else:
        state["messages"].append({
            "role": "assistant",
            "content": "I couldn't understand the date. Please select **Today** or **Tomorrow**.",
            "options": dates,
        })
    return state


def select_slot_node(state: BookingState) -> BookingState:
    state["stage"] = "select_slot"
    doctor         = state.get("selected_doctor")

    if not doctor:
        state["messages"].append({"role": "assistant", "content": "Please select a doctor first."})
        return state

    slots   = generate_time_slots(doctor["office_timing"])
    message = f"Please pick an available time slot for **{state.get('selected_date', 'your chosen date')}**:"

    if not state["messages"] or state["messages"][-1]["content"] != message:
        state["messages"].append({"role": "assistant", "content": message, "options": slots})

    raw = interrupt({
        "role": "assistant",
        "content": message,
        "available_options": slots,
    })

    extracted = call_llm(
        system_prompt="Extract time slots. Return ONLY the exact match or 'UNKNOWN'.",
        user_prompt=(
            f'Extract time slot from: "{raw}"\n'
            f"Available: {', '.join(slots)}\n"
            "Reply ONLY with the exact slot string or 'UNKNOWN'."
        ),
        max_tokens=20,
    )

    selected = next((s for s in slots if s.lower() in extracted.lower()), None)

    if selected:
        state["selected_slot"] = selected
        state["messages"].append({"role": "user", "content": raw})
        state["retry_count"] = 0
    else:
        state["messages"].append({
            "role": "assistant",
            "content": "I didn't catch that. Which time slot would you prefer?",
            "options": slots,
        })
    return state


def confirm_node(state: BookingState) -> BookingState:
    state["stage"] = "confirm"
    doctor = state.get("selected_doctor", {})
    slot   = state.get("selected_slot", "—")
    date   = state.get("selected_date", "Today")

    if not doctor or not slot:
        state["messages"].append({
            "role": "assistant",
            "content": "Some appointment details are missing. Let's start the slot selection again.",
        })
        return state

    message = (
        f"📋 **Appointment Summary**\n\n"
        f"| | |\n|---|---|\n"
        f"| 👨‍⚕️ Doctor      | {doctor.get('doctor_name', '—')} |\n"
        f"| 🩺 Speciality   | {doctor.get('speciality', '—')} |\n"
        f"| 📅 Date         | {date} |\n"
        f"| ⏰ Time         | {slot} |\n\n"
        f"Would you like to **confirm** this appointment?"
    )
    options = ["✅ Confirm", "❌ Cancel", "🔄 Change Slot"]

    if not state["messages"] or state["messages"][-1].get("content") != message:
        state["messages"].append({"role": "assistant", "content": message, "options": options})

    choice = interrupt({
        "role": "assistant",
        "content": message,
        "available_options": options,
    })
    state["messages"].append({"role": "user", "content": choice})
    return state


def collect_details_node(state: BookingState) -> BookingState:
    state["stage"] = "collect_details"

    # ── Name ──
    msg_name = "Almost done! 🎉 Please enter your **full name**:"
    if not state["messages"] or state["messages"][-1]["content"] != msg_name:
        state["messages"].append({"role": "assistant", "content": msg_name})
    name = interrupt(msg_name)
    state["messages"].append({"role": "user", "content": name})

    # ── Phone ──
    msg_phone = "Please enter your **phone number** (for booking confirmation):"
    if state["messages"][-1]["content"] != msg_phone:
        state["messages"].append({"role": "assistant", "content": msg_phone})
    phone = interrupt(msg_phone)
    state["messages"].append({"role": "user", "content": phone})

    state["customer_name"]  = name
    state["customer_phone"] = phone
    state["stage"]          = "completed"
    return state


def completed_node(state: BookingState) -> BookingState:
    state["stage"] = "completed"
    doctor = state["selected_doctor"]
    if not doctor:
        raise ValueError("selected_doctor missing in completed_node")

    booking_id = confirm_booking(
        doctor_id=doctor["doctor_id"],
        customer_name=state["customer_name"] or "",
        customer_phone=state["customer_phone"] or "",
        time_slot=state["selected_slot"] or "",
        appointment_date=state["selected_date"],
    )
    state["booking_id"] = booking_id

    message = (
        f"🎉 **Appointment Confirmed!**\n\n"
        f"| | |\n|---|---|\n"
        f"| 🔖 Booking ID   | `{booking_id}` |\n"
        f"| 👨‍⚕️ Doctor      | {doctor['doctor_name']} |\n"
        f"| 🩺 Speciality   | {doctor['speciality']} |\n"
        f"| 📅 Date         | {state['selected_date']} |\n"
        f"| ⏰ Time         | {state['selected_slot']} |\n"
        f"| 🙋 Patient      | {state['customer_name']} |\n\n"
        f"Thank you for choosing **Clinexa AI** by JillaniSofTech. "
        f"We'll see you soon! 💙"
    )
    state["messages"].append({"role": "assistant", "content": message})
    state["available_options"] = []
    return state


def cancelled_node(state: BookingState) -> BookingState:
    state["messages"].append({
        "role": "assistant",
        "content": (
            "Your booking has been cancelled. No worries — you can start a new "
            "booking anytime by clicking **Start New Booking** or typing 'hi'.\n\n"
            "_Clinexa AI by JillaniSofTech_ 💙"
        ),
        "options": ["Book Again"],
    })
    state["available_options"] = ["Book Again"]
    state["stage"] = "cancelled"
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────
def build_booking_graph():
    wf = StateGraph(BookingState)

    wf.add_node("greeting",          greeting_node)
    wf.add_node("select_speciality", select_speciality_node)
    wf.add_node("select_doctor",     select_doctor_node)
    wf.add_node("select_date",       select_date_node)
    wf.add_node("select_slot",       select_slot_node)
    wf.add_node("confirm",           confirm_node)
    wf.add_node("collect_details",   collect_details_node)
    wf.add_node("completed",         completed_node)
    wf.add_node("cancelled",         cancelled_node)

    wf.set_entry_point("greeting")

    wf.add_conditional_edges("greeting",          llm_router,
        {"greeting": "greeting", "select_speciality": "select_speciality", "cancelled": "cancelled"})
    wf.add_conditional_edges("select_speciality", llm_router,
        {"select_speciality": "select_speciality", "select_doctor": "select_doctor"})
    wf.add_edge("select_doctor", "select_date")
    wf.add_conditional_edges("select_date",       llm_router,
        {"select_date": "select_date", "select_slot": "select_slot"})
    wf.add_conditional_edges("select_slot",       llm_router,
        {"select_slot": "select_slot", "confirm": "confirm"})
    wf.add_conditional_edges("confirm", llm_router,
        {"confirm": "confirm", "collect_details": "collect_details",
         "cancelled": "cancelled", "select_slot": "select_slot",
         "select_speciality": "select_speciality"})
    wf.add_edge("collect_details", "completed")
    wf.add_edge("completed",       END)
    wf.add_edge("cancelled",       END)

    return wf.compile(checkpointer=MemorySaver())


booking_graph = build_booking_graph()


# ── Public API ────────────────────────────────────────────────────────────────
def process_message(
    state: BookingState,
    user_message: str,
    thread_id: str = "default_session",
) -> BookingState:
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    current = booking_graph.get_state(config)

    if current.tasks and current.tasks[0].interrupts:
        result = booking_graph.invoke(Command(resume=user_message), config=config)
    else:
        if user_message.lower() != "hi" or state["messages"]:
            last_content = state["messages"][-1].get("content") if state["messages"] else None
            if last_content != user_message:
                state["messages"].append({"role": "user", "content": user_message})
        result = booking_graph.invoke(state, config=config)

    # ── Sync interrupt payload into result ──
    snapshot = booking_graph.get_state(config)
    if snapshot.tasks and snapshot.tasks[0].interrupts:
        iv = snapshot.tasks[0].interrupts[0].value

        msg_content: str  = iv.get("content", "")  if isinstance(iv, dict) else str(iv)
        options:     list = iv.get("available_options", []) if isinstance(iv, dict) else []

        if msg_content:
            last = result["messages"][-1].get("content", "") if result["messages"] else ""
            if last != msg_content:
                result["messages"].append({
                    "role": "assistant",
                    "content": msg_content,
                    "options": options,
                })
            else:
                result["messages"][-1]["options"] = options

        result["available_options"] = options
    else:
        result.setdefault("available_options", [])

    return cast(BookingState, result)