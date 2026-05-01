"""SQLite database setup and operations for the clinic booking system."""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "clinic.db")


def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize the database with tables and sample data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id TEXT PRIMARY KEY,
            doctor_name TEXT NOT NULL,
            speciality TEXT NOT NULL,
            office_timing TEXT NOT NULL
        )
    """)
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)
    
    # Create bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    """)
    
    # Insert sample doctors if not exists
    doctors = [
        ("D1", "Dr. John Smith", "General Physician", "10:00-14:00"),
        ("D2", "Dr. Emily Johnson", "Dermatologist", "11:00-16:00"),
        ("D3", "Dr. Michael Brown", "Orthopedic", "09:00-13:00"),
        ("D4", "Dr. Sarah Davis", "Pediatrician", "10:00-15:00"),
        ("D5", "Dr. David Wilson", "ENT Specialist", "12:00-17:00"),

        ("D6", "Dr. James Anderson", "Cardiologist", "08:00-12:00"),
        ("D7", "Dr. Olivia Thomas", "Neurologist", "10:00-14:00"),
        ("D8", "Dr. Daniel Taylor", "General Physician", "09:00-13:00"),
        ("D9", "Dr. Sophia Moore", "Gynecologist", "11:00-15:00"),
        ("D10", "Dr. Matthew Jackson", "Orthopedic", "13:00-18:00"),

        ("D11", "Dr. Isabella Martin", "Dermatologist", "10:00-14:00"),
        ("D12", "Dr. Christopher Lee", "Cardiologist", "12:00-16:00"),
        ("D13", "Dr. Ava Perez", "Pediatrician", "09:00-13:00"),
        ("D14", "Dr. Andrew White", "ENT Specialist", "11:00-15:00"),
        ("D15", "Dr. Mia Harris", "Neurologist", "14:00-18:00"),

        ("D16", "Dr. Joshua Clark", "General Physician", "08:00-12:00"),
        ("D17", "Dr. Charlotte Lewis", "Gynecologist", "10:00-14:00"),
        ("D18", "Dr. Benjamin Walker", "Orthopedic", "09:00-13:00"),
        ("D19", "Dr. Amelia Hall", "Dermatologist", "12:00-16:00"),
        ("D20", "Dr. Elijah Allen", "Cardiologist", "13:00-17:00"),

        ("D21", "Dr. Harper Young", "Pediatrician", "10:00-15:00"),
        ("D22", "Dr. Alexander King", "ENT Specialist", "11:00-16:00"),
        ("D23", "Dr. Evelyn Wright", "Neurologist", "09:00-13:00"),
        ("D24", "Dr. Henry Scott", "General Physician", "12:00-16:00"),
        ("D25", "Dr. Abigail Green", "Gynecologist", "10:00-14:00"),

        ("D26", "Dr. Sebastian Adams", "Orthopedic", "08:00-12:00"),
        ("D27", "Dr. Ella Baker", "Dermatologist", "11:00-15:00"),
        ("D28", "Dr. Jack Nelson", "Cardiologist", "09:00-13:00"),
        ("D29", "Dr. Scarlett Carter", "Pediatrician", "13:00-17:00"),
        ("D30", "Dr. Leo Mitchell", "ENT Specialist", "10:00-14:00"),

        ("D31", "Dr. Grace Perez", "Neurologist", "12:00-16:00"),
        ("D32", "Dr. Wyatt Roberts", "General Physician", "09:00-13:00"),
        ("D33", "Dr. Chloe Turner", "Gynecologist", "11:00-15:00"),
        ("D34", "Dr. Julian Phillips", "Orthopedic", "10:00-14:00"),
        ("D35", "Dr. Lily Campbell", "Dermatologist", "08:00-12:00"),

        ("D36", "Dr. Nathan Parker", "Cardiologist", "13:00-18:00"),
        ("D37", "Dr. Zoey Evans", "Pediatrician", "10:00-15:00"),
        ("D38", "Dr. Aaron Edwards", "ENT Specialist", "11:00-16:00"),
        ("D39", "Dr. Hannah Collins", "Neurologist", "09:00-13:00"),
        ("D40", "Dr. Caleb Stewart", "General Physician", "12:00-17:00"),

        ("D41", "Dr. Nora Sanchez", "Gynecologist", "10:00-14:00"),
        ("D42", "Dr. Isaac Morris", "Orthopedic", "08:00-12:00"),
        ("D43", "Dr. Victoria Rogers", "Dermatologist", "11:00-15:00"),
        ("D44", "Dr. Owen Reed", "Cardiologist", "09:00-13:00"),
        ("D45", "Dr. Penelope Cook", "Pediatrician", "13:00-17:00"),

        ("D46", "Dr. Lucas Bennett", "General Physician", "09:00-13:00"),
        ("D47", "Dr. Aria Foster", "Dermatologist", "10:00-14:00"),
        ("D48", "Dr. Mason Gray", "Orthopedic", "12:00-16:00"),
        ("D49", "Dr. Ella Simmons", "Pediatrician", "08:00-12:00"),
        ("D50", "Dr. Logan Hughes", "ENT Specialist", "11:00-15:00"),

        ("D51", "Dr. Avery Price", "Cardiologist", "13:00-17:00"),
        ("D52", "Dr. Ethan Hayes", "Neurologist", "09:00-13:00"),
        ("D53", "Dr. Scarlett Myers", "Gynecologist", "10:00-14:00"),
        ("D54", "Dr. Jack Long", "General Physician", "12:00-16:00"),

    ]
    
    for doctor in doctors:
        cursor.execute(
            "INSERT OR IGNORE INTO doctors (doctor_id, doctor_name, speciality, office_timing) VALUES (?, ?, ?, ?)",
            doctor
        )
    
    conn.commit()
    conn.close()


