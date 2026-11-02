"""Repository translating the MySQL schema into the dictionaries used by views."""
from contextlib import contextmanager
from datetime import date, datetime
from werkzeug.security import generate_password_hash
import database


@contextmanager
def cursor(write=False):
    with database.transaction() as connection:
        cur = connection.cursor(dictionary=True)
        try:
            yield cur
        finally:
            cur.close()


def fetch(sql, params=()):
    with cursor() as c:
        c.execute(sql, params)
        return c.fetchall()


def one(sql, params=()):
    rows = fetch(sql, params)
    return rows[0] if rows else None


def _user(row):
    if row:
        row['assigned_events'] = [r['event_id'] for r in fetch('SELECT event_id FROM coordinator_events WHERE coordinator_id=%s', (row['id'],))] if row['role'] == 'manager' else []
    return row

USER_SQL = 'SELECT u.user_id AS id,u.name,u.email,u.password_hash,u.role,c.name AS college,u.roll_number FROM users u LEFT JOIN colleges c ON c.college_id=u.college_id'

def get_users(): return [_user(r) for r in fetch(USER_SQL)]
def get_user_by_id(uid): return _user(one(USER_SQL + ' WHERE u.user_id=%s', (uid,)))
def get_user_by_email(email): return _user(one(USER_SQL + ' WHERE u.email=%s', ((email or '').strip(),)))
def get_managers(): return [u for u in get_users() if u['role'] == 'manager']
def get_participants(): return [u for u in get_users() if u['role'] == 'participant']


def get_events():
    events = fetch('SELECT e.event_id AS id,e.name,e.description,e.event_date AS date,e.banner,e.published,v.venue_name AS venue FROM events e JOIN venues v ON v.venue_id=e.venue_id ORDER BY e.event_date,e.name')
    items = fetch('SELECT a.activity_id AS id,a.event_id AS eventId,a.name,a.category,a.rules,a.max_participants AS maxParticipants,s.starts_at AS dateTime,v.venue_name AS venue FROM activities a LEFT JOIN schedules s ON s.activity_id=a.activity_id LEFT JOIN venues v ON v.venue_id=s.venue_id ORDER BY s.starts_at,a.name')
    for e in events:
        if isinstance(e['date'], date): e['date'] = e['date'].isoformat()
        e['items'] = [i for i in items if i['eventId'] == e['id']]
        for i in e['items']:
            if isinstance(i['dateTime'], datetime): i['dateTime'] = i['dateTime'].isoformat(timespec='minutes')
            i['dateTime'] = i['dateTime'] or ''
            i['category'] = i['category'] or ''
    return events

def get_event_by_id(eid): return next((e for e in get_events() if e['id'] == eid), None)
def get_item_by_id(iid):
    for e in get_events():
        for i in e['items']:
            if i['id'] == iid: return i, e
    return None, None

def get_venues(): return fetch('SELECT venue_id AS id,venue_name AS name FROM venues ORDER BY venue_name')
def venue_by_name(name): return one('SELECT venue_id AS id,venue_name AS name FROM venues WHERE venue_name=%s', (name,))

def get_clubs():
    clubs = fetch('SELECT club_id AS id,name,description FROM clubs ORDER BY name')
    events = fetch('SELECT club_id,event_id FROM club_events')
    coords = fetch('SELECT club_id,coordinator_id FROM club_coordinators')
    for c in clubs:
        c['event_ids'] = [r['event_id'] for r in events if r['club_id'] == c['id']]
        c['coordinator_ids'] = [r['coordinator_id'] for r in coords if r['club_id'] == c['id']]
    return clubs

def clubs_for_event(eid): return [c for c in get_clubs() if eid in c['event_ids']]
def clubs_for_coordinator(uid): return [c for c in get_clubs() if uid in c['coordinator_ids']]

def get_registrations():
    rows = fetch('SELECT registration_id AS id,participant_id AS participantId,event_id AS eventId FROM registrations')
    choices = fetch('SELECT registration_id,activity_id FROM registration_activities')
    for r in rows: r['itemIds'] = [i['activity_id'] for i in choices if i['registration_id'] == r['id']]
    return rows

