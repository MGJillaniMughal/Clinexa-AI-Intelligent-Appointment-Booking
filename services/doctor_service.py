"""Service layer for doctor-related operations · Clinexa AI · JillaniSofTech"""

import random
from data.db import get_all_doctors, get_doctors_by_speciality, get_doctor_by_id


def get_specialities_list():
    """Return unique specialities in insertion order."""
    doctors = get_all_doctors()
    return list(dict.fromkeys(doc[2] for doc in doctors))


def get_doctor_info(speciality: str) -> dict | None:
    """
    Return a RANDOM available doctor for the given speciality.
    Previously used fetchone() which always returned the same first doctor.
    """
    doctors = get_doctors_by_speciality(speciality)
    if not doctors:
        return None
    doctor = random.choice(doctors)
    return {
        "doctor_id":    doctor[0],
        "doctor_name":  doctor[1],
        "speciality":   doctor[2],
        "office_timing": doctor[3],
    }


def get_all_doctors_by_speciality(speciality: str) -> list[dict]:
    """Return ALL doctors for a speciality (used if you want user to pick)."""
    doctors = get_doctors_by_speciality(speciality)
    return [
        {
            "doctor_id":     d[0],
            "doctor_name":   d[1],
            "speciality":    d[2],
            "office_timing": d[3],
        }
        for d in doctors
    ]


def get_doctor_info_by_id(doctor_id: str) -> dict | None:
    """Get doctor information by ID."""
    doctor = get_doctor_by_id(doctor_id)
    if not doctor:
        return None
    return {
        "doctor_id":     doctor[0],
        "doctor_name":   doctor[1],
        "speciality":    doctor[2],
        "office_timing": doctor[3],
    }


def generate_time_slots(office_timing: str) -> list[str]:
    """Generate hourly time slots from office timing string e.g. '11:00-16:00'."""
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