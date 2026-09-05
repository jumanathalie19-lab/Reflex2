from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection


# ============================================================
# AUTHENTICATION BLUEPRINT
# ============================================================

auth_bp = Blueprint("auth", __name__)


# ============================================================
# LOGIN PAGE
# ============================================================

@auth_bp.route("/login", methods=["GET"])
def login_page():

    # Already logged in
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    phone = str(body.get("phone", "")).strip()
    password = str(body.get("password", ""))

    if not phone:
        return jsonify({
            "error": "Phone number is required"
        }), 400

    if not password:
        return jsonify({
            "error": "Password is required"
        }), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                user_id,
                name,
                phone,
                role,
                password_hash
            FROM Users
            WHERE phone = %s
            LIMIT 1
            """,
            (phone,)
        )

        user = cur.fetchone()

        if user is None:
            return jsonify({
                "error": "Invalid phone number or password"
            }), 401

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            return jsonify({
                "error": "Invalid phone number or password"
            }), 401

        # ----------------------------------------------------
        # CREATE SESSION
        # ----------------------------------------------------

        session.clear()

        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        session["phone"] = user["phone"]
        session["role"] = user["role"]

        # ----------------------------------------------------
        # DETERMINE DASHBOARD
        # ----------------------------------------------------

        dashboard_urls = {
            "Retailer": "/retailer",
            "Dispatcher": "/dispatcher",
            "Rider": "/rider"
        }

        dashboard = dashboard_urls.get(user["role"])

        if dashboard is None:

            session.clear()

            return jsonify({
                "error": "Your account has an invalid role"
            }), 403

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "phone": user["phone"],
                "role": user["role"]
            },
            "redirect": dashboard
        }), 200

    except Exception as error:

        print("Login error:", error)

        return jsonify({
            "error": "Unable to process login"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# REGISTER PAGE
# ============================================================

@auth_bp.route("/register", methods=["GET"])
def register_page():

    # Already logged in
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("register.html")


# ============================================================
# REGISTER
# ============================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    name = str(body.get("name", "")).strip()
    phone = str(body.get("phone", "")).strip()
    password = str(body.get("password", ""))
    confirm_password = str(
        body.get("confirm_password", "")
    )
    role = str(body.get("role", "")).strip()

    # ========================================================
    # VALIDATION
    # ========================================================

    if not name:
        return jsonify({
            "error": "Name is required"
        }), 400

    if not phone:
        return jsonify({
            "error": "Phone number is required"
        }), 400

    if not password:
        return jsonify({
            "error": "Password is required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    if password != confirm_password:
        return jsonify({
            "error": "Passwords do not match"
        }), 400

    valid_roles = {
        "Retailer",
        "Dispatcher",
        "Rider"
    }

    if role not in valid_roles:
        return jsonify({
            "error": "Please select a valid role"
        }), 400

    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # CHECK IF PHONE ALREADY EXISTS
        # ----------------------------------------------------

        cur.execute(
            """
            SELECT user_id
            FROM Users
            WHERE phone = %s
            LIMIT 1
            """,
            (phone,)
        )

        existing_user = cur.fetchone()

        if existing_user is not None:

            return jsonify({
                "error": "An account with this phone number already exists"
            }), 409

        # ----------------------------------------------------
        # HASH PASSWORD
        # ----------------------------------------------------

        password_hash = generate_password_hash(password)

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        cur.execute(
            """
            INSERT INTO Users
                (name, phone, role, password_hash)
            VALUES
                (%s, %s, %s, %s)
            """,
            (
                name,
                phone,
                role,
                password_hash
            )
        )

        user_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": {
                "user_id": user_id,
                "name": name,
                "phone": phone,
                "role": role
            },
            "redirect": "/login"
        }), 201

    except Exception as error:

        conn.rollback()

        print("Registration error:", error)

        return jsonify({
            "error": "Unable to create account"
        }), 500

    finally:

        cur.close()
        conn.close()


# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200


# ============================================================
# CURRENT USER
# ============================================================

@auth_bp.route("/api/me", methods=["GET"])
def current_user():

    if "user_id" not in session:

        return jsonify({
            "authenticated": False
        }), 401

    return jsonify({
        "authenticated": True,
        "user": {
            "user_id": session["user_id"],
            "name": session["name"],
            "phone": session["phone"],
            "role": session["role"]
        }
    }), 200


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            # API requests should receive JSON
            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required"
                }), 401

            # Normal browser requests go to login
            return redirect(
                url_for("auth.login_page")
            )

        return view(*args, **kwargs)

    return wrapped_view


# ============================================================
# ROLE REQUIRED
# ============================================================

def role_required(*allowed_roles):

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            # ------------------------------------------------
            # NOT LOGGED IN
            # ------------------------------------------------

            if "user_id" not in session:

                if request.path.startswith("/api/"):
                    return jsonify({
                        "error": "Authentication required"
                    }), 401

                return redirect(
                    url_for("auth.login_page")
                )

            # ------------------------------------------------
            # CHECK ROLE
            # ------------------------------------------------

            user_role = session.get("role")

            if user_role not in allowed_roles:

                if request.path.startswith("/api/"):
                    return jsonify({
                        "error": "You do not have permission to access this resource"
                    }), 403

                return redirect(
                    url_for("dashboard")
                )

            return view(*args, **kwargs)

        return wrapped_view

    return decorator