
# ============================================================
# REFLEX QR CONFIRMATION
# PostgreSQL version
# ============================================================

from flask import Blueprint, request, jsonify, session
from psycopg2.extras import RealDictCursor

from db import get_connection
from statusendpoint import apply_transition
from sms import send_sms


qr_bp = Blueprint("qr", __name__)


# ------------------------------------------------------------
# DEMO QR CODE
# ------------------------------------------------------------
# For the project demo, every assigned delivery uses this QR.
# The value is checked in this file but is NOT stored in the
# qr_confirmations table.
DEMO_QR_CODE = "REFLEX-DELIVERY"


# ------------------------------------------------------------
# CONFIRM QR CODE
# ------------------------------------------------------------
@qr_bp.route(
    "/deliveries/<int:delivery_id>/qr-confirm",
    methods=["POST"]
)
def confirm_qr(delivery_id):

    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------
    rider_id = session.get("user_id")
    role = session.get("role")

    if not rider_id:
        return jsonify({
            "success": False,
            "message": "You must be logged in."
        }), 401

    if role != "Rider":
        return jsonify({
            "success": False,
            "message": "Only riders can confirm delivery QR codes."
        }), 403

    # --------------------------------------------------------
    # GET SUBMITTED QR CODE
    # --------------------------------------------------------
    data = request.get_json(silent=True) or {}

    submitted_qr = str(
        data.get("qr_code", "")
    ).strip()

    if not submitted_qr:
        return jsonify({
            "success": False,
            "message": "QR code is required."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # ----------------------------------------------------
        # CHECK DELIVERY
        # ----------------------------------------------------
        cur.execute("""
            SELECT
                delivery_id,
                rider_id,
                customer_name,
                customer_phone,
                status,
                qr_code
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cur.fetchone()

        if not delivery:
            return jsonify({
                "success": False,
                "message": "Delivery not found."
            }), 404

        # ----------------------------------------------------
        # CHECK RIDER OWNERSHIP
        # ----------------------------------------------------
        if delivery["rider_id"] != rider_id:
            return jsonify({
                "success": False,
                "message": "This delivery is not assigned to you."
            }), 403

        # ----------------------------------------------------
        # CHECK DELIVERY STATUS
        # ----------------------------------------------------
        if delivery["status"] != "PICKED_UP":
            return jsonify({
                "success": False,
                "message": (
                    "QR confirmation is only allowed after "
                    "the delivery has been picked up."
                )
            }), 400

        # ----------------------------------------------------
        # DETERMINE EXPECTED QR
        # ----------------------------------------------------
        stored_qr = delivery.get("qr_code")

        # If a QR was stored during assignment, use it.
        # Otherwise use the demo QR.
        expected_qr = stored_qr or DEMO_QR_CODE

        # ----------------------------------------------------
        # VALIDATE QR
        # ----------------------------------------------------
        if submitted_qr != expected_qr:
            # Record failed attempt.
            # qr_confirmations does NOT have a qr_code column.
            cur.execute("""
                INSERT INTO qr_confirmations
                    (delivery_id, rider_id, result)
                VALUES
                    (%s, %s, %s)
            """, (
                delivery_id,
                rider_id,
                "Failed"
            ))

            conn.commit()

            return jsonify({
                "success": False,
                "message": "Invalid QR code."
            }), 400

        # ----------------------------------------------------
        # RECORD SUCCESSFUL QR CONFIRMATION
        # ----------------------------------------------------
        cur.execute("""
            INSERT INTO qr_confirmations
                (delivery_id, rider_id, result)
            VALUES
                (%s, %s, %s)
        """, (
            delivery_id,
            rider_id,
            "Successful"
        ))

        # ----------------------------------------------------
        # CHANGE DELIVERY STATUS
        # PICKED_UP -> DELIVERED
        # ----------------------------------------------------
        apply_transition(
            cur,
            delivery_id,
            rider_id,
            "DELIVERED"
        )

        conn.commit()

        # ----------------------------------------------------
        # SEND SMS
        # ----------------------------------------------------
        try:
            customer_phone = delivery["customer_phone"]
            customer_name = delivery["customer_name"]

            if customer_phone:
                send_sms(
                    customer_phone,
                    (
                        f"Hello {customer_name}, your Reflex delivery "
                        f"has been successfully delivered."
                    )
                )

        except Exception:
            # SMS failure should not undo a successful delivery.
            pass

        return jsonify({
            "success": True,
            "message": "QR confirmed successfully. Delivery completed.",
            "delivery_id": delivery_id,
            "status": "DELIVERED"
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("QR CONFIRMATION ERROR:", e)

        return jsonify({
            "success": False,
            "message": "QR confirmation failed.",
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


