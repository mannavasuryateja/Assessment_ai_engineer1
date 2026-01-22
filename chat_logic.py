from app.booking_flow import (
    initialize_booking_state,
    next_question,
    update_state_from_input,
    booking_summary,
    get_missing_fields,
    HELP_TEXT,
    validate_field,
)
from app.tools import save_booking_tool, email_tool

MAX_MEMORY = 25


def initialize_chat_state():
    return {
        "messages": [],
        "booking_active": False,
        "booking_state": None,
        "awaiting_confirmation": False,
        "mode": "chat",  # "chat" or "booking"
    }


def add_message(state: dict, role: str, content: str):
    state["messages"].append({"role": role, "content": content})
    state["messages"] = state["messages"][-MAX_MEMORY:]


def detect_intent(message: str) -> str:
    """
    VERY STRICT booking detection.
    Booking starts ONLY when user explicitly asks to book.
    """
    message = message.lower().strip()

    booking_phrases = [
        "i want to book",
        "book a room",
        "reserve a room",
        "make a booking",
        "i want to reserve",
        "book hotel",
        "confirm booking",
        "start booking",
        "new booking",
        "how can i book room here",
        "help me book",
        
    ]

    for phrase in booking_phrases:
        if phrase in message:
            return "booking"

    return "general"


def detect_greeting(message: str) -> bool:
    """
    Detect if user is greeting the assistant.
    Returns True if greeting detected.
    """
    message = message.lower().strip()
    
    greetings = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "greetings", "welcome", "howdy", "hiya", "sup", "yo", "what's up",
        "hallo", "bonjour", "buenas", "namaste", "salaam", "habibi"
    ]
    
    for greeting in greetings:
        if greeting in message:
            return True
    
    return False


def generate_greeting_response(name: str = None) -> str:
    """
    Generate a professional hotel greeting response.
    """
    greeting_responses = [
        "Welcome to our Hotel Booking Assistant! 🏨 I'm here to assist you with room reservations, guest inquiries, and hotel information. How may I be of service today?",
        "Good day! Thank you for choosing our hotel. I'm delighted to assist you with your booking needs or any questions about our properties and amenities.",
        "Warm greetings! Welcome to our hospitality service. Whether you're looking to make a reservation or learn more about our facilities, I'm at your service.",
        "Hello and welcome! 🎉 Thank you for visiting our booking service. I'm ready to help you secure the perfect room or answer any questions you may have.",
        "Greetings! It's a pleasure to assist you. As your hotel concierge assistant, I'm here to facilitate your reservation and ensure your stay is exceptional."
    ]
    
    import random
    response = random.choice(greeting_responses)
    
    if name:
        return f"Wonderful to meet you, {name}! {response}"
    return response


def generate_formal_response(topic: str = None) -> str:
    """
    Generate formal, hotel-related responses when information is not available.
    """
    formal_responses = {
        "default": "I appreciate your inquiry. Unfortunately, I don't have specific information on that topic in our current database. I recommend contacting our guest services team directly for comprehensive assistance with your request.",
        "amenities": "I apologize, but the specific details about that amenity are not available in our system. Please contact our front desk, and they will be delighted to provide you with detailed information about our facilities.",
        "pricing": "Regarding pricing inquiries, I don't have access to real-time rate information. I encourage you to speak with our reservations team who can provide you with accurate quotes and current promotions.",
        "availability": "To check real-time room availability and rates, please contact our reservations department directly, or I can assist you in starting a booking with us.",
        "policies": "For detailed information about our policies, I recommend reaching out to our guest services or administrative team. They will be happy to clarify any policies concerning your stay.",
        "services": "That specific service information is not available in my current database. Our guest relations team would be the ideal contact to provide you with complete details about all our offerings.",
    }
    
    if topic and topic in formal_responses:
        return formal_responses[topic]
    return formal_responses["default"]


def detect_exit_command(user_input: str) -> str:
    """
    Detect if user wants to exit booking or switch mode.
    Returns: "documents", "exit", "help", "restart", or None
    """
    user_lower = user_input.lower().strip()
    
    if user_lower in ["back", "exit", "quit", "cancel"]:
        return "exit"
    elif user_lower in ["documents", "info", "raag", "rag", "hotel info", "details"]:
        return "documents"
    elif user_lower == "help":
        return "help"
    elif user_lower in ["restart", "start over", "begin again"]:
        return "restart"
    
    return None


