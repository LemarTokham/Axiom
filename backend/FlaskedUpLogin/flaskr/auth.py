import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from .db import get_db

import pymongo

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        try:
            from bson.objectid import ObjectId
            g.user = get_db().user.find_one({"_id": ObjectId(user_id)})

            #this updates the last activity time if the user manages to log in
            if g.user is not None:
               from datetime import datetime
               currTime = datetime.utcnow()
               get_db().user.update_one(
                   {"_id": g.user["_id"]},
                   {"$set": {"study_stats.last_activity": currTime}}
               )



        except (TypeError, ValueError):

            g.user = None


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                # Check if user already exists
                if db.user.find_one({"username": username}) is not None:
                    error = f"User {username} is already registered."
                else:
                    # Insert new user

                    from datetime import datetime, timedelta
                    import uuid 
                    currTime = datetime.utcnow() 
                    expiry_time = currTime + timedelta(days=1)
                                                       
                    db.user.insert_one({
                 "username": username,
                 "email": request.form.get("email", ""),
                 "password_hash": generate_password_hash(password),
                 "first_name": request.form.get("first_name", ""),
                 "last_name": request.form.get("last_name", ""),
                 "created_at": currTime,
                 "last_login": currTime,
                 "is_admin": False,
                 "is_active": True,
                 "is_verified": False,
                 "verification_token": str(uuid.uuid4()),
                 "verification_token_expiry": expiry_time,
                 "profile": {
                     "avatar": None,
                     "bio": None,
                     "education_level": None,
                     "subjects": []
                 },
                 "preferences": {
                     "theme": "light",
                     "notification_email": True,
                     "language": "en",
                     "study_reminder": False
                 },
                 "study_stats": {
                     "total_study_time": 0,
                     "quizzes_completed": 0,
                     "flashcards_reviewed": 0,
                     "last_activity": currTime
                 },
                 "security": {
                     "password_reset_token": None,
                     "password_reset_expiry": None,
                     "failed_login_attempts": 0,
                     "last_password_change": currTime
                 }
              })
                # Success, go to the login page
                return redirect(url_for("auth.login"))
            except pymongo.errors.PyMongoError:
                error = "Database error occurred."

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.user.find_one({"username": username})

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = str(user["_id"])

            from datetime import datetime
            currTime = datetime.utcnow()

            db.user.update_one(
          {"_id": user["_id"]},
          {
              "$set": {
                  "last_login": currTime,
                  "study_stats.last_activity": currTime,
                  "security.failed_login_attempts": 0
              }
          }
      )


            return redirect(url_for("index"))

        else:
            if user is not None:
                db.user.update_one(
              {"_id": user["_id"]},
              {"$inc": {"security.failed_login_attempts": 1}}
                )

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))