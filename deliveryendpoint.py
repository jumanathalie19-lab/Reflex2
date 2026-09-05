from flask import Blueprint, request, jsonify, session
import mysql.connector
from mysql.connector import Error


delivery_bp = Blueprint("delivery", __name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="reflex_db"
    )


# ============================================================
# HELPER: CLOSE DATABASE CONNECTION
# ============================================================

def close_db(connection, cursor=None):
    try:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
    except Exception:
        pass


# ============================================================
# GET ALL DELIVERIES
# GET /api/deliveries
# ============================================================

@delivery_bp.route("/api/deliveries", methods=["GET"])
def get_deliveries():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                d.delivery_id,
                d.retailer_id,
                d.rider_id,
                d.customer_name,
                d.customer_phone,
                d.delivery_address,
                d.item_description,
                d.qr_code,
                d.status,
                d.created_at,
                d.updated_at,

                retailer.name AS retailer_name,
                retailer.phone AS retailer_phone,

                rider.name AS rider_name,
                rider.phone AS rider_phone

            FROM deliveries d

            LEFT JOIN users retailer
                ON d.retailer_id = retailer.user_id

            LEFT JOIN users rider
                ON d.rider_id = rider.user_id

            ORDER BY d.created_at DESC
        """)

        deliveries = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(deliveries),
            "deliveries": deliveries
        }), 200

    except Error as e:

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Could not retrieve deliveries."
        }), 500

    finally:
        close_db(connection, cursor)


# ============================================================
# GET SINGLE DELIVERY
# GET /api/deliveries/<delivery_id>
# ============================================================

@delivery_bp.route("/api/deliveries/<int:delivery_id>", methods=["GET"])
def get_delivery(delivery_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                d.delivery_id,
                d.retailer_id,
                d.rider_id,
                d.customer_name,
                d.customer_phone,
                d.delivery_address,
                d.item_description,
                d.qr_code,
                d.status,
                d.created_at,
                d.updated_at,

                retailer.name AS retailer_name,
                retailer.phone AS retailer_phone,

                rider.name AS rider_name,
                rider.phone AS rider_phone

            FROM deliveries d

            LEFT JOIN users retailer
                ON d.retailer_id = retailer.user_id

            LEFT JOIN users rider
                ON d.rider_id = rider.user_id

            WHERE d.delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "success": False,
                "message": "Delivery not found."
            }), 404

        return jsonify({
            "success": True,
            "delivery": delivery
        }), 200

    except Error as e:

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Could not retrieve delivery."
        }), 500

    finally:
        close_db(connection, cursor)


# ============================================================
# GET RETAILER DELIVERIES
# GET /api/retailers/<retailer_id>/deliveries
# ============================================================

@delivery_bp.route(
    "/api/retailers/<int:retailer_id>/deliveries",
    methods=["GET"]
)
def get_retailer_deliveries(retailer_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                d.delivery_id,
                d.retailer_id,
                d.rider_id,
                d.customer_name,
                d.customer_phone,
                d.delivery_address,
                d.item_description,
                d.qr_code,
                d.status,
                d.created_at,
                d.updated_at,

                rider.name AS rider_name,
                rider.phone AS rider_phone

            FROM deliveries d

            LEFT JOIN users rider
                ON d.rider_id = rider.user_id

            WHERE d.retailer_id = %s

            ORDER BY d.created_at DESC
        """, (retailer_id,))

        deliveries = cursor.fetchall()

        return jsonify({
            "success": True,
            "count": len(deliveries),
            "deliveries": deliveries
        }), 200

    except Error as e:

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Could not retrieve retailer deliveries."
        }), 500

    finally:
        close_db(connection, cursor)


# ============================================================
# CREATE DELIVERY
# POST /api/deliveries
# ============================================================