def get_registrations_for_participant(uid): return [r for r in get_registrations() if r['participantId'] == uid]
def get_registrations_for_event(eid): return [r for r in get_registrations() if r['eventId'] == eid]
def count_participants_for_item(iid): return one('SELECT COUNT(*) AS n FROM registration_activities WHERE activity_id=%s',(iid,))['n']
def count_participants_for_event(eid): return one('SELECT COUNT(*) AS n FROM registrations WHERE event_id=%s',(eid,))['n']

def get_item_results(item_id=None, published_only=False):
    sql = 'SELECT result_id AS id,activity_id AS itemId,participant_id AS participantId,position AS `rank`,score,medal,published FROM activity_results WHERE 1=1'
    args = []
    if item_id: sql += ' AND activity_id=%s'; args.append(item_id)
    if published_only: sql += ' AND published=1'
    return fetch(sql, tuple(args))

def get_event_result(eid, published_only=False):
    row = one('SELECT event_result_id AS id,event_id AS eventId,published FROM event_results WHERE event_id=%s' + (' AND published=1' if published_only else ''), (eid,))
    if row: row['entries'] = fetch('SELECT c.name AS college,s.position AS `rank`,s.points,s.note FROM event_standings s JOIN colleges c ON c.college_id=s.college_id WHERE s.event_result_id=%s ORDER BY s.position', (row['id'],))
    return row


def _college(c, name):
    if not name: return None
    c.execute('INSERT INTO colleges (college_id,name) VALUES (%s,%s) ON DUPLICATE KEY UPDATE name=VALUES(name)', (database.new_id('cl'), name))
    c.execute('SELECT college_id FROM colleges WHERE name=%s', (name,))
    return c.fetchone()['college_id']

def save_user(values, uid=None, assignments=None):
    name, email = values.get('name','').strip(), values.get('email','').strip()
    password = values.get('password','')
    if not name or not email or '@' not in email: raise ValueError('A name and valid email are required.')
    if (not uid and len(password) < 6) or (password and len(password) < 6): raise ValueError('Password must be at least 6 characters.')
    with cursor(True) as c:
        college = _college(c, values.get('college','').strip())
        if uid:
            c.execute('UPDATE users SET name=%s,email=%s,college_id=%s,roll_number=%s WHERE user_id=%s', (name,email,college,values.get('roll_number') or None,uid))
            if password: c.execute('UPDATE users SET password_hash=%s WHERE user_id=%s', (generate_password_hash(password),uid))
        else:
            uid = database.new_id('u')
            c.execute('INSERT INTO users (user_id,name,email,password_hash,role,college_id,roll_number) VALUES (%s,%s,%s,%s,%s,%s,%s)', (uid,name,email,generate_password_hash(password),values['role'],college,values.get('roll_number') or None))
        if assignments is not None:
            c.execute('DELETE FROM coordinator_events WHERE coordinator_id=%s', (uid,))
            for eid in set(assignments): c.execute('INSERT INTO coordinator_events (coordinator_id,event_id) VALUES (%s,%s)', (uid,eid))
    return uid

def delete_user(uid):
    with cursor(True) as c:
        c.execute('DELETE FROM users WHERE user_id=%s AND role=%s', (uid,'manager'))

def save_venue(name, vid=None):
    name = name.strip()
    if not name: raise ValueError('Venue name is required.')
    with cursor(True) as c:
        if vid: c.execute('UPDATE venues SET venue_name=%s WHERE venue_id=%s', (name,vid))
        else: c.execute('INSERT INTO venues (venue_id,venue_name) VALUES (%s,%s)', (database.new_id('v'),name))

def delete_venue(vid):
    with cursor(True) as c: c.execute('DELETE FROM venues WHERE venue_id=%s', (vid,))

def _venue(c, name):
    c.execute('SELECT venue_id FROM venues WHERE venue_name=%s', (name,))
    row = c.fetchone()
    if not row: raise ValueError('Select a valid venue.')
    return row['venue_id']

