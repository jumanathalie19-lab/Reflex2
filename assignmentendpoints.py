from flask import Blueprint, jsonify, request, session
from psycopg2.extras import RealDictCursor

from auth import role_required
from db import get_connection
from sms_service import send_sms


assignment_bp = Blueprint("assignment", __name__)


# ============================================================
# DEMO QR CODE
# ============================================================

DEMO_QR_CODE = "REFLEX-DELIVERY"


# ============================================================
# CREATE DELIVERY
# POST /deliveries
# ============================================================

@assignment_bp.route("/deliveries", methods=["POST"])
@role_required("Retailer")
def create_delivery():

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    required = [
        "customer_name",
        "customer_phone",
        "delivery_address",
        "item_description"
    ]

    missing = [
        field
        for field in required
        if not body.get(field)
    ]

    if missing:
        return jsonify({
            "error": (
                f"Missing required field(s): "
                f"{', '.join(missing)}"
            )
        }), 400

    retailer_id = session.get("user_id")

    if not retailer_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    conn = None
    cur = None

    try:

        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # CONFIRM RETAILER
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                user_id,
                name,
                phone,
                role
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (retailer_id,)
        )

        retailer = cur.fetchone()

        if retailer is None or retailer["role"] != "Retailer":
            return jsonify({
                "error": "Logged-in user is not a valid Retailer"
            }), 403

        # ----------------------------------------------------
        # CREATE DELIVERY
        # PostgreSQL uses RETURNING instead of lastrowid
        # ----------------------------------------------------

        cur.execute(
            """
            INSERT INTO deliveries
                (
                    retailer_id,
                    rider_id,
                    customer_name,
                    customer_phone,
                    delivery_address,
                    item_description,
                    qr_code,
                    status
                )
            VALUES
                (
                    %s,
                    NULL,
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    'OPEN'
                )
            RETURNING delivery_id
            """,
            (
                retailer_id,
                body["customer_name"].strip(),
                body["customer_phone"].strip(),
                body["delivery_address"].strip(),
                body["item_description"].strip()
            )
        )

        result = cur.fetchone()
        delivery_id = result["delivery_id"]

        # ----------------------------------------------------
        # RECORD INITIAL STATUS
        # ----------------------------------------------------

        cur.execute(
            """
            INSERT INTO status_history
                (
                    delivery_id,
                    changed_by,
                    status
                )
            VALUES
                (
                    %s,
                    %s,
                    'OPEN'
                )
            """,
            (
                delivery_id,
                retailer_id
            )
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "message": "Delivery request created successfully.",
            "delivery_id": delivery_id,
            "retailer_id": retailer_id,
            "retailer_name": retailer["name"],
            "retailer_phone": retailer["phone"],
            "customer_name": body["customer_name"].strip(),
            "customer_phone": body["customer_phone"].strip(),
            "delivery_address": body["delivery_address"].strip(),
            "item_description": body["item_description"].strip(),
            "status": "OPEN"
        }), 201

    except Exception as error:

        if conn:
            conn.rollback()

        print("Create delivery error:", error)

        return jsonify({
            "success": False,
            "error": "Unable to create delivery",
            "message": str(error)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# LIST OPEN DELIVERIES
# GET /deliveries
# ============================================================

@assignment_bp.route("/deliveries", methods=["GET"])
@role_required("Dispatcher")
def list_open_deliveries():

    conn = None
    cur = None

    try:

        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            """
            SELECT
                delivery_id,
                retailer_id,
                customer_name,
                customer_phone,
                delivery_address,
                item_description,
                status,
                created_at
            FROM deliveries
            WHERE status = 'OPEN'
            ORDER BY created_at ASC
            """
        )

        rows = cur.fetchall()

        return jsonify(rows), 200

    except Exception as error:

        print("List deliveries error:", error)

        return jsonify({
            "error": "Unable to load deliveries"
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# LIST RIDERS
# GET /riders
# ============================================================

@assignment_bp.route("/riders", methods=["GET"])
@role_required("Dispatcher")
def list_riders():

    conn = None
    cur = None

    try:

        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cur.execute(
            """
            SELECT
                user_id,
                name,
                phone
            FROM users
            WHERE role = 'Rider'
            ORDER BY name ASC
            """
        )

        rows = cur.fetchall()

        return jsonify(rows), 200

    except Exception as error:

        print("List riders error:", error)

        return jsonify({
            "error": "Unable to load riders"
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ============================================================
# ASSIGN DELIVERY
# POST /deliveries/<delivery_id>/assign
# ============================================================

@assignment_bp.route(
    "/deliveries/<int:delivery_id>/assign",
    methods=["POST"]
)
@role_required("Dispatcher")
def assign_delivery(delivery_id):

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    rider_id = body.get("rider_id")

    if not rider_id:
        return jsonify({
            "error": "rider_id is required"
        }), 400

    dispatcher_id = session.get("user_id")

    if not dispatcher_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    conn = None
    cur = None

    try:

        conn = get_connection()

        cur = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # ----------------------------------------------------
        # CONFIRM DISPATCHER
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                user_id,
                name,
                role
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (dispatcher_id,)
        )

        dispatcher = cur.fetchone()

        if (
            dispatcher is None
            or dispatcher["role"] != "Dispatcher"
        ):
            return jsonify({
                "error": (
                    "Logged-in user is not "
                    "a valid Dispatcher"
                )
            }), 403

        # ----------------------------------------------------
        # CHECK DELIVERY
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                delivery_id,
                status,
                customer_phone,
                customer_name
            FROM deliveries
            WHERE delivery_id = %s
            LIMIT 1
            """,
            (delivery_id,)
        )

        delivery = cur.fetchone()

        if delivery is None:
            return jsonify({
                "error": (
                    f"No delivery found with id "
                    f"{delivery_id}"
                )
            }), 404

        # ----------------------------------------------------
        # DELIVERY MUST BE OPEN
        # ----------------------------------------------------

        if delivery["status"] != "OPEN":

            return jsonify({
                "error": (
                    f"Delivery {delivery_id} is already "
                    f"{delivery['status']}, cannot assign"
                )
            }), 409

        # ----------------------------------------------------
        # CONFIRM RIDER
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                user_id,
                name,
                phone,
                role
            FROM users
            WHERE user_id = %s
            LIMIT 1
            """,
            (rider_id,)
        )

        rider = cur.fetchone()

        if rider is None or rider["role"] != "Rider":

            return jsonify({
                "error": (
                    f"User {rider_id} is not "
                    f"a valid Rider"
                )
            }), 400

        # ----------------------------------------------------
        # USE DEMO QR
        # ----------------------------------------------------

        qr_code = DEMO_QR_CODE

        # ----------------------------------------------------
        # ASSIGN DELIVERY
        # ----------------------------------------------------

        cur.execute(
            """
            UPDATE deliveries
            SET
                rider_id = %s,
                status = 'ASSIGNED',
                qr_code = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE delivery_id = %s
            """,
            (
                rider_id,
                qr_code,
                delivery_id
            )
        )

        # ----------------------------------------------------
        # RECORD STATUS HISTORY
        # ----------------------------------------------------

        cur.execute(
            """
            INSERT INTO status_history
                (
                    delivery_id,
                    changed_by,
                    status
                )
            VALUES
                (
                    %s,
                    %s,
                    'ASSIGNED'
                )
            """,
            (
                delivery_id,
                dispatcher_id
            )
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # SEND CUSTOMER SMS
        # ----------------------------------------------------

        sms_result = send_sms(
            delivery["customer_phone"],
            (
                f"Hi {delivery['customer_name']}, your Reflex "
                f"delivery has been assigned to a rider and "
                f"is on its way."
            )
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "delivery_id": delivery_id,
            "rider_id": rider_id,
            "dispatcher_id": dispatcher_id,
            "status": "ASSIGNED",
            "qr_code": DEMO_QR_CODE,
            "sms": sms_result
        }), 200

    except Exception as error:

        if conn:
            conn.rollback()

        print("Assignment error:", error)

        return jsonify({
            "success": False,
            "error": "Unable to assign delivery",
            "message": str(error)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()
