"""
Dummy data for the Event Management System.
Stands in for a database until wired to a real backend.
"""

from copy import deepcopy

USERS = [
    {
        "id": "u1",
        "name": "Admin User",
        "email": "admin@eventhub.edu",
        "password": "admin123",
        "role": "admin",
        "college": "EventHub HQ",
        "roll_number": None,
    },
    {
        "id": "u2",
        "name": "Priya Sharma",
        "email": "priya@mit.edu",
        "password": "manager123",
        "role": "manager",
        "college": "MIT College of Engineering",
        "roll_number": None,
        "assigned_events": ["e1", "e2"],
    },
    {
        "id": "u3",
        "name": "Rahul Mehta",
        "email": "rahul@vit.edu",
        "password": "manager123",
        "role": "manager",
        "college": "VIT University",
        "roll_number": None,
        "assigned_events": ["e1"],
    },
    {
        "id": "u4",
        "name": "Ananya Reddy",
        "email": "ananya@student.edu",
        "password": "part123",
        "role": "participant",
        "college": "MIT College of Engineering",
        "roll_number": "MIT2024001",
    },
    {
        "id": "u5",
        "name": "Karthik Nair",
        "email": "karthik@student.edu",
        "password": "part123",
        "role": "participant",
        "college": "VIT University",
        "roll_number": "VIT2024088",
    },
    {
        "id": "u6",
        "name": "Sneha Patel",
        "email": "sneha@student.edu",
        "password": "part123",
        "role": "participant",
        "college": "MIT College of Engineering",
        "roll_number": "MIT2024015",
    },
    {
        "id": "u7",
        "name": "Arjun Das",
        "email": "arjun@student.edu",
        "password": "part123",
        "role": "participant",
        "college": "SRM Institute",
        "roll_number": "SRM2024033",
    },
    {
        "id": "u8",
        "name": "Meera Iyer",
        "email": "meera@student.edu",
        "password": "part123",
        "role": "participant",
        "college": "VIT University",
        "roll_number": "VIT2024120",
    },
]

EVENTS = [
    {
        "id": "e1",
        "name": "Aether Tech Fest 2026",
        "description": "Annual inter-college technology festival featuring coding, robotics, and design competitions.",
        "date": "2026-09-15",
        "venue": "Main Campus Auditorium",
        "banner": "/static/img/banner-tech.svg",
        "published": True,
        "items": [
            {
                "id": "i1",
                "eventId": "e1",
                "name": "CodeSprint",
                "category": "Programming",
                "dateTime": "2026-09-15T10:00",
                "venue": "Lab Block A",
                "rules": "Teams of 2. 3-hour coding contest. Languages: C++, Java, Python.",
                "maxParticipants": 60,
            },
            {
                "id": "i2",
                "eventId": "e1",
                "name": "RoboRace",
                "category": "Robotics",
                "dateTime": "2026-09-15T14:00",
                "venue": "Sports Ground",
                "rules": "Line-following robots only. Track obstacles allowed. Max bot size 30cm.",
                "maxParticipants": 40,
            },
            {
                "id": "i3",
                "eventId": "e1",
                "name": "UI/UX Challenge",
                "category": "Design",
                "dateTime": "2026-09-16T09:30",
                "venue": "Design Studio",
                "rules": "Individual. Redesign a given app flow in 4 hours. Figma preferred.",
                "maxParticipants": 50,
            },
            {
                "id": "i4",
                "eventId": "e1",
                "name": "Hackathon Night",
                "category": "Hackathon",
                "dateTime": "2026-09-16T18:00",
                "venue": "Innovation Hub",
                "rules": "Teams of 3–4. 12-hour build. Theme announced on-site.",
                "maxParticipants": 80,
            },
        ],
    },
    {
        "id": "e2",
        "name": "Rhythm Cultural Night",
        "description": "Celebrating arts and culture with music, dance, and drama competitions across colleges.",
        "date": "2026-10-05",
        "venue": "Open Air Amphitheatre",
        "banner": "/static/img/banner-cultural.svg",
        "published": True,
        "items": [
            {
                "id": "i5",
                "eventId": "e2",
                "name": "Solo Singing",
                "category": "Music",
                "dateTime": "2026-10-05T11:00",
                "venue": "Amphitheatre Stage",
                "rules": "Max 5 minutes. Karaoke tracks allowed. Original or covers.",
                "maxParticipants": 30,
            },
            {
                "id": "i6",
                "eventId": "e2",
                "name": "Group Dance",
                "category": "Dance",
                "dateTime": "2026-10-05T15:00",
                "venue": "Amphitheatre Stage",
                "rules": "4–10 members. Max 8 minutes. Props allowed.",
                "maxParticipants": 100,
            },
            {
                "id": "i7",
                "eventId": "e2",
                "name": "Short Film",
                "category": "Film",
                "dateTime": "2026-10-06T10:00",
                "venue": "Media Hall",
                "rules": "Max 10 minutes runtime. Submit MP4 by deadline. Any genre.",
                "maxParticipants": 40,
            },
            {
                "id": "i8",
                "eventId": "e2",
                "name": "Debate Finals",
                "category": "Literary",
                "dateTime": "2026-10-06T14:00",
                "venue": "Seminar Hall 2",
                "rules": "Teams of 2. British Parliamentary format. Topics given 30 min prior.",
                "maxParticipants": 32,
            },
        ],
    },
]

