import os
import logging
from flask import Flask, render_template
from flask_talisman import Talisman

app = Flask(__name__)

secret_path = os.path.join(os.path.dirname(__file__), "secrets.txt")
try:
    with open(secret_path, "r") as f:
        app.secret_key = f.read().strip()
except FileNotFoundError:
    raise RuntimeError("Secret key file not found. Please create a 'secrets.txt' file.")

logging.basicConfig(level=logging.INFO)

csp = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'"],
}
Talisman(
    app,
    content_security_policy=csp,
    force_https=False,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
)

@app.route("/")
def index():
    return render_template("index.html")

@app.context_processor
def inject_version():
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        with open(version_path, "r") as vf:
            version = vf.read().strip()
    except Exception:
        version = "unknown"
    return {"version": version}

if __name__ == "__main__":
    app.run(debug=True)
