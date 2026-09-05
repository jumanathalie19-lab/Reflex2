
from flask import Blueprint, jsonify, request, session

from auth import role_required
from db import get_connection
from sms_service import send_sms


assignment_bp = Blueprint("assignment", __name__)


# ============================================================
# DEMO QR CODE
# ============================================================
#
# For the prototype/demo, all assigned deliveries use the
# same simple QR value.
#
# In a production system, this should be replaced with a
# unique QR code for every delivery.
# ============================================================

DEMO_QR_CODE = "REFLEX-DELIVERY"


# ============================================================
# CREATE DELIVERY
# ============================================================
#
# Retailer creates a new delivery request.
# Retailer ID comes automatically from the logged-in session.
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

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                user_id,
                name,
                role
            FROM Users
            WHERE user_id = %s
            """,
            (retailer_id,)
        )

        retailer = cur.fetchone()

        if retailer is None or retailer["role"] != "Retailer":
            return jsonify({
                "error": "Logged-in user is not a valid Retailer"
            }), 403

        cur.execute(
            """
            INSERT INTO Deliveries
                (
                    retailer_id,
                    customer_name,
                    customer_phone,
                    delivery_address,
                    item_description
                )
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                retailer_id,
                body["customer_name"],
                body["customer_phone"],
                body["delivery_address"],
                body["item_description"]
            )
        )

        delivery_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "success": True,
            "delivery_id": delivery_id,
            "retailer_id": retailer_id,
            "status": "OPEN"
        }), 201

    except Exception as error:

        conn.rollback()

        print("Create delivery error:", error)

        return jsonify({
            "error": "Unable to create delivery"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# LIST OPEN DELIVERIES
# ============================================================
#
# Dispatcher can see available delivery requests.
# ============================================================

@assignment_bp.route("/deliveries", methods=["GET"])
@role_required("Dispatcher")
def list_open_deliveries():

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

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
            FROM Deliveries
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

        cur.close()
        conn.close()


# ============================================================
# LIST RIDERS
# ============================================================
#
# Dispatcher can retrieve available riders.
# ============================================================

@assignment_bp.route("/riders", methods=["GET"])
@role_required("Dispatcher")
def list_riders():

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                user_id,
                name,
                phone
            FROM Users
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

        cur.close()
        conn.close()


# ============================================================
# ASSIGN DELIVERY
# ============================================================
#
# Dispatcher assigns an open delivery to a rider.
#
# dispatcher_id comes automatically from the logged-in session.
# Frontend only sends rider_id.
#
# QR CODE:
# A fixed demo QR code is stored with the assignment.
#
# SMS:
# After successful assignment, an SMS notification is sent
# using the SMS stub in sms_service.py.
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

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # CONFIRM LOGGED-IN USER IS A DISPATCHER
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                user_id,
                name,
                role
            FROM Users
            WHERE user_id = %s
            """,
            (dispatcher_id,)
        )

        dispatcher = cur.fetchone()

        if dispatcher is None or dispatcher["role"] != "Dispatcher":
            return jsonify({
                "error": "Logged-in user is not a valid Dispatcher"
            }), 403

        # ----------------------------------------------------
        # CHECK DELIVERY
        #
        # Retrieve customer details as well because they are
        # required for the SMS notification.
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT
                delivery_id,
                status,
                customer_phone,
                customer_name
            FROM Deliveries
            WHERE delivery_id = %s
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
            FROM Users
            WHERE user_id = %s
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
        # USE FIXED DEMO QR CODE
        # ----------------------------------------------------

        qr_code = DEMO_QR_CODE

        # ----------------------------------------------------
        # ASSIGN DELIVERY
        # ----------------------------------------------------

        cur.execute(
            """
            UPDATE Deliveries
            SET
                rider_id = %s,
                status = 'ASSIGNED',
                qr_code = %s
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
            INSERT INTO Status_history
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
        # SAVE DATABASE CHANGES
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # SEND CUSTOMER SMS
        # ----------------------------------------------------
        #
        # Currently this uses the SMS stub.
        # The message will appear in the Flask terminal.
        #
        # Later, sms_service.py can be connected to a real
        # SMS provider without changing this endpoint.
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
        # RETURN SUCCESS
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

        conn.rollback()

        print("Assignment error:", error)

        return jsonify({
            "error": "Unable to assign delivery"
        }), 500

    finally:

        cur.close()
        conn.close()

