"""Service layer for booking operations · Clinexa AI · JillaniSofTech"""

import uuid
from datetime import datetime
from data.db import (
    create_customer,
    create_booking,
    get_customer_by_phone,
    get_bookings_by_doctor_and_date,
    get_booking_by_id,
)
from services.doctor_service import generate_time_slots, parse_time_slot


def get_or_create_customer(name: str, phone: str) -> str:
    """Return existing customer_id or create a new customer."""
    customer = get_customer_by_phone(phone)
    if customer:
        return customer[0]
    customer_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    create_customer(customer_id, name, phone)
    return customer_id


def get_available_slots(
    doctor_id: str,
    office_timing: str,
    appointment_date: str | None = None,
) -> list[str]:
    """
    Return slots not yet booked for a doctor on a specific date.

    Previously hardcoded today's date — now uses the date passed from
    the booking state (selected_date), defaulting to today only as fallback.
    """
    date = appointment_date or datetime.now().strftime("%Y-%m-%d")
    all_slots    = generate_time_slots(office_timing)
    booked_times = get_bookings_by_doctor_and_date(doctor_id, date)  # list of "HH:MM"

    return [
        slot for slot in all_slots
        if parse_time_slot(slot) not in booked_times
    ]


def confirm_booking(
    doctor_id: str,
    customer_name: str,
    customer_phone: str,
    time_slot: str,
    appointment_date: str | None = None,
) -> str:
    """
    Create customer (if new) and insert a confirmed booking row.
    Returns the generated booking ID.
    """
    customer_id      = get_or_create_customer(customer_name, customer_phone)
    booking_id       = f"BKG-{uuid.uuid4().hex[:6].upper()}"
    date             = appointment_date or datetime.now().strftime("%Y-%m-%d")
    appointment_time = parse_time_slot(time_slot)

    create_booking(booking_id, doctor_id, customer_id, date, appointment_time)
    return booking_id


def get_booking_details(booking_id: str) -> dict | None:
    """Return booking details dict or None."""
    booking = get_booking_by_id(booking_id)
    if not booking:
        return None
    return {
        "booking_id":       booking[0],
        "doctor_id":        booking[1],
        "customer_id":      booking[2],
        "appointment_date": booking[3],
        "appointment_time": booking[4],
        "status":           booking[5],
    }