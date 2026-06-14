"""Service layer for doctor-related operations · Clinexa AI · JillaniSofTech"""

import random
from data.db import (
    get_all_doctors,
    get_doctors_by_speciality,
    get_doctor_by_id,
    CURRENCY,
)


def _to_dict(row: tuple) -> dict:
    """
    Map a doctors table row to a dict.
    Columns: doctor_id, doctor_name, speciality, office_timing,
             experience_years, rating, consultation_fee,
             qualification, languages, room_no
    Older 4-column rows are still handled gracefully.
    """
    base = {
        "doctor_id":     row[0],
        "doctor_name":   row[1],
        "speciality":    row[2],
        "office_timing": row[3],
    }
    if len(row) >= 10:
        base.update({
            "experience_years": row[4],
            "rating":           row[5],
            "consultation_fee": row[6],
            "fee_display":      f"{CURRENCY}{row[6]}",
            "qualification":    row[7],
            "languages":        row[8],
            "room_no":          row[9],
        })
    return base


def get_specialities_list():
    """Return unique specialities in insertion order."""
    doctors = get_all_doctors()
    return list(dict.fromkeys(doc[2] for doc in doctors))


def get_doctor_info(speciality: str) -> dict | None:
    """Return a RANDOM available doctor for the given speciality."""
    doctors = get_doctors_by_speciality(speciality)
    if not doctors:
        return None
    return _to_dict(random.choice(doctors))


def get_all_doctors_by_speciality(speciality: str) -> list[dict]:
    """Return ALL doctors for a speciality (used if you let the user pick)."""
    return [_to_dict(d) for d in get_doctors_by_speciality(speciality)]


def get_doctor_info_by_id(doctor_id: str) -> dict | None:
    """Get full doctor information by ID."""
    doctor = get_doctor_by_id(doctor_id)
    return _to_dict(doctor) if doctor else None


def generate_time_slots(office_timing: str) -> list[str]:
    """Generate hourly time slots from an office timing string e.g. '11:00-16:00'."""
    start_str, end_str = office_timing.split("-")
    start_hour = int(start_str.split(":")[0])
    end_hour   = int(end_str.split(":")[0])

    slots = []
    for hour in range(start_hour, end_hour):
        if hour < 12:
            slots.append(f"{hour}:00 AM")
        elif hour == 12:
            slots.append("12:00 PM")
        else:
            slots.append(f"{hour - 12}:00 PM")
    return slots


def parse_time_slot(slot_str: str) -> str:
    """Convert '1:00 PM' → '13:00' (24-hour format for DB storage)."""
    time_part, suffix = slot_str.split(" ")
    hour, minute = time_part.split(":")
    hour = int(hour)
    if suffix == "PM" and hour != 12:
        hour += 12
    elif suffix == "AM" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute}"