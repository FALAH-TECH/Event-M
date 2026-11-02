"""Administrator workflows backed by the MySQL repository."""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import mysql.connector
import data
from routes.decorators import login_required

admin_bp = Blueprint('admin', __name__)


def perform(fn):
    try:
        fn()
        flash('Changes saved.', 'success')
    except ValueError as exc:
        flash(str(exc), 'error')
    except mysql.connector.IntegrityError:
        flash('The record is already in use, is duplicated, or refers to an invalid record.', 'error')


@admin_bp.route('/clubs', methods=['GET','POST'])
@login_required(role='admin')
def clubs():
    if request.method == 'POST':
        action=request.form.get('action'); cid=request.form.get('id')
        if action in ('create','edit'): perform(lambda: data.save_club(request.form, cid if action == 'edit' else None))
        elif action == 'delete': perform(lambda: data.delete_club(cid))
        return redirect(url_for('admin.clubs'))
    return render_template('admin/clubs.html',clubs=data.get_clubs(),events=data.get_events(),coordinators=data.get_managers())


@admin_bp.route('/venues', methods=['GET','POST'])
@login_required(role='admin')
def venues():
    if request.method == 'POST':
        action=request.form.get('action'); vid=request.form.get('id')
        if action in ('create','edit'): perform(lambda: data.save_venue(request.form.get('name',''), vid if action == 'edit' else None))
        elif action == 'delete': perform(lambda: data.delete_venue(vid))
        return redirect(url_for('admin.venues'))
    return render_template('admin/venues.html',venues=data.get_venues())


@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    events=data.get_events(); participants=data.get_participants(); managers=data.get_managers()
    upcoming=[e for e in events if e['date'] >= date.today().isoformat()]
    return render_template('admin/dashboard.html',total_events=len(events),total_participants=len(participants),total_managers=len(managers),upcoming_count=len(upcoming),upcoming=upcoming[:5],events=events)


@admin_bp.route('/events', methods=['GET','POST'])
@login_required(role='admin')
def events():
    if request.method == 'POST':
        action=request.form.get('action'); eid=request.form.get('id')
        if action in ('create','edit'): perform(lambda: data.save_event(request.form, eid if action == 'edit' else None))
        elif action == 'delete': perform(lambda: data.delete_event(eid))
        return redirect(url_for('admin.events'))
    return render_template('admin/events.html',events=data.get_events(),venues=data.get_venues(),clubs_for_event=data.clubs_for_event)


@admin_bp.route('/events/<event_id>/items', methods=['GET','POST'])
@login_required(role='admin')
def event_items(event_id):
    event=data.get_event_by_id(event_id)
    if not event:
        flash('Event not found.','error'); return redirect(url_for('admin.events'))
    if request.method == 'POST':
        action=request.form.get('action'); iid=request.form.get('id')
        if action in ('create','edit'): perform(lambda: data.save_item(event_id,request.form,iid if action == 'edit' else None))
        elif action == 'delete': perform(lambda: data.delete_item(event_id,iid))
        return redirect(url_for('admin.event_items',event_id=event_id))
    items=[{**i,'participant_count':data.count_participants_for_item(i['id'])} for i in event['items']]
    return render_template('admin/event_items.html',event=event,items=items,venues=data.get_venues())