# Provisional application-only stores. Activity locations remain free text.
VENUES = [
    {"id": f"v{index}", "name": name}
    for index, name in enumerate(dict.fromkeys(
        [event["venue"] for event in EVENTS] +
        [item["venue"] for event in EVENTS for item in event["items"]]
    ), 1)
]
CLUBS = []


def clubs_for_event(event_id):
    return [club for club in CLUBS if event_id in club["event_ids"]]


def clubs_for_coordinator(user_id):
    return [club for club in CLUBS if user_id in club["coordinator_ids"]]


def venue_by_name(name):
    return next((venue for venue in VENUES if venue["name"] == name), None)


# Registrations: participant can register for multiple items within same event
REGISTRATIONS = [
    {"id": "r1", "participantId": "u4", "eventId": "e1", "itemIds": ["i1", "i3"]},
    {"id": "r2", "participantId": "u5", "eventId": "e1", "itemIds": ["i1", "i2", "i4"]},
    {"id": "r3", "participantId": "u6", "eventId": "e1", "itemIds": ["i2", "i3"]},
    {"id": "r4", "participantId": "u7", "eventId": "e1", "itemIds": ["i1", "i4"]},
    {"id": "r5", "participantId": "u4", "eventId": "e2", "itemIds": ["i5", "i8"]},
    {"id": "r6", "participantId": "u8", "eventId": "e2", "itemIds": ["i5", "i6"]},
    {"id": "r7", "participantId": "u5", "eventId": "e2", "itemIds": ["i7"]},
    {"id": "r8", "participantId": "u6", "eventId": "e2", "itemIds": ["i6", "i8"]},
]

# Per-item results
ITEM_RESULTS = [
    {"id": "ir1", "itemId": "i1", "participantId": "u5", "rank": 1, "score": 95, "medal": "Gold", "published": True},
    {"id": "ir2", "itemId": "i1", "participantId": "u4", "rank": 2, "score": 88, "medal": "Silver", "published": True},
    {"id": "ir3", "itemId": "i1", "participantId": "u7", "rank": 3, "score": 82, "medal": "Bronze", "published": True},
    {"id": "ir4", "itemId": "i2", "participantId": "u6", "rank": 1, "score": 90, "medal": "Gold", "published": True},
    {"id": "ir5", "itemId": "i2", "participantId": "u5", "rank": 2, "score": 85, "medal": "Silver", "published": True},
    {"id": "ir6", "itemId": "i3", "participantId": "u4", "rank": 1, "score": 92, "medal": "Gold", "published": False},
    {"id": "ir7", "itemId": "i5", "participantId": "u8", "rank": 1, "score": 94, "medal": "Gold", "published": True},
    {"id": "ir8", "itemId": "i5", "participantId": "u4", "rank": 2, "score": 87, "medal": "Silver", "published": True},
]

