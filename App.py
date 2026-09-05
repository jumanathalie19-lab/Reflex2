from flask import Flask, render_template, session, redirect, url_for
from deliveryendpoint import delivery_bp
from auth import auth_bp, role_required
from assignmentendpoints import assignment_bp
from statusendpoint import status_bp
from qr import qr_bp

app = Flask(__name__)

app.secret_key = "reflex-development-secret-key"

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(assignment_bp)
app.register_blueprint(status_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(delivery_bp)



@app.route("/")
def home():
    # If not logged in, go to login
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    # If already logged in, go to dashboard
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    role = session.get("role")

    if role == "Retailer":
        return redirect(url_for("retailer_page"))

    if role == "Dispatcher":
        return redirect(url_for("dispatcher_page"))

    if role == "Rider":
        return redirect(url_for("rider_page"))

    session.clear()
    return redirect(url_for("auth.login_page"))


@app.route("/retailer")
@role_required("Retailer")
def retailer_page():
    return render_template("retailer.html")


@app.route("/rider")
@role_required("Rider")
def rider_page():
    return render_template("rider.html")


@app.route("/dispatcher")
@role_required("Dispatcher")
def dispatcher_page():
    return render_template("dispatcher.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)