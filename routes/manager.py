"""Team Manager role routes."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

import data
import mysql.connector
from routes.decorators import login_required

manager_bp = Blueprint("manager", __name__)


def _assigned_events(user):
    ids = user.get("assigned_events") or []
    return [e for e in data.get_events() if e["id"] in ids]


@manager_bp.route("/dashboard")
@login_required(role="manager")
def dashboard():
    user = data.get_user_by_id(session["user_id"])
    events = _assigned_events(user)
    cards = []
    for e in events:
        cards.append(
            {
                "event": e,
                "participant_count": data.count_participants_for_event(e["id"]),
                "item_count": len(e["items"]),
            }
        )
    return render_template(
        "manager/dashboard.html",
        cards=cards,
        total_events=len(events),
        total_participants=sum(c["participant_count"] for c in cards),
    )


@manager_bp.route("/clubs")
@login_required(role="manager")
def clubs():
    clubs = data.clubs_for_coordinator(session["user_id"])
    # Club membership grants visibility only; existing assigned-event permissions remain unchanged.
    return render_template("manager/clubs.html", clubs=clubs, events=data.get_events())


@manager_bp.route("/participants", methods=["GET", "POST"])
@login_required(role="manager")
def participants():
    user = data.get_user_by_id(session["user_id"])
    events = _assigned_events(user)

    if request.method == "POST":
        action = request.form.get("action", "register")
        if action == "register":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            college = request.form.get("college", "").strip()
            roll_number = request.form.get("roll_number", "").strip()
            event_id = request.form.get("eventId")
            item_ids = request.form.getlist("itemIds")

            assigned_ids = user.get("assigned_events") or []
            if event_id not in assigned_ids:
                flash("You can only register participants for assigned events.", "error")
                return redirect(url_for("manager.participants"))

            if not item_ids:
                flash("Select at least one item.", "error")
                return redirect(url_for("manager.participants"))

            existing = data.get_user_by_email(email)
            if existing and existing["role"] != "participant":
                flash("That email belongs to a non-participant account.", "error")
                return redirect(url_for("manager.participants"))
            try:
                data.register(existing["id"] if existing else None, event_id, item_ids,
                              None if existing else {"name": name, "email": email, "college": college, "roll_number": roll_number})
            except (ValueError, mysql.connector.IntegrityError) as exc:
                flash(str(exc) if isinstance(exc, ValueError) else "Invalid or duplicate registration.", "error")
                return redirect(url_for("manager.participants"))
            flash("Participant registered for selected items.", "success")
        return redirect(url_for("manager.participants"))

    # Build list of participants for assigned events
    rows = []
    for e in events:
        for reg in data.get_registrations_for_event(e["id"]):
            p = data.get_user_by_id(reg["participantId"])
            if not p:
                continue
            item_names = [
                i["name"] for i in e["items"] if i["id"] in reg["itemIds"]
            ]
            rows.append(
                {
                    "participant": p,
                    "event": e,
                    "items": item_names,
                }
            )

    return render_template(
        "manager/participants.html",
        events=events,
        rows=rows,
    )


@manager_bp.route("/events")
@login_required(role="manager")
def events():
    user = data.get_user_by_id(session["user_id"])
    events_list = []
    for e in _assigned_events(user):
        items = [
            {
                **item,
                "participant_count": data.count_participants_for_item(item["id"]),
            }
            for item in e["items"]
        ]
        events_list.append(
            {
                **e,
                "items": items,
                "participant_count": data.count_participants_for_event(e["id"]),
            }
        )
    return render_template("manager/events.html", events=events_list, clubs_for_event=data.clubs_for_event)


@manager_bp.route("/schedule")
@login_required(role="manager")
def schedule():
    user = data.get_user_by_id(session["user_id"])
    events = _assigned_events(user)
    return render_template("manager/schedule.html", events=events)


@manager_bp.route("/results")
@login_required(role="manager")
def results():
    user = data.get_user_by_id(session["user_id"])
    events = _assigned_events(user)
    selected_id = request.args.get("event")
    selected = data.get_event_by_id(selected_id) if selected_id else (events[0] if events else None)

    if selected and selected["id"] not in (user.get("assigned_events") or []):
        selected = events[0] if events else None

    item_results_map = {}
    event_result = None
    my_team = user.get("college")
    if selected:
        for item in selected["items"]:
            rows = []
            for r in data.get_item_results(item["id"]):
                p = data.get_user_by_id(r["participantId"])
                rows.append(
                    {
                        **r,
                        "participant": p,
                        "team": (p or {}).get("college") or "—",
                    }
                )
            rows.sort(key=lambda x: (x.get("rank") is None, x.get("rank") or 999, -float(x.get("score") or 0)))
            item_results_map[item["id"]] = rows
        event_result = data.get_event_result(selected["id"])
        if event_result:
            event_result = {
                **event_result,
                "entries": sorted(
                    event_result.get("entries") or [],
                    key=lambda e: e.get("rank") or 999,
                ),
            }

    return render_template(
        "manager/results.html",
        events=events,
        selected_event=selected,
        item_results_map=item_results_map,
        event_result=event_result,
        my_team=my_team,
    )


@manager_bp.route("/profile", methods=["GET", "POST"])
@login_required(role="manager")
def profile():
    user = data.get_user_by_id(session["user_id"])
    if request.method == "POST":
        values = dict(request.form)
        values["roll_number"] = user.get("roll_number")
        try:
            data.save_user(values, user["id"])
            updated = data.get_user_by_id(user["id"])
            session["name"], session["email"] = updated["name"], updated["email"]
            flash("Profile updated.", "success")
        except (ValueError, mysql.connector.IntegrityError):
            flash("Unable to update profile; check your details.", "error")
        return redirect(url_for("manager.profile"))

    assigned = _assigned_events(user)
    return render_template("manager/profile.html", user=user, assigned=assigned)
