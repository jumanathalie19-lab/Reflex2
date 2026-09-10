```python
# ============================================================
# REFLEX QR CONFIRMATION
# ============================================================
#
# Handles QR confirmation for deliveries.
#
# Prototype behavior:
#   1. Rider must be logged in.
#   2. Delivery must belong to that rider.
#   3. Delivery must be PICKED_UP.
#   4. Demo QR code is REFLEX-DELIVERY.
#   5. Successful QR confirmation changes:
#
#          PICKED_UP -> DELIVERED
#
#   6. Every QR attempt is recorded in qr_confirmations.
#   7. Customer receives an SMS after successful delivery.
#
# ============================================================

from flask import Blueprint, jsonify, request, session
from psycopg2.extras import RealDictCursor

from db import get_connection
from auth import role_required
from statusendpoint import apply_transition
from sms_service import send_sms


# ============================================================
# BLUEPRINT
# ============================================================

qr_bp = Blueprint("qr", __name__)


# ============================================================
# DEMO QR CODE
# ============================================================

DEMO_QR_CODE = "REFLEX-DELIVERY"


# ============================================================
# CONFIRM DELIVERY USING QR CODE
# ============================================================

@qr_bp.route(
    "/deliveries/<int:delivery_id>/qr-confirm",
    methods=["POST"]
)
@role_required("Rider")
def qr_confirm(delivery_id):

    # --------------------------------------------------------
    # Get logged-in rider from Flask session
    # --------------------------------------------------------

    rider_id = session.get("user_id")

    if not rider_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    # --------------------------------------------------------
    # Read JSON request
    # --------------------------------------------------------

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    # --------------------------------------------------------
    # Get submitted QR code
    # --------------------------------------------------------

    submitted_code = str(
        body.get("qr_code", "")
    ).strip()

    if not submitted_code:
        return jsonify({
            "error": "qr_code is required"
        }), 400

    conn = None
    cur = None

    try:

        # ----------------------------------------------------
        # Connect to PostgreSQL
        # ----------------------------------------------------

        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # Find delivery
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                delivery_id,
                status,
                rider_id,
                qr_code,
                customer_phone,
                customer_name
            FROM deliveries
            WHERE delivery_id = %s
            LIMIT 1
            """,
            (delivery_id,)
        )

        delivery = cur.fetchone()

        # ----------------------------------------------------
        # Delivery does not exist
        # ----------------------------------------------------

        if delivery is None:
            return jsonify({
                "error": (
                    f"No delivery found with id "
                    f"{delivery_id}"
                )
            }), 404

        # ----------------------------------------------------
        # Make sure delivery belongs to logged-in rider
        # ----------------------------------------------------

        if str(delivery["rider_id"]) != str(rider_id):
            return jsonify({
                "error": (
                    "You are not assigned to this delivery"
                )
            }), 403

        # ----------------------------------------------------
        # QR confirmation only works for PICKED_UP
        # ----------------------------------------------------

        if delivery["status"] != "PICKED_UP":
            return jsonify({
                "error": (
                    "Cannot QR-confirm a delivery with "
                    f"status '{delivery['status']}'. "
                    "Delivery must be PICKED_UP first."
                )
            }), 409

        # ----------------------------------------------------
        # Validate demo QR code
        # ----------------------------------------------------

        stored_code = delivery["qr_code"]

        is_match = (
            stored_code is not None
            and str(stored_code).strip().upper()
            == DEMO_QR_CODE
            and submitted_code.upper()
            == DEMO_QR_CODE
        )

        # ----------------------------------------------------
        # Determine scan result
        # ----------------------------------------------------

        result = (
            "Successful"
            if is_match
            else "Failed"
        )

        # ----------------------------------------------------
        # Record QR attempt
        # ----------------------------------------------------

        cur.execute(
            """
            INSERT INTO qr_confirmations
                (
                    delivery_id,
                    qr_code,
                    scanned_by,
                    result
                )
            VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """,
            (
                delivery_id,
                submitted_code,
                rider_id,
                result
            )
        )

        # ----------------------------------------------------
        # Invalid QR code
        # ----------------------------------------------------

        if not is_match:

            conn.commit()

            return jsonify({
                "error": (
                    "Invalid demo QR code. "
                    "Use REFLEX-DELIVERY."
                ),
                "result": "fail"
            }), 409

        # ----------------------------------------------------
        # Successful QR confirmation
        #
        # PICKED_UP -> DELIVERED
        # ----------------------------------------------------

        apply_transition(
            cur,
            delivery_id,
            rider_id,
            "DELIVERED"
        )

        # ----------------------------------------------------
        # Save database transaction
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # Send customer SMS
        # ----------------------------------------------------

        sms_result = send_sms(
            delivery["customer_phone"],
            (
                f"Hi {delivery['customer_name']}, your Reflex "
                f"delivery has been confirmed as delivered. "
                f"Thank you!"
            )
        )

        # ----------------------------------------------------
        # Return success
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "delivery_id": delivery_id,
            "previous_status": "PICKED_UP",
            "status": "DELIVERED",
            "result": "success",
            "message": "Delivery confirmed successfully",
            "sms": sms_result
        }), 200

    except Exception as error:

        if conn:
            conn.rollback()

        print(
            "QR confirmation error:",
            error
        )

        return jsonify({
            "success": False,
            "error": "Unable to process QR confirmation",
            "message": str(error)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
```
