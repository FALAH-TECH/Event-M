"""Participant role routes."""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)

import data
import mysql.connector
from routes.decorators import login_required

participant_bp = Blueprint("participant", __name__)


@participant_bp.route("/home")
@login_required(role="participant")
def home():
    user = data.get_user_by_id(session["user_id"])
    regs = data.get_registrations_for_participant(user["id"])

    registered_items = []
    upcoming_events = []
    seen_events = set()

    for reg in regs:
        event = data.get_event_by_id(reg["eventId"])
        if not event or not event["published"]:
            continue
        if event["id"] not in seen_events:
            upcoming_events.append(event)
            seen_events.add(event["id"])
        for item in event["items"]:
            if item["id"] in reg["itemIds"]:
                registered_items.append({"event": event, "item": item})

    all_events = [event for event in data.get_events() if event["published"]]
    return render_template(
        "participant/home.html",
        user=user,
        registered_items=registered_items,
        upcoming_events=upcoming_events or all_events[:2],
        all_events=all_events,
        clubs_for_event=data.clubs_for_event,
    )


def _student():
    user = data.get_user_by_id(session["user_id"])
    if not user or user.get("role") != "participant":
        session.clear()
        abort(403)
    return user


@participant_bp.route("/events")
@login_required(role="participant")
def events():
    _student()
    return render_template("participant/events.html", events=[e for e in data.get_events() if e["published"]])


@participant_bp.route("/events/<event_id>")
@login_required(role="participant")
def event_detail(event_id):
    user = _student()
    event = data.get_event_by_id(event_id)
    if not event or not event["published"]:
        abort(404)
    regs = data.get_registrations_for_participant(user["id"])
    selected = {iid for r in regs if r["eventId"] == event_id for iid in r["itemIds"]}
    activities = []
    for item in event["items"]:
        available = max(0, item["maxParticipants"] - data.count_participants_for_item(item["id"]))
        activities.append({"item": item, "available": available, "registered": item["id"] in selected})
    return render_template("participant/event_detail.html", event=event, activities=activities)


@participant_bp.route("/events/<event_id>/register", methods=["POST"])
@login_required(role="participant")
def register_event(event_id):
    user = _student()
    try:
        added = data.register(user["id"], event_id, request.form.getlist("itemIds"))
        flash("Registration successful." if added else "You are already registered for the selected activities.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("participant.event_detail", event_id=event_id))


@participant_bp.route("/registrations")
@login_required(role="participant")
def registrations():
    user = _student()
    rows = []
    for reg in data.get_registrations_for_participant(user["id"]):
        event = data.get_event_by_id(reg["eventId"])
        if event and event["published"]:
            rows.append({"event": event, "items": [i for i in event["items"] if i["id"] in reg["itemIds"]]})
    return render_template("participant/registrations.html", rows=rows)


@participant_bp.route("/results")
@login_required(role="participant")
def results():
    user = data.get_user_by_id(session["user_id"])
    regs = data.get_registrations_for_participant(user["id"])

    per_item = []
    overall = []
    seen_overall = set()
    my_team = user.get("college")

    for reg in regs:
        event = data.get_event_by_id(reg["eventId"])
        if not event:
            continue
        for item in event["items"]:
            if item["id"] not in reg["itemIds"]:
                continue
            rows = []
            my_result = None
            for r in data.get_item_results(item["id"], published_only=True):
                p = data.get_user_by_id(r["participantId"])
                row = {
                    **r,
                    "participant": p,
                    "team": (p or {}).get("college") or "—",
                    "is_me": r["participantId"] == user["id"],
                }
                if row["is_me"]:
                    my_result = row
                rows.append(row)
            rows.sort(
                key=lambda x: (x.get("rank") is None, x.get("rank") or 999, -float(x.get("score") or 0))
            )
            per_item.append(
                {
                    "event": event,
                    "item": item,
                    "results": rows,
                    "my_result": my_result,
                }
            )

        if event["id"] in seen_overall:
            continue
        seen_overall.add(event["id"])
        er = data.get_event_result(event["id"], published_only=True)
        if er:
            entries = sorted(er.get("entries") or [], key=lambda e: e.get("rank") or 999)
            team_entry = next(
                (e for e in entries if e.get("college") == my_team),
                None,
            )
            overall.append(
                {
                    "event": event,
                    "entries": entries,
                    "published": er.get("published"),
                    "my_team": team_entry,
                }
            )

    return render_template(
        "participant/results.html",
        per_item=per_item,
        overall=overall,
        my_team=my_team,
        user=user,
    )


@participant_bp.route("/schedule")
@login_required(role="participant")
def schedule():
    user = data.get_user_by_id(session["user_id"])
    regs = data.get_registrations_for_participant(user["id"])

    date_filter = request.args.get("date", "").strip()
    category_filter = request.args.get("category", "").strip()

    schedule_data = []
    categories = set()

    for reg in regs:
        event = data.get_event_by_id(reg["eventId"])
        if not event:
            continue
        items = []
        for item in event["items"]:
            if item["id"] not in reg["itemIds"]:
                continue
            categories.add(item["category"])
            if category_filter and item["category"] != category_filter:
                continue
            if date_filter and not item["dateTime"].startswith(date_filter):
                continue
            items.append(item)
        if items or (not date_filter and not category_filter):
            # Show event even if filters emptied items? Prefer only if items match
            if items:
                schedule_data.append({"event": event, "items": items})

    # If no registrations, show all public events as browse schedule
    if not regs and not schedule_data:
        for event in data.get_events():
            items = event["items"]
            if category_filter:
                items = [i for i in items if i["category"] == category_filter]
            if date_filter:
                items = [i for i in items if i["dateTime"].startswith(date_filter)]
            if items:
                schedule_data.append({"event": event, "items": items})

    return render_template(
        "participant/schedule.html",
        schedule_data=schedule_data,
        categories=sorted(categories) or sorted(
            {i["category"] for e in data.get_events() for i in e["items"]}
        ),
        date_filter=date_filter,
        category_filter=category_filter,
    )


@participant_bp.route("/profile", methods=["GET", "POST"])
@login_required(role="participant")
def profile():
    user = data.get_user_by_id(session["user_id"])
    if request.method == "POST":
        try:
            data.save_user(dict(request.form), user["id"])
            updated = data.get_user_by_id(user["id"])
            session["name"], session["email"] = updated["name"], updated["email"]
            flash("Profile updated.", "success")
        except (ValueError, mysql.connector.IntegrityError):
            flash("Unable to update profile; check your details.", "error")
        return redirect(url_for("participant.profile"))

    regs = data.get_registrations_for_participant(user["id"])
    reg_rows = []
    for r in regs:
        event = data.get_event_by_id(r["eventId"])
        if not event:
            continue
        item_names = [i["name"] for i in event["items"] if i["id"] in r["itemIds"]]
        reg_rows.append({"event": event, "items": item_names})
    return render_template(
        "participant/profile.html", user=user, reg_rows=reg_rows
    )
