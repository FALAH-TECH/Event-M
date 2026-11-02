"""Admin role routes."""

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
from routes.decorators import login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/clubs", methods=["GET", "POST"])
@login_required(role="admin")
def clubs():
    if request.method == "POST":
        action = request.form.get("action")
        club = next((c for c in data.CLUBS if c["id"] == request.form.get("id")), None)
        if action in ("create", "edit"):
            name = request.form.get("name", "").strip()
            event_ids = list(dict.fromkeys(request.form.getlist("event_ids")))
            coordinator_ids = list(dict.fromkeys(request.form.getlist("coordinator_ids")))
            if action == "edit" and not club:
                flash("Club not found.", "error")
            elif not name:
                flash("Club name is required.", "error")
            elif any(c["name"].casefold() == name.casefold() and c is not club for c in data.CLUBS):
                flash("A club with that name already exists.", "error")
            elif not set(event_ids) <= {e["id"] for e in data.EVENTS} or not set(coordinator_ids) <= {u["id"] for u in data.get_managers()}:
                flash("Select valid events and faculty coordinators.", "error")
            else:
                values = {"name": name, "description": request.form.get("description", "").strip(), "event_ids": event_ids, "coordinator_ids": coordinator_ids}
                if club:
                    club.update(values)
                else:
                    data.CLUBS.append({"id": data.next_id("c", data.CLUBS), **values})
                flash("Club saved.", "success")
        elif action == "delete":
            if not club:
                flash("Club not found.", "error")
            elif any(data.get_event_by_id(eid) for eid in club["event_ids"]):
                flash("Remove the club's event associations before deleting it.", "error")
            else:
                data.CLUBS.remove(club)
                flash("Club deleted.", "success")
        return redirect(url_for("admin.clubs"))
    return render_template("admin/clubs.html", clubs=data.CLUBS, events=data.EVENTS, coordinators=data.get_managers())


@admin_bp.route("/venues", methods=["GET", "POST"])
@login_required(role="admin")
def venues():
    if request.method == "POST":
        action = request.form.get("action")
        venue = next((v for v in data.VENUES if v["id"] == request.form.get("id")), None)
        if action in ("create", "edit"):
            name = request.form.get("name", "").strip()
            if action == "edit" and not venue:
                flash("Venue not found.", "error")
            elif not name:
                flash("Venue name is required.", "error")
            elif any(v["name"].casefold() == name.casefold() and v is not venue for v in data.VENUES):
                flash("A venue with that name already exists.", "error")
            elif venue:
                old_name = venue["name"]
                venue["name"] = name
                for event in data.EVENTS:
                    if event.get("venue", "").strip().casefold() == old_name.casefold():
                        event["venue"] = name
                    for item in event["items"]:
                        if item.get("venue", "").strip().casefold() == old_name.casefold():
                            item["venue"] = name
                flash("Venue updated.", "success")
            else:
                data.VENUES.append({"id": data.next_id("v", data.VENUES), "name": name})
                flash("Venue created.", "success")
        elif action == "delete":
            if not venue:
                flash("Venue not found.", "error")
            elif any(event.get("venue", "").strip().casefold() == venue["name"].casefold() or any(item.get("venue", "").strip().casefold() == venue["name"].casefold() for item in event["items"]) for event in data.EVENTS):
                flash("Venue is still used by an event or activity.", "error")
            else:
                data.VENUES.remove(venue)
                flash("Venue deleted.", "success")
        return redirect(url_for("admin.venues"))
    return render_template("admin/venues.html", venues=data.VENUES)


@admin_bp.route("/dashboard")
@login_required(role="admin")
def dashboard():
    events = data.get_events()
    participants = data.get_participants()
    managers = data.get_managers()
    upcoming = [e for e in events if e.get("date", "") >= "2026-08-27"]
    return render_template(
        "admin/dashboard.html",
        total_events=len(events),
        total_participants=len(participants),
        total_managers=len(managers),
        upcoming_count=len(upcoming),
        upcoming=upcoming[:5],
        events=events,
    )


