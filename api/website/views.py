import asyncio
import json
import os
from datetime import datetime
import random
from crypt import methods
from threading import Thread
from flask import Blueprint, render_template, request, jsonify, redirect
from functools import wraps
from flask import redirect, session

from database import Database
from flask_cors import CORS
from positions import Positions
from structures.users import Users
from structures.cards import Cards

views = Blueprint("views", __name__)
db = Database.establish_connection(Database.URI, Database.NAME)
users = Users(db.users)
cards = Cards(db.cards)

CORS(views)


def admin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect("/login")
        return func(*args, **kwargs)

    return decorated


@views.route("/")
def home():
    return render_template("home.html")

@views.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    id_input = request.form.get("email")
    password_input = request.form.get("password")

    try:
        with open("/administrators.json", "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Internal error", 500

    for admin in data:
        if admin["id"] == id_input and admin["pwd"] == password_input:
            session["admin_id"] = id_input
            return redirect("/admin/home")

    return render_template("login.html", error="Invalid credentials")

@views.route("admin/home")
@admin_required
def admin_home():
    return render_template("adminpanel.html")

@views.route("/admin/profile/<id>")
@admin_required
def admin_profile(id):
    return render_template("profile.html", id=id)

# the api stuff

@views.route("api/get_status", methods=["GET"])
def get_status():
    return jsonify({"status": 200})

@views.route("api/create_user", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": 400, "response": "Invalid JSON body"})

    name = data.get("name")
    id = data.get("id")
    position = data.get("position")

    created = users.create(name, id, position, False)
    if created:
        return jsonify({"status": 201, "response": "User created"})
    else:
        return jsonify({"status": 409, "response": "User with ID already exists"})

@views.route("api/update_user", methods=["PUT"])
def update_user():
    data = request.get_json(silent=True)

    id = data.get("id")
    position = data.get("position")
    score = data.get("score")
    admin = data.get("admin")

    updated = users.update(id, position, score, admin)
    if updated:
        return jsonify({"status": 201, "response": "User updated"})
    else:
        return jsonify({"status": 409, "response": "Unable to update user"})

@views.route("api/delete_user", methods=["DELETE"])
def delete_user():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": 400, "response": "Invalid JSON body"})

    id = data.get("id")

    deleted = users.delete(id)
    if deleted:
        return jsonify({"status": 200, "response": "User deleted"})
    else:
        return jsonify({"status": 210, "response": "User does not exist"})

@views.route("api/get_users", methods=["GET"])
def get_users():
    return {"status": 200, "response": users.get_all()}

@views.route("api/get_user")
def get_user():
    id = request.args.get("id")
    return {"status": 200, "response": users.get({"id": id})}

@views.route("api/check_in", methods=["POST"])
def check_in():
    data = request.get_json(silent=True)
    id = data.get("id")

    checked_in = users.check_in(id)
    return jsonify({"status": 200, "response": "Checked in" if checked_in else "Checked out"})

@views.route("api/is_present")
def is_checked_in():
    id = request.args.get("id")
    user = users.get({"id": id})

    if not user:
        return False

    if not user.get("attendance"):
        return {"status": 200, "response": False}

    last_obj = user["attendance"][-1]
    if last_obj["date"] == datetime.now().strftime("%x") and not last_obj["out"]:
        return {"status": 200, "response": True}

    return {"status": 200, "response": False}


@views.route("api/create_card", methods=["POST"])
def create_card():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": 400, "response": "Invalid JSON body"})

    user_id = data.get("user_id")
    academic_year = data.get("year")
    expires = data.get("expires")


    created = cards.create(user_id, academic_year, expires)
    if created:
        return jsonify({"status": 201, "response": "Card created"})
    else:
        return jsonify({"status": 409, "response": "Something went terribly wrong"})

@views.route("api/update_card", methods=["POST"])
def update_card():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": 400, "response": "Invalid JSON body"})

    id = data.get("id")
    enabled = data.get("enabled")

    cards.update(id, enabled)

@views.route("api/delete_card", methods=["DELETE"])
def delete_card():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"status": 400, "response": "Invalid JSON body"})

    id = data.get("id")

    deleted = cards.delete(id)
    if deleted:
        return jsonify({"status": 200, "response": "Card deleted"})
    else:
        return jsonify({"status": 210, "response": "Card does not exist"})

@views.route("api/get_card")
def get_card():
    id = request.args.get("id")
    return jsonify({"status": 200, "response": cards.get({"id": id})})

@views.route("api/get_cards")
def get_cards():
    return jsonify({"status": 200, "response": cards.get_all()})

@views.route("api/get_cards_from")
def get_cards_from():
    user_id = request.args.get("user_id")
    return jsonify({"status": 200, "response": cards.get({"user_id": user_id})})