def get_all_doctors():
    """Get all doctors from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    conn.close()
    return doctors


def get_doctor_by_speciality(speciality):
    """Get doctor by speciality."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM doctors WHERE LOWER(speciality) = LOWER(?)",
        (speciality,)
    )
    doctor = cursor.fetchone()
    conn.close()
    return doctor


def get_doctors_by_speciality(speciality: str) -> list[tuple]:
    """
    Return ALL doctors for a given speciality.
    Replaces fetchone() so random selection works across 50+ doctors.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM doctors WHERE LOWER(speciality) = LOWER(?)",
        (speciality,)
    )
    doctors = cursor.fetchall()
    conn.close()
    return doctors

def get_doctor_by_id(doctor_id):
    """Get doctor by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctors WHERE doctor_id = ?", (doctor_id,))
    doctor = cursor.fetchone()
    conn.close()
    return doctor


def create_customer(customer_id, name, phone):
    """Create a new customer."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (customer_id, name, phone) VALUES (?, ?, ?)",
        (customer_id, name, phone)
    )
    conn.commit()
    conn.close()


def get_customer_by_phone(phone):
    """Get customer by phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE phone = ?", (phone,))
    customer = cursor.fetchone()
    conn.close()
    return customer


def create_booking(booking_id, doctor_id, customer_id, appointment_date, appointment_time, status="Confirmed"):
    """Create a new booking."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (booking_id, doctor_id, customer_id, appointment_date, appointment_time, status) VALUES (?, ?, ?, ?, ?, ?)",
        (booking_id, doctor_id, customer_id, appointment_date, appointment_time, status)
    )
    conn.commit()
    conn.close()


def get_bookings_by_doctor_and_date(doctor_id, date_str):
    """Get all bookings for a doctor on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT appointment_time FROM bookings WHERE doctor_id = ? AND appointment_date = ? AND status = 'Confirmed'",
        (doctor_id, date_str)
    )
    bookings = cursor.fetchall()
    conn.close()
    return [b[0] for b in bookings]


def get_booking_by_id(booking_id):
    """Get booking by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    return booking


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")