def handle_user_message(state: dict, user_input: str):
    """
    Enhanced booking logic with dynamic switching.
    Returns:
    - string → booking handled
    - None   → let RAG handle
    """

    # Always store user message
    add_message(state, "user", user_input)

    user_lower = user_input.lower().strip()

    # =====================================================
    # GREETING DETECTION (greet the user when they greet first)
    # =====================================================
    if detect_greeting(user_input):
        greeting_response = generate_greeting_response()
        add_message(state, "assistant", greeting_response)
        return greeting_response

    # =====================================================
    # COMMAND PROCESSING (works at ANY stage)
    # =====================================================
    exit_cmd = detect_exit_command(user_input)
    
    if exit_cmd == "exit":
        state["booking_active"] = False
        state["awaiting_confirmation"] = False
        state["booking_state"] = None
        state["mode"] = "chat"
        
        response = "✋ Exited booking mode. How can I help you? (You can still ask about hotels or start a new booking)"
        add_message(state, "assistant", response)
        return response
    
    if exit_cmd == "documents":
        if state["booking_active"]:
            response = "📚 Let me search the hotel documents for you..."
            add_message(state, "assistant", response)
            return None  # Let RAG handle
        else:
            response = "📚 Let me search the hotel documents for you..."
            add_message(state, "assistant", response)
            return None
    
    if exit_cmd == "help":
        response = HELP_TEXT
        add_message(state, "assistant", response)
        return response
    
    if exit_cmd == "restart":
        state["booking_active"] = True
        state["booking_state"] = initialize_booking_state()
        state["awaiting_confirmation"] = False
        state["mode"] = "booking"
        
        question = next_question(state["booking_state"])
        add_message(state, "assistant", question)
        return question

    # =====================================================
    # ESCAPE HATCH: Questions during booking
    # =====================================================
    if state["booking_active"] and "?" in user_input:
        response = "🔍 Let me look that up from the hotel documents..."
        add_message(state, "assistant", response)
        return None  # RAG will handle this

    # =====================================================
    # START BOOKING
    # =====================================================
    if not state["booking_active"]:
        intent = detect_intent(user_input)

        if intent == "booking" and "?" not in user_input:
            state["booking_active"] = True
            state["booking_state"] = initialize_booking_state()
            state["awaiting_confirmation"] = False
            state["mode"] = "booking"

            question = next_question(state["booking_state"])
            response = f"{question}\n\n💡 *Type **documents** anytime to see hotel info or **help** for commands*"
            add_message(state, "assistant", response)
            return response

        # Not booking intent → let RAG answer
        return None

    # =====================================================
    # CONFIRMATION STAGE
    # =====================================================
    if state["awaiting_confirmation"]:
        if user_lower == "confirm":
            booking_id = save_booking_tool(state["booking_state"])
            guest_email = state["booking_state"]["email"]  # Save email before clearing state

            email_result = email_tool(
                guest_email,
                booking_id,
                state["booking_state"],
            )

            state["booking_active"] = False
            state["awaiting_confirmation"] = False
            state["booking_state"] = None
            state["mode"] = "chat"

            if email_result:
                response = f"✅ **Booking confirmed!** Your booking ID is **{booking_id}**\n📧 Confirmation email sent to {guest_email}"
            else:
                response = f"✅ **Booking confirmed!** Your booking ID is **{booking_id}**\n⚠️ Email delivery pending - check your inbox"
            add_message(state, "assistant", response)
            return response

        if user_lower == "cancel" or user_lower == "back":
            state["booking_active"] = False
            state["awaiting_confirmation"] = False
            state["booking_state"] = None
            state["mode"] = "chat"

            response = "❌ Booking cancelled. How can I help you?"
            add_message(state, "assistant", response)
            return response

        response = "⚠️ Please type **confirm** to book or **cancel** to exit."
        add_message(state, "assistant", response)
        return response

    # =====================================================
    # COLLECT BOOKING DETAILS WITH VALIDATION
    # =====================================================
    current_field = state["booking_state"].get("current_field")
    
    if not current_field:
        # No field to collect yet
        question = next_question(state["booking_state"])
        add_message(state, "assistant", question)
        return question

    # Validate the input for current field
    is_valid, error_msg, state_updated = update_state_from_input(
        state["booking_state"], user_input
    )

    if not is_valid:
        # Invalid input - show error and re-ask
        response = f"{error_msg}\n\n🔄 Please try again."
        add_message(state, "assistant", response)
        return response

    # Valid input - move to next field
    missing = get_missing_fields(state["booking_state"])
    
    if missing:
        # More fields needed
        question = next_question(state["booking_state"])
        response = f"✅ Got it!\n\n{question}"
        add_message(state, "assistant", response)
        return response

    # All fields collected - show summary
    summary = booking_summary(state["booking_state"])
    state["awaiting_confirmation"] = True
    add_message(state, "assistant", summary)
    return summary