@admin_bp.route("/events", methods=["GET", "POST"])
@login_required(role="admin")
def events():
    if request.method == "POST":
        action = request.form.get("action")
        if action in ("create", "edit") and (not request.form.get("name", "").strip() or not request.form.get("date", "").strip() or not data.venue_by_name(request.form.get("venue", ""))):
            flash("Event name, date, and a valid venue are required.", "error")
            return redirect(url_for("admin.events"))
        if action == "create":
            new_event = {
                "id": data.next_id("e", data.EVENTS),
                "name": request.form.get("name", "").strip(),
                "description": request.form.get("description", "").strip(),
                "date": request.form.get("date", ""),
                "venue": request.form.get("venue", "").strip(),
                "banner": "/static/img/banner-tech.svg",
                "published": True,
                "items": [],
            }
            if new_event["name"]:
                data.EVENTS.append(new_event)
                flash("Event created.", "success")
            else:
                flash("Event name is required.", "error")
        elif action == "edit":
            eid = request.form.get("id")
            event = data.get_event_by_id(eid)
            if event:
                event["name"] = request.form.get("name", event["name"]).strip()
                event["description"] = request.form.get(
                    "description", event["description"]
                ).strip()
                event["date"] = request.form.get("date", event["date"])
                event["venue"] = request.form.get("venue", event["venue"]).strip()
                flash("Event updated.", "success")
        elif action == "delete":
            eid = request.form.get("id")
            data.EVENTS[:] = [e for e in data.EVENTS if e["id"] != eid]
            for club in data.CLUBS:
                club["event_ids"] = [event_id for event_id in club["event_ids"] if event_id != eid]
            flash("Event deleted.", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/events.html", events=data.get_events(), venues=data.VENUES, clubs_for_event=data.clubs_for_event)


@admin_bp.route("/events/<event_id>/items", methods=["GET", "POST"])
@login_required(role="admin")
def event_items(event_id):
    event = data.get_event_by_id(event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin.events"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            item = {
                "id": data.next_id("i", [i for e in data.EVENTS for i in e["items"]]),
                "eventId": event_id,
                "name": request.form.get("name", "").strip(),
                "category": request.form.get("category", "").strip(),
                "dateTime": request.form.get("dateTime", ""),
                "venue": request.form.get("venue", "").strip(),
                "rules": request.form.get("rules", "").strip(),
                "maxParticipants": int(request.form.get("maxParticipants") or 50),
            }
            if item["name"]:
                event["items"].append(item)
                flash("Item added.", "success")
            else:
                flash("Item name is required.", "error")
        elif action == "edit":
            iid = request.form.get("id")
            for item in event["items"]:
                if item["id"] == iid:
                    item["name"] = request.form.get("name", item["name"]).strip()
                    item["category"] = request.form.get(
                        "category", item["category"]
                    ).strip()
                    item["dateTime"] = request.form.get("dateTime", item["dateTime"])
                    item["venue"] = request.form.get("venue", item["venue"]).strip()
                    item["rules"] = request.form.get("rules", item["rules"]).strip()
                    item["maxParticipants"] = int(
                        request.form.get("maxParticipants") or item["maxParticipants"]
                    )
                    flash("Item updated.", "success")
                    break
        elif action == "delete":
            iid = request.form.get("id")
            event["items"] = [i for i in event["items"] if i["id"] != iid]
            flash("Item deleted.", "success")
        return redirect(url_for("admin.event_items", event_id=event_id))

    items_with_counts = [
        {**item, "participant_count": data.count_participants_for_item(item["id"])}
        for item in event["items"]
    ]
    return render_template(
        "admin/event_items.html", event=event, items=items_with_counts
    )


@admin_bp.route("/results", methods=["GET", "POST"])
@login_required(role="admin")
def results():
    selected_event_id = request.args.get("event") or request.form.get("eventId")
    events = data.get_events()
    selected_event = data.get_event_by_id(selected_event_id) if selected_event_id else None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "save_item_result":
            item_id = request.form.get("itemId")
            participant_id = request.form.get("participantId")
            existing = next(
                (
                    r
                    for r in data.ITEM_RESULTS
                    if r["itemId"] == item_id and r["participantId"] == participant_id
                ),
                None,
            )
            payload = {
                "rank": int(request.form.get("rank") or 0),
                "score": float(request.form.get("score") or 0),
                "medal": request.form.get("medal", ""),
                "published": request.form.get("published") == "on",
            }
            if existing:
                existing.update(payload)
            else:
                data.ITEM_RESULTS.append(
                    {
                        "id": data.next_id("ir", data.ITEM_RESULTS),
                        "itemId": item_id,
                        "participantId": participant_id,
                        **payload,
                    }
                )
            flash("Item result saved.", "success")
        elif action == "publish_item":
            item_id = request.form.get("itemId")
            for r in data.ITEM_RESULTS:
                if r["itemId"] == item_id:
                    r["published"] = True
            flash("Item results published.", "success")
        elif action == "save_event_result":
            event_id = request.form.get("eventId")
            er = data.get_event_result(event_id)
            colleges = request.form.getlist("college")
            ranks = request.form.getlist("rank")
            points = request.form.getlist("points")
            notes = request.form.getlist("note")
            entries = []
            for i, college in enumerate(colleges):
                if college.strip():
                    entries.append(
                        {
                            "college": college.strip(),
                            "rank": int(ranks[i] or 0),
                            "points": int(points[i] or 0),
                            "note": notes[i] if i < len(notes) else "",
                        }
                    )
            published = request.form.get("published") == "on"
            if er:
                er["entries"] = entries
                er["published"] = published
            else:
                data.EVENT_RESULTS.append(
                    {
                        "id": data.next_id("er", data.EVENT_RESULTS),
                        "eventId": event_id,
                        "entries": entries,
                        "published": published,
                    }
                )
            flash("Event overall result saved.", "success")
        return redirect(url_for("admin.results", event=selected_event_id))

    item_results_map = {}
    event_result = None
    regs_by_item = {}
    if selected_event:
        for item in selected_event["items"]:
            item_results_map[item["id"]] = data.get_item_results(item["id"])
            regs_by_item[item["id"]] = [
                data.get_user_by_id(r["participantId"])
                for r in data.get_registrations()
                if item["id"] in r["itemIds"]
            ]
        event_result = data.get_event_result(selected_event["id"])

    return render_template(
        "admin/results.html",
        events=events,
        selected_event=selected_event,
        item_results_map=item_results_map,
        regs_by_item=regs_by_item,
        event_result=event_result,
        participants=data.get_participants(),
    )


@admin_bp.route("/team-managers", methods=["GET", "POST"])
@login_required(role="admin")
def team_managers():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            email = request.form.get("email", "").strip()
            if data.get_user_by_email(email):
                flash("Email already in use.", "error")
            else:
                assigned = request.form.getlist("assigned_events")
                data.USERS.append(
                    {
                        "id": data.next_id("u", data.USERS),
                        "name": request.form.get("name", "").strip(),
                        "email": email,
                        "password": request.form.get("password") or "manager123",
                        "role": "manager",
                        "college": request.form.get("college", "").strip(),
                        "roll_number": None,
                        "assigned_events": assigned,
                    }
                )
                flash("Faculty coordinator created.", "success")
        elif action == "edit":
            uid = request.form.get("id")
            user = data.get_user_by_id(uid)
            if user and user["role"] == "manager":
                user["name"] = request.form.get("name", user["name"]).strip()
                user["email"] = request.form.get("email", user["email"]).strip()
                user["college"] = request.form.get("college", user.get("college", "")).strip()
                user["assigned_events"] = request.form.getlist("assigned_events")
                new_pw = request.form.get("password", "").strip()
                if new_pw:
                    user["password"] = new_pw
                flash("Faculty coordinator updated.", "success")
        elif action == "delete":
            uid = request.form.get("id")
            manager = data.get_user_by_id(uid)
            if manager and manager["role"] == "manager":
                data.USERS.remove(manager)
                for club in data.CLUBS:
                    club["coordinator_ids"] = [cid for cid in club["coordinator_ids"] if cid != uid]
                flash("Faculty coordinator removed.", "success")
            else:
                flash("Faculty coordinator not found.", "error")
        return redirect(url_for("admin.team_managers"))

    managers = data.get_managers()
    return render_template(
        "admin/team_managers.html",
        managers=managers,
        events=data.get_events(),
    )


@admin_bp.route("/data-entry", methods=["GET", "POST"])
@login_required(role="admin")
def data_entry():
    if request.method == "POST":
        entry_type = request.form.get("entry_type")
        if entry_type == "participant":
            email = request.form.get("email", "").strip()
            if data.get_user_by_email(email):
                flash("Participant email already exists.", "error")
            else:
                data.USERS.append(
                    {
                        "id": data.next_id("u", data.USERS),
                        "name": request.form.get("name", "").strip(),
                        "email": email,
                        "password": request.form.get("password") or "part123",
                        "role": "participant",
                        "college": request.form.get("college", "").strip(),
                        "roll_number": request.form.get("roll_number", "").strip(),
                    }
                )
                flash("Participant added.", "success")
        elif entry_type == "event":
            if not request.form.get("name", "").strip() or not request.form.get("date", "").strip() or not data.venue_by_name(request.form.get("venue", "")):
                flash("Event name, date, and a valid venue are required.", "error")
                return redirect(url_for("admin.data_entry"))
            data.EVENTS.append(
                {
                    "id": data.next_id("e", data.EVENTS),
                    "name": request.form.get("name", "").strip(),
                    "description": request.form.get("description", "").strip(),
                    "date": request.form.get("date", ""),
                    "venue": request.form.get("venue", "").strip(),
                    "banner": "/static/img/banner-tech.svg",
                    "published": True,
                    "items": [],
                }
            )
            flash("Event added.", "success")
        elif entry_type == "item":
            event_id = request.form.get("eventId")
            event = data.get_event_by_id(event_id)
            if event:
                event["items"].append(
                    {
                        "id": data.next_id(
                            "i", [i for e in data.EVENTS for i in e["items"]]
                        ),
                        "eventId": event_id,
                        "name": request.form.get("name", "").strip(),
                        "category": request.form.get("category", "").strip(),
                        "dateTime": request.form.get("dateTime", ""),
                        "venue": request.form.get("venue", "").strip(),
                        "rules": request.form.get("rules", "").strip(),
                        "maxParticipants": int(
                            request.form.get("maxParticipants") or 50
                        ),
                    }
                )
                flash("Item added to event.", "success")
            else:
                flash("Select a valid event.", "error")
        elif entry_type == "registration":
            pid = request.form.get("participantId")
            eid = request.form.get("eventId")
            item_ids = request.form.getlist("itemIds")
            if pid and eid and item_ids:
                data.REGISTRATIONS.append(
                    {
                        "id": data.next_id("r", data.REGISTRATIONS),
                        "participantId": pid,
                        "eventId": eid,
                        "itemIds": item_ids,
                    }
                )
                flash("Registration created.", "success")
            else:
                flash("Participant, event, and at least one item required.", "error")
        return redirect(url_for("admin.data_entry"))

    return render_template(
        "admin/data_entry.html",
        events=data.get_events(),
        participants=data.get_participants(),
        venues=data.VENUES,
    )


@admin_bp.route("/participants")
@login_required(role="admin")
def participants():
    q = (request.args.get("q") or "").strip().lower()
    people = data.get_participants()
    if q:
        people = [
            p
            for p in people
            if q in p["name"].lower()
            or q in p["email"].lower()
            or q in (p.get("college") or "").lower()
            or q in (p.get("roll_number") or "").lower()
        ]

    enriched = []
    for p in people:
        regs = data.get_registrations_for_participant(p["id"])
        item_count = sum(len(r["itemIds"]) for r in regs)
        enriched.append({**p, "reg_count": len(regs), "item_count": item_count})

    return render_template(
        "admin/participants.html", participants=enriched, q=q
    )


@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required(role="admin")
def profile():
    user = data.get_user_by_id(session["user_id"])
    if request.method == "POST":
        user["name"] = request.form.get("name", user["name"]).strip()
        user["email"] = request.form.get("email", user["email"]).strip()
        new_pw = request.form.get("password", "").strip()
        if new_pw:
            user["password"] = new_pw
        session["name"] = user["name"]
        session["email"] = user["email"]
        flash("Profile updated.", "success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html", user=user)