def save_event(values, eid=None):
    name = values.get('name','').strip()
    if not name: raise ValueError('Event name is required.')
    try: date.fromisoformat(values.get('date',''))
    except ValueError: raise ValueError('Enter a valid event date.')
    with cursor(True) as c:
        venue = _venue(c, values.get('venue',''))
        args = (name,values.get('description','').strip(),values['date'],venue)
        if eid: c.execute('UPDATE events SET name=%s,description=%s,event_date=%s,venue_id=%s WHERE event_id=%s', (*args,eid))
        else: c.execute('INSERT INTO events (event_id,name,description,event_date,venue_id,banner,published) VALUES (%s,%s,%s,%s,%s,%s,1)', (database.new_id('e'),*args,'/static/img/banner-tech.svg'))

def delete_event(eid):
    with cursor(True) as c: c.execute('DELETE FROM events WHERE event_id=%s',(eid,))

def save_item(eid, values, iid=None):
    name = values.get('name','').strip()
    try:
        capacity = int(values.get('maxParticipants') or 50)
        starts = datetime.fromisoformat(values.get('dateTime',''))
        if not name or capacity < 1: raise ValueError()
    except ValueError: raise ValueError('Enter a valid activity name, time and positive capacity.')
    with cursor(True) as c:
        venue = _venue(c, values.get('venue','').strip())
        args = (name,values.get('category','').strip(),values.get('rules','').strip(),capacity)
        if iid:
            c.execute('UPDATE activities SET name=%s,category=%s,rules=%s,max_participants=%s WHERE activity_id=%s AND event_id=%s', (*args,iid,eid))
            c.execute('SELECT activity_id FROM activities WHERE activity_id=%s AND event_id=%s', (iid,eid))
            if not c.fetchone(): raise ValueError('Activity not found in event.')
            c.execute('INSERT INTO schedules (activity_id,venue_id,starts_at) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE venue_id=VALUES(venue_id),starts_at=VALUES(starts_at)', (iid,venue,starts))
        else:
            iid=database.new_id('i')
            c.execute('INSERT INTO activities (activity_id,event_id,name,category,rules,max_participants) VALUES (%s,%s,%s,%s,%s,%s)', (iid,eid,*args))
            c.execute('INSERT INTO schedules (activity_id,venue_id,starts_at) VALUES (%s,%s,%s)',(iid,venue,starts))

def delete_item(eid,iid):
    with cursor(True) as c:
        # Schedule is owned by the activity. Other dependencies remain protected by FKs.
        c.execute('DELETE FROM schedules WHERE activity_id=%s AND activity_id IN (SELECT activity_id FROM activities WHERE event_id=%s)',(iid,eid))
        c.execute('DELETE FROM activities WHERE activity_id=%s AND event_id=%s',(iid,eid))

def save_club(values, cid=None):
    name=values.get('name','').strip()
    if not name: raise ValueError('Club name is required.')
    events=set(values.getlist('event_ids')); coordinators=set(values.getlist('coordinator_ids'))
    with cursor(True) as c:
        for uid in coordinators:
            c.execute('SELECT user_id FROM users WHERE user_id=%s AND role=%s',(uid,'manager'))
            if not c.fetchone(): raise ValueError('Select valid faculty coordinators.')
        if cid:
            c.execute('UPDATE clubs SET name=%s,description=%s WHERE club_id=%s',(name,values.get('description','').strip(),cid))
            c.execute('DELETE FROM club_events WHERE club_id=%s',(cid,)); c.execute('DELETE FROM club_coordinators WHERE club_id=%s',(cid,))
        else:
            cid=database.new_id('c'); c.execute('INSERT INTO clubs (club_id,name,description) VALUES (%s,%s,%s)',(cid,name,values.get('description','').strip()))
        for eid in events: c.execute('INSERT INTO club_events (club_id,event_id) VALUES (%s,%s)',(cid,eid))
        for uid in coordinators: c.execute('INSERT INTO club_coordinators (club_id,coordinator_id) VALUES (%s,%s)',(cid,uid))

