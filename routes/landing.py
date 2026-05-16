from flask import Blueprint, render_template, current_app
import json, os

landing_bp = Blueprint("landing", __name__)

@landing_bp.route("/doula")
def landing():
    # Load Slovak copy from content/sk/landing.json
    content_path = os.path.join(current_app.root_path, "content", "sk", "landing.json")
    with open(content_path, encoding="utf-8") as f:
        copy = json.load(f)
    return render_template("landing.html", copy=copy)