@delivery_bp.route("/api/deliveries", methods=["POST"])
def create_delivery():

    connection = None
    cursor = None

    try:
        # ----------------------------------------------------
        # REQUIRE LOGIN
        # ----------------------------------------------------
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "You must be logged in to create a delivery."
            }), 401

        # The retailer ID MUST come from the logged-in session.
        # Never trust a retailer_id supplied by the browser.
        retailer_id = session.get("user_id")
        user_role = session.get("role")

        if user_role != "Retailer":
            return jsonify({
                "success": False,
                "message": "Only Retailers can create delivery requests."
            }), 403

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "No delivery data received."
            }), 400

        customer_name = str(data.get("customer_name", "")).strip()
        customer_phone = str(data.get("customer_phone", "")).strip()
        delivery_address = str(data.get("delivery_address", "")).strip()
        item_description = str(data.get("item_description", "")).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------
        if not customer_name:
            return jsonify({
                "success": False,
                "message": "Customer name is required."
            }), 400

        if not customer_phone:
            return jsonify({
                "success": False,
                "message": "Customer phone is required."
            }), 400

        if not delivery_address:
            return jsonify({
                "success": False,
                "message": "Delivery address is required."
            }), 400

        if not item_description:
            return jsonify({
                "success": False,
                "message": "Item description is required."
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # VERIFY LOGGED-IN USER IS STILL A RETAILER
        # ----------------------------------------------------
        cursor.execute("""
            SELECT user_id, name, phone, role
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """, (retailer_id,))

        retailer = cursor.fetchone()

        if not retailer or retailer["role"] != "Retailer":
            session.clear()
            return jsonify({
                "success": False,
                "message": "Your account is not a valid Retailer account."
            }), 403

        # ----------------------------------------------------
        # INSERT DELIVERY
        # ----------------------------------------------------
        cursor.execute("""
            INSERT INTO deliveries (
                retailer_id,
                rider_id,
                customer_name,
                customer_phone,
                delivery_address,
                item_description,
                qr_code,
                status
            )
            VALUES (
                %s,
                NULL,
                %s,
                %s,
                %s,
                %s,
                NULL,
                'OPEN'
            )
        """, (
            retailer_id,
            customer_name,
            customer_phone,
            delivery_address,
            item_description
        ))

        delivery_id = cursor.lastrowid

        # ----------------------------------------------------
        # CREATE INITIAL STATUS HISTORY
        # ----------------------------------------------------
        cursor.execute("""
            INSERT INTO status_history (
                delivery_id,
                changed_by,
                status
            )
            VALUES (
                %s,
                %s,
                'OPEN'
            )
        """, (
            delivery_id,
            retailer_id
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Delivery request created successfully.",
            "delivery": {
                "delivery_id": delivery_id,
                "retailer_id": retailer_id,
                "retailer_name": retailer["name"],
                "retailer_phone": retailer["phone"],
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "delivery_address": delivery_address,
                "item_description": item_description,
                "status": "OPEN"
            }
        }), 201

    except Error as e:
        if connection:
            connection.rollback()

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Database error while creating delivery.",
            "error": str(e)
        }), 500

    except Exception as e:
        if connection:
            connection.rollback()

        print("Server error:", e)

        return jsonify({
            "success": False,
            "message": "Unexpected server error.",
            "error": str(e)
        }), 500

    finally:
        close_db(connection, cursor)


# ============================================================
# UPDATE DELIVERY
# PUT /api/deliveries/<delivery_id>
# ============================================================

@delivery_bp.route(
    "/api/deliveries/<int:delivery_id>",
    methods=["PUT"]
)
def update_delivery(delivery_id):

    connection = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No update data received."
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # ----------------------------------------------------
        # CHECK DELIVERY
        # ----------------------------------------------------

        cursor.execute("""
            SELECT *
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "success": False,
                "message": "Delivery not found."
            }), 404

        # ----------------------------------------------------
        # ALLOWED FIELDS
        # ----------------------------------------------------

        customer_name = data.get(
            "customer_name",
            delivery["customer_name"]
        )

        customer_phone = data.get(
            "customer_phone",
            delivery["customer_phone"]
        )

        delivery_address = data.get(
            "delivery_address",
            delivery["delivery_address"]
        )

        item_description = data.get(
            "item_description",
            delivery["item_description"]
        )

        cursor.execute("""
            UPDATE deliveries
            SET
                customer_name = %s,
                customer_phone = %s,
                delivery_address = %s,
                item_description = %s
            WHERE delivery_id = %s
        """, (
            customer_name,
            customer_phone,
            delivery_address,
            item_description,
            delivery_id
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Delivery updated successfully.",
            "delivery_id": delivery_id
        }), 200

    except Error as e:

        if connection:
            connection.rollback()

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Could not update delivery."
        }), 500

    finally:
        close_db(connection, cursor)


# ============================================================
# DELETE DELIVERY
# DELETE /api/deliveries/<delivery_id>
# ============================================================

@delivery_bp.route(
    "/api/deliveries/<int:delivery_id>",
    methods=["DELETE"]
)
def delete_delivery(delivery_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT delivery_id
            FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        delivery = cursor.fetchone()

        if not delivery:
            return jsonify({
                "success": False,
                "message": "Delivery not found."
            }), 404

        cursor.execute("""
            DELETE FROM deliveries
            WHERE delivery_id = %s
        """, (delivery_id,))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Delivery deleted successfully."
        }), 200

    except Error as e:

        if connection:
            connection.rollback()

        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Could not delete delivery."
        }), 500

    finally:
        close_db(connection, cursor)