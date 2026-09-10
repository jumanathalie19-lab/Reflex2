
# ============================================================
# REFLEX QR CONFIRMATION
# PostgreSQL version
# ============================================================

from flask import Blueprint, request, jsonify, session
from psycopg2.extras import RealDictCursor

from db import get_connection
from statusendpoint import apply_transition


qr_bp = Blueprint("qr", __name__)


# ------------------------------------------------------------
# DEMO QR CODE
# ------------------------------------------------------------
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
        # GET DELIVERY
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
        # GET EXPECTED QR
        # ----------------------------------------------------
        stored_qr = delivery.get("qr_code")

        if stored_qr:
            expected_qr = stored_qr
        else:
            expected_qr = DEMO_QR_CODE

        # ----------------------------------------------------
        # CHECK QR CODE
        # ----------------------------------------------------
        if submitted_qr != expected_qr:

            # Record failed attempt.
            # qr_confirmations contains:
            # confirmation_id
            # delivery_id
            # rider_id
            # result
            # scanned_at

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
        # SUCCESS RESPONSE
        # --------------------------------------------------------
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