# Per-event aggregate / overall results
EVENT_RESULTS = [
    {
        "id": "er1",
        "eventId": "e1",
        "entries": [
            {"college": "VIT University", "rank": 1, "points": 120, "note": "Strong showing in CodeSprint & RoboRace"},
            {"college": "MIT College of Engineering", "rank": 2, "points": 110, "note": "Top in UI/UX"},
            {"college": "SRM Institute", "rank": 3, "points": 75, "note": "Hackathon finalists"},
        ],
        "published": True,
    },
    {
        "id": "er2",
        "eventId": "e2",
        "entries": [
            {"college": "VIT University", "rank": 1, "points": 100, "note": "Solo Singing & Group Dance"},
            {"college": "MIT College of Engineering", "rank": 2, "points": 90, "note": "Debate Finals"},
        ],
        "published": False,
    },
]


def get_users():
    return USERS


def get_user_by_email(email):
    email_l = (email or "").strip().lower()
    for u in USERS:
        if u["email"].lower() == email_l:
            return u
    return None


def get_user_by_id(user_id):
    for u in USERS:
        if u["id"] == user_id:
            return u
    return None


def get_events():
    return EVENTS


def get_event_by_id(event_id):
    for e in EVENTS:
        if e["id"] == event_id:
            return e
    return None


def get_item_by_id(item_id):
    for e in EVENTS:
        for item in e["items"]:
            if item["id"] == item_id:
                return item, e
    return None, None


def get_managers():
    return [u for u in USERS if u["role"] == "manager"]


def get_participants():
    return [u for u in USERS if u["role"] == "participant"]


def get_registrations():
    return REGISTRATIONS


def get_registrations_for_participant(participant_id):
    return [r for r in REGISTRATIONS if r["participantId"] == participant_id]


def get_registrations_for_event(event_id):
    return [r for r in REGISTRATIONS if r["eventId"] == event_id]


def count_participants_for_item(item_id):
    return sum(1 for r in REGISTRATIONS if item_id in r["itemIds"])


def count_participants_for_event(event_id):
    ids = {r["participantId"] for r in REGISTRATIONS if r["eventId"] == event_id}
    return len(ids)


def get_item_results(item_id=None, published_only=False):
    results = ITEM_RESULTS
    if item_id:
        results = [r for r in results if r["itemId"] == item_id]
    if published_only:
        results = [r for r in results if r.get("published")]
    return results


def get_event_result(event_id, published_only=False):
    for er in EVENT_RESULTS:
        if er["eventId"] == event_id:
            if published_only and not er.get("published"):
                return None
            return er
    return None


def next_id(prefix, collection, key="id"):
    nums = []
    for item in collection:
        raw = item.get(key, "")
        if isinstance(raw, str) and raw.startswith(prefix):
            try:
                nums.append(int(raw[len(prefix) :]))
            except ValueError:
                pass
    n = max(nums) + 1 if nums else 1
    return f"{prefix}{n}"


def snapshot():
    """Deep copy of all mutable stores (useful for resets in tests)."""
    return {
        "users": deepcopy(USERS),
        "clubs": deepcopy(CLUBS),
        "venues": deepcopy(VENUES),
        "events": deepcopy(EVENTS),
        "registrations": deepcopy(REGISTRATIONS),
        "item_results": deepcopy(ITEM_RESULTS),
        "event_results": deepcopy(EVENT_RESULTS),
    }
