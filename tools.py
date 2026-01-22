from database import (
    insert_customer,
    insert_booking,
)
from email_service import send_confirmation_email


def save_booking_tool(booking_state: dict):
    """
    Save confirmed booking into Supabase.
    """
    customer_id = insert_customer(
        name=booking_state["name"],
        email=booking_state["email"],
        phone=booking_state["phone"],
    )

    booking_id = insert_booking(
        customer_id=customer_id,
        room_type=booking_state["room_type"],
        check_in=booking_state["check_in"],
        check_out=booking_state["check_out"],
    )

    return booking_id


def email_tool(email: str, booking_id: str, booking_state: dict):
    return send_confirmation_email(
        to_email=email,
        booking_id=booking_id,
        booking_state=booking_state,
    )