@admin_bp.route('/results', methods=['GET','POST'])
@login_required(role='admin')
def results():
    eid=request.args.get('event') or request.form.get('eventId')
    if request.method == 'POST':
        action=request.form.get('action'); iid=request.form.get('itemId')
        if action == 'save_item_result': perform(lambda: data.save_item_result(eid,iid,request.form.get('participantId'),request.form.get('rank'),request.form.get('score'),request.form.get('medal',''),request.form.get('published') == 'on'))
        elif action == 'publish_item': perform(lambda: data.publish_item(eid,iid))
        elif action == 'save_event_result':
            colleges=request.form.getlist('college'); ranks=request.form.getlist('rank'); points=request.form.getlist('points'); notes=request.form.getlist('note')
            entries=[{'college':v.strip(),'rank':ranks[i] if i<len(ranks) else '', 'points':points[i] if i<len(points) else '', 'note':notes[i] if i<len(notes) else ''} for i,v in enumerate(colleges) if v.strip()]
            perform(lambda: data.save_event_result(eid,entries,request.form.get('published') == 'on'))
        return redirect(url_for('admin.results',event=eid))
    events=data.get_events(); selected=data.get_event_by_id(eid) if eid else None
    item_results_map={}; regs_by_item={}; event_result=None
    if selected:
        regs=data.get_registrations()
        for item in selected['items']:
            item_results_map[item['id']]=data.get_item_results(item['id'])
            regs_by_item[item['id']]=[data.get_user_by_id(r['participantId']) for r in regs if item['id'] in r['itemIds']]
        event_result=data.get_event_result(eid)
    return render_template('admin/results.html',events=events,selected_event=selected,item_results_map=item_results_map,regs_by_item=regs_by_item,event_result=event_result,participants=data.get_participants())


@admin_bp.route('/team-managers', methods=['GET','POST'])
@login_required(role='admin')
def team_managers():
    if request.method == 'POST':
        action=request.form.get('action'); uid=request.form.get('id')
        if action in ('create','edit'):
            user=data.get_user_by_id(uid) if action == 'edit' else None
            if action == 'edit' and (not user or user['role'] != 'manager'): flash('Faculty coordinator not found.','error')
            else:
                values=dict(request.form); values['role']='manager'; values['roll_number']=None
                if action == 'create' and not values.get('password'): values['password']='manager123'
                perform(lambda: data.save_user(values, uid if action == 'edit' else None, request.form.getlist('assigned_events')))
        elif action == 'delete': perform(lambda: data.delete_user(uid))
        return redirect(url_for('admin.team_managers'))
    return render_template('admin/team_managers.html',managers=data.get_managers(),events=data.get_events())


@admin_bp.route('/data-entry', methods=['GET','POST'])
@login_required(role='admin')
def data_entry():
    if request.method == 'POST':
        kind=request.form.get('entry_type')
        if kind == 'participant':
            values=dict(request.form); values['role']='participant'; values['password']=values.get('password') or 'part123'
            perform(lambda: data.save_user(values))
        elif kind == 'event': perform(lambda: data.save_event(request.form))
        elif kind == 'item': perform(lambda: data.save_item(request.form.get('eventId'),request.form))
        elif kind == 'registration': perform(lambda: data.register(request.form.get('participantId'),request.form.get('eventId'),request.form.getlist('itemIds')))
        return redirect(url_for('admin.data_entry'))
    return render_template('admin/data_entry.html',events=data.get_events(),participants=data.get_participants(),venues=data.get_venues())


@admin_bp.route('/participants')
@login_required(role='admin')
def participants():
    q=(request.args.get('q') or '').strip().lower(); people=data.get_participants()
    if q: people=[p for p in people if any(q in (p.get(k) or '').lower() for k in ('name','email','college','roll_number'))]
    enriched=[]
    for p in people:
        regs=data.get_registrations_for_participant(p['id']); enriched.append({**p,'reg_count':len(regs),'item_count':sum(len(r['itemIds']) for r in regs)})
    return render_template('admin/participants.html',participants=enriched,q=q)


@admin_bp.route('/profile', methods=['GET','POST'])
@login_required(role='admin')
def profile():
    user=data.get_user_by_id(session['user_id'])
    if request.method == 'POST':
        values=dict(request.form); values['college']=user.get('college') or ''; values['roll_number']=user.get('roll_number')
        perform(lambda: data.save_user(values,user['id']))
        updated=data.get_user_by_id(user['id']); session['name']=updated['name']; session['email']=updated['email']
        return redirect(url_for('admin.profile'))
    return render_template('admin/profile.html',user=user)
