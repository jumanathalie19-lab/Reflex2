
from flask import Blueprint, jsonify, request, session
from db import get_connection
from auth import role_required

status_bp = Blueprint("status", __name__)


VALID_TRANSITIONS = {
    "ASSIGNED": ["PICKED_UP"],
    "PICKED_UP": ["DELIVERED"],
    "DELIVERED": [],
}


def apply_transition(cur, delivery_id, changed_by, new_status):
    """
    Performs the actual status UPDATE and Status_history INSERT.

    The rider identity is supplied by the caller after it has already
    been obtained from the authenticated Flask session.
    """
    cur.execute(
        """
        UPDATE Deliveries
        SET status = %s
        WHERE delivery_id = %s
        """,
        (new_status, delivery_id),
    )

    cur.execute(
        """
        INSERT INTO Status_history (delivery_id, changed_by, status)
        VALUES (%s, %s, %s)
        """,
        (delivery_id, changed_by, new_status),
    )


# ============================================================
# GET RIDER'S DELIVERIES
# ============================================================

@status_bp.route("/deliveries/mine", methods=["GET"])
@role_required("Rider")
def list_rider_deliveries():

    # Get the rider automatically from the logged-in session.
    rider_id = session.get("user_id")

    if not rider_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    status_filter = request.args.get("status")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        if status_filter == "active":

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
                    created_at,
                    updated_at
                FROM Deliveries
                WHERE rider_id = %s
                  AND status IN ('ASSIGNED', 'PICKED_UP')
                ORDER BY updated_at ASC
                """,
                (rider_id,),
            )

        else:

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
                    created_at,
                    updated_at
                FROM Deliveries
                WHERE rider_id = %s
                ORDER BY updated_at DESC
                """,
                (rider_id,),
            )

        rows = cur.fetchall()

        return jsonify(rows), 200

    except Exception as error:

        print("Load rider deliveries error:", error)

        return jsonify({
            "error": "Unable to load deliveries"
        }), 500

    finally:
        cur.close()
        conn.close()


# ============================================================
# UPDATE DELIVERY STATUS
# ============================================================

@status_bp.route(
    "/deliveries/<int:delivery_id>/status",
    methods=["PATCH"]
)
@role_required("Rider")
def update_status(delivery_id):

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    # Rider identity comes from the authenticated session.
    rider_id = session.get("user_id")

    if not rider_id:
        return jsonify({
            "error": "Authentication required"
        }), 401

    new_status = body.get("status")

    if not new_status:
        return jsonify({
            "error": "status is required"
        }), 400

    if new_status not in ("PICKED_UP", "DELIVERED"):
        return jsonify({
            "error": f"'{new_status}' is not a status a rider can set directly"
        }), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        # Find the delivery and its assigned rider.
        cur.execute(
            """
            SELECT status, rider_id
            FROM Deliveries
            WHERE delivery_id = %s
            """,
            (delivery_id,),
        )

        delivery = cur.fetchone()

        if delivery is None:
            return jsonify({
                "error": f"No delivery found with id {delivery_id}"
            }), 404

        # Make sure this delivery belongs to the logged-in rider.
        if str(delivery["rider_id"]) != str(rider_id):
            return jsonify({
                "error": "You are not assigned to this delivery"
            }), 403

        current_status = delivery["status"]

        allowed_next = VALID_TRANSITIONS.get(
            current_status,
            []
        )

        if new_status not in allowed_next:
            return jsonify({
                "error": (
                    f"Cannot change status from "
                    f"{current_status} to {new_status}"
                )
            }), 409

        # DELIVERED requires successful QR confirmation.
        if new_status == "DELIVERED":

            cur.execute(
                """
                SELECT confirmation_id
                FROM QR_confirmations
                WHERE delivery_id = %s
                  AND result = 'Successful'
                ORDER BY scanned_at DESC
                LIMIT 1
                """,
                (delivery_id,),
            )

            confirmation = cur.fetchone()

            if confirmation is None:
                return jsonify({
                    "error": "DELIVERED requires a successful QR scan first",
                    "delivery_id": delivery_id
                }), 409

        # Apply transition using the logged-in rider as changed_by.
        apply_transition(
            cur,
            delivery_id,
            rider_id,
            new_status
        )

        conn.commit()

        return jsonify({
            "delivery_id": delivery_id,
            "previous_status": current_status,
            "status": new_status
        }), 200

    except Exception as error:

        conn.rollback()

        print("Update delivery status error:", error)

        return jsonify({
            "error": "Unable to update delivery status"
        }), 500

    finally:
        cur.close()
        conn.close()

