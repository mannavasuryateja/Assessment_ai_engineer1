import re
from datetime import datetime

REQUIRED_FIELDS = [
    "name",
    "email",
    "phone",
    "room_type",
    "check_in",
    "check_out"
]

VALID_ROOM_TYPES = ["standard", "deluxe", "suite"]

HELP_TEXT = """
💡 **Booking Help:**
- Type **back** or **exit** to go back to chat
- Type **documents** to see hotel info from RAG
- Type **help** to see available commands
- Type **restart** to start booking over
"""


def initialize_booking_state():
    return {
        "name": None,
        "email": None,
        "phone": None,
        "room_type": None,
        "check_in": None,
        "check_out": None,
        "confirmed": False,
        "current_field": None  # Track which field we're asking for
    }


def get_missing_fields(state: dict):
    return [field for field in REQUIRED_FIELDS if not state.get(field)]


def validate_name(value: str) -> tuple:
    """Validate name field. Returns (is_valid, error_message)"""
    value = value.strip()
    if len(value) < 2:
        return False, "❌ Name must be at least 2 characters."
    if not re.match(r"^[a-zA-Z\s'-]+$", value):
        return False, "❌ Name should only contain letters, spaces, hyphens, and apostrophes."
    return True, None


def validate_email(value: str) -> tuple:
    """Validate email field. Returns (is_valid, error_message)"""
    value = value.strip()
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, value):
        return False, "❌ Please enter a valid email address (e.g., user@example.com)."
    return True, None


def validate_phone(value: str) -> tuple:
    """Validate phone field. Returns (is_valid, error_message)"""
    value = value.strip()
    # Remove common separators
    phone_digits = re.sub(r"[\s\-\(\)\.+]", "", value)
    if not re.match(r"^\d{7,15}$", phone_digits):
        return False, "❌ Please enter a valid phone number (7-15 digits)."
    return True, None


def validate_room_type(value: str) -> tuple:
    """Validate room type field. Returns (is_valid, error_message)"""
    value = value.lower().strip()
    if value not in VALID_ROOM_TYPES:
        return False, f"❌ Invalid room type. Please choose: **Standard**, **Deluxe**, or **Suite**."
    return True, None


def validate_date(value: str) -> tuple:
    """Validate date field. Returns (is_valid, error_message)"""
    value = value.strip()
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True, None
    except ValueError:
        return False, "❌ Invalid date format. Please use **YYYY-MM-DD** (e.g., 2026-01-25)."


def validate_checkout_after_checkin(state: dict) -> tuple:
    """Validate that checkout is after checkin. Returns (is_valid, error_message)"""
    if state.get("check_in") and state.get("check_out"):
        checkin = datetime.strptime(state["check_in"], "%Y-%m-%d")
        checkout = datetime.strptime(state["check_out"], "%Y-%m-%d")
        if checkout <= checkin:
            return False, "❌ Check-out date must be after check-in date."
    return True, None


def validate_field(field: str, value: str, state: dict = None) -> tuple:
    """
    Validate a specific field.
    Returns (is_valid, error_message, cleaned_value)
    """
    validators = {
        "name": validate_name,
        "email": validate_email,
        "phone": validate_phone,
        "room_type": validate_room_type,
        "check_in": validate_date,
        "check_out": validate_date,
    }

    if field not in validators:
        return True, None, value

    is_valid, error = validators[field](value)
    
    if not is_valid:
        return False, error, None

    # Clean up the value
    if field == "room_type":
        cleaned = value.strip().lower()
    else:
        cleaned = value.strip()

    return True, None, cleaned


def next_question(state: dict):
    """Get the next question for missing fields"""
    missing = get_missing_fields(state)

    questions = {
        "name": "👤 May I have your full name?",
        "email": "📧 Please share your email address.",
        "phone": "📱 What is your phone number?",
        "room_type": "🏨 Which room would you like? (**Standard** / **Deluxe** / **Suite**)",
        "check_in": "📅 What is your check-in date? (Format: **YYYY-MM-DD**)",
        "check_out": "📅 What is your check-out date? (Format: **YYYY-MM-DD**)"
    }

    if missing:
        field = missing[0]
        state["current_field"] = field
        return questions[field]

    return None


def update_state_from_input(state: dict, user_input: str) -> tuple:
    """
    Update state with validated input.
    Returns (success, message, state)
    """
    current_field = state.get("current_field")
    
    if not current_field:
        return False, "No field to update.", state

    is_valid, error, cleaned = validate_field(current_field, user_input, state)
    
    if not is_valid:
        return False, error, state

    state[current_field] = cleaned

    # Special validation for checkout date
    if current_field == "check_out":
        is_valid_range, error = validate_checkout_after_checkin(state)
        if not is_valid_range:
            state[current_field] = None  # Reset invalid value
            return False, error, state

    return True, None, state


def booking_summary(state: dict):
    return f"""
✅ **Please confirm your booking details:**

👤 Name: {state['name']}
📧 Email: {state['email']}
📱 Phone: {state['phone']}
🏨 Room Type: {state['room_type'].capitalize()}
📅 Check-in: {state['check_in']}
📅 Check-out: {state['check_out']}

Type **confirm** to proceed or **cancel** to abort.
"""


def handle_confirmation(state: dict, user_input: str):
    if user_input.lower() == "confirm":
        state["confirmed"] = True
        return "✅ Booking confirmed. Processing your reservation..."
    elif user_input.lower() == "cancel":
        return "❌ Booking cancelled."
    return "Please type **confirm** or **cancel**."
