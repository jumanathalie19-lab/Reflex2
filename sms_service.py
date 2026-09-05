
# ============================================================
# REFLEX SMS SERVICE
# ============================================================
#
# This is currently a development/testing SMS service.
#
# It does NOT send real SMS messages.
# Instead, it prints the message to the Flask terminal.
#
# Later, this function can be connected to a real SMS provider
# such as Africa's Talking without changing the delivery
# endpoints that call send_sms().
#
# ============================================================


def send_sms(phone_number, message):
    """
    Simulate sending an SMS message.

    Args:
        phone_number (str):
            Customer's phone number.

        message (str):
            SMS message to send.

    Returns:
        dict:
            Information about the simulated SMS.
    """

    # Make sure the values are strings
    phone_number = str(phone_number).strip()
    message = str(message).strip()

    # Basic validation
    if not phone_number:
        print("[SMS STUB] ERROR: Phone number is missing.")

        return {
            "status": "failed",
            "to": phone_number,
            "message": message,
            "error": "Phone number is required"
        }

    if not message:
        print("[SMS STUB] ERROR: Message is empty.")

        return {
            "status": "failed",
            "to": phone_number,
            "message": message,
            "error": "Message is required"
        }

    # --------------------------------------------------------
    # DEVELOPMENT SMS OUTPUT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("[REFLEX SMS STUB]")
    print(f"To      : {phone_number}")
    print(f"Message : {message}")
    print("Status  : SMS simulated successfully")
    print("=" * 60)
    print()

    # Return useful information to the calling endpoint
    return {
        "status": "stubbed",
        "to": phone_number,
        "message": message
    }