def delete_club(cid):
    with cursor(True) as c: c.execute('DELETE FROM clubs WHERE club_id=%s',(cid,))

def register(pid,eid,item_ids, new_user=None):
    item_ids=set(item_ids)
    if not item_ids: raise ValueError('Select at least one activity.')
    with cursor(True) as c:
        if new_user:
            name=new_user.get('name','').strip(); email=new_user.get('email','').strip()
            if not name or '@' not in email or not new_user.get('college','').strip() or not new_user.get('roll_number','').strip(): raise ValueError('Participant details are required.')
            college=_college(c,new_user['college'].strip()); pid=database.new_id('u')
            c.execute('INSERT INTO users (user_id,name,email,password_hash,role,college_id,roll_number) VALUES (%s,%s,%s,%s,%s,%s,%s)',(pid,name,email,generate_password_hash('part123'),'participant',college,new_user['roll_number'].strip()))
        c.execute('SELECT user_id FROM users WHERE user_id=%s AND role=%s',(pid,'participant'))
        if not c.fetchone(): raise ValueError('Select a valid participant.')
        for iid in item_ids:
            c.execute('SELECT activity_id FROM activities WHERE activity_id=%s AND event_id=%s',(iid,eid))
            if not c.fetchone(): raise ValueError('Each activity must belong to the selected event.')
        rid=database.new_id('r')
        c.execute('INSERT INTO registrations (registration_id,participant_id,event_id) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE registration_id=registration_id',(rid,pid,eid))
        c.execute('SELECT registration_id FROM registrations WHERE participant_id=%s AND event_id=%s',(pid,eid)); rid=c.fetchone()['registration_id']
        for iid in item_ids: c.execute('INSERT INTO registration_activities (registration_id,activity_id,event_id) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE activity_id=activity_id',(rid,iid,eid))

def save_item_result(eid,iid,pid,rank,score,medal,published):
    try:
        rank=int(rank or 0); score=float(score or 0)
        if rank < 0 or score < 0 or score != score or score > 999999.99 or len(medal)>20: raise ValueError()
    except ValueError: raise ValueError('Enter a valid rank and score.')
    with cursor(True) as c:
        c.execute('SELECT ra.activity_id FROM registration_activities ra JOIN registrations r ON r.registration_id=ra.registration_id WHERE ra.event_id=%s AND ra.activity_id=%s AND r.participant_id=%s',(eid,iid,pid))
        if not c.fetchone(): raise ValueError('Participant must be registered for this activity.')
        c.execute('INSERT INTO activity_results (result_id,activity_id,participant_id,position,score,medal,published) VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE position=VALUES(position),score=VALUES(score),medal=VALUES(medal),published=VALUES(published)',(database.new_id('ir'),iid,pid,rank,score,medal or None,published))

def publish_item(eid,iid):
    with cursor(True) as c: c.execute('UPDATE activity_results SET published=1 WHERE activity_id=%s AND activity_id IN (SELECT activity_id FROM activities WHERE event_id=%s)',(iid,eid))

def save_event_result(eid,entries,published):
    with cursor(True) as c:
        rid=database.new_id('er')
        c.execute('INSERT INTO event_results (event_result_id,event_id,published) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE published=VALUES(published)',(rid,eid,published))
        c.execute('SELECT event_result_id FROM event_results WHERE event_id=%s',(eid,)); rid=c.fetchone()['event_result_id']
        c.execute('DELETE FROM event_standings WHERE event_result_id=%s',(rid,))
        for entry in entries:
            try:
                rank=int(entry['rank']); points=int(entry['points'])
                if rank < 1 or points < 0: raise ValueError()
            except ValueError: raise ValueError('Standings require a positive rank and nonnegative points.')
            college=_college(c,entry['college'])
            c.execute('INSERT INTO event_standings (event_result_id,college_id,position,points,note) VALUES (%s,%s,%s,%s,%s)',(rid,college,rank,points,entry['note']))
