import os
import sqlite3
import io
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import database
from models import User

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mein-it-portal-geheimnis-2026')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = sqlite3.connect(database.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, username, role, fullname, department FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(row[0], row[1], row[2], row[3], row[4])
    except:
        return None
    return None

database.init_db()

@app.route('/health')
def health_check():
    return "OK", 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = database.get_user(username)
        if user_data and user_data['password'] == password:
            user = User(user_data['id'], user_data['username'], user_data['role'], user_data['fullname'], user_data['department'])
            login_user(user)
            return redirect(url_for('index'))
        flash('Ungültiger Benutzername oder Passwort')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        department = request.form['department']
        if database.get_user(username):
            flash('Benutzername existiert bereits.')
            return redirect(url_for('register'))
        role = 'admin' if username.lower() == 'admin' else 'user'
        database.add_user(username, password, role, fullname, department)
        flash('Registrierung erfolgreich.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    category = request.args.get('category')
    services = database.get_services(category)
    return render_template('index.html', user=current_user, services=services)

@app.route('/request/<service_id>')
@login_required
def show_request_form(service_id):
    service = database.get_service(service_id)
    return render_template('service_request.html', service=service, user=current_user)

@app.route('/request', methods=['POST'])
@login_required
def request_service():
    service_id = request.form['service_id']
    reason = request.form.get('reason', '')
    priority = database.calculate_priority(service_id, reason)
    resolution_minutes = database.get_resolution_minutes(priority)
    sla_deadline = datetime.now() + timedelta(minutes=resolution_minutes)
    database.add_request(service_id, current_user.fullname, current_user.department, reason, priority, sla_deadline)
    flash('Ihre Anfrage wurde gesendet. SLA-Deadline: ' + sla_deadline.strftime('%d.%m.%Y %H:%M'))
    return redirect(url_for('requests_list'))

@app.route('/requests')
@login_required
def requests_list():
    reqs = database.get_requests(user_name=current_user.fullname)
    return render_template('requests.html', requests=reqs, now=datetime.now())

@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    try:
        stats = database.get_ticket_stats()
        inv_count = database.get_inventory_count()
        requests_all = database.get_all_requests()
        return render_template('admin.html', requests=requests_all, stats=stats, inv_count=inv_count, now=datetime.now())
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/admin/update/<int:request_id>', methods=['POST'])
@login_required
def admin_update_request(request_id):
    if current_user.role == 'admin':
        new_status = request.form['status']
        admin_note = request.form.get('reason', '')
        database.update_request_status(request_id, new_status, admin_note)
        flash('Status aktualisiert.')
    return redirect(url_for('admin_panel'))

@app.route('/admin/cmdb', methods=['GET', 'POST'])
@login_required
def admin_cmdb():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        inventory_data = {
            'asset_tag': request.form['asset_tag'],
            'geraetetyp': request.form['geraetetyp'],
            'hersteller_modell': request.form['hersteller_modell'],
            'seriennummer': request.form['seriennummer'],
            'kaufdatum': request.form['kaufdatum'],
            'status': request.form['status'],
            'nutzer_standort': request.form['nutzer_standort'],
            'garantie_bis': request.form['garantie_bis'],
            'lizenz_bis': request.form['lizenz_bis'],
            'user': current_user.username
        }
        success = database.add_inventory_item(inventory_data)
        if success:
            flash('Inventar erfolgreich aktualisiert.')
        else:
            flash('Fehler: Asset-Tag bereits vorhanden.')
        return redirect(url_for('admin_cmdb'))
    items = database.get_inventory()
    return render_template('cmdb.html', items=items)

@app.route('/admin/add_service', methods=['GET', 'POST'])
@login_required
def add_service_form():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        service_data = {
            'id': request.form['id'], 'name': request.form['name'], 'category': request.form['category'],
            'availability': request.form['availability'], 'description_business': request.form['description_business'],
            'description_technical': request.form['description_technical'], 'sla': request.form['sla'], 'costs': request.form['costs']
        }
        database.add_service(service_data)
        flash('Service hinzugefügt.')
        return redirect(url_for('index'))
    return render_template('add_service.html')

@app.route('/admin/export/tickets')
@login_required
def export_tickets_excel():
    if current_user.role != 'admin':
        return "Zugriff verweigert", 403
    tickets = database.get_all_requests()
    if not tickets:
        flash("Keine Daten vorhanden.")
        return redirect(url_for('admin_panel'))
    try:
        df = pd.DataFrame(tickets)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='IT_Tickets')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='IT_Report_2026.xlsx')
    except Exception as e:
        flash(f"Export-Fehler: {str(e)}")
        return redirect(url_for('admin_panel'))

@app.route('/admin/kedb')
@login_required
def kedb_list():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    errors = database.get_known_errors()
    return render_template('kedb.html', errors=errors)

@app.route('/admin/kedb/add', methods=['POST'])
@login_required
def kedb_add():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    error_code = request.form['error_code']
    description = request.form['description']
    workaround = request.form['workaround']
    solution = request.form['solution']
    database.add_known_error(error_code, description, workaround, solution)
    flash('Known Error hinzugefügt.')
    return redirect(url_for('kedb_list'))

@app.route('/admin/services')
@login_required
def manage_services():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, category, active FROM services ORDER BY category, name")
    rows = c.fetchall()
    conn.close()
    services = [{'id': r[0], 'name': r[1], 'category': r[2], 'active': r[3]} for r in rows]
    return render_template('manage_services.html', services=services)

@app.route('/admin/service/toggle/<service_id>', methods=['POST'])
@login_required
def toggle_service_status(service_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT active FROM services WHERE id=?", (service_id,))
    row = c.fetchone()
    if row:
        new_status = 0 if row[0] == 1 else 1
        c.execute("UPDATE services SET active = ? WHERE id=?", (new_status, service_id))
        conn.commit()
        flash(f'Service {service_id} wurde {"aktiviert" if new_status == 1 else "deaktiviert"}.')
    else:
        flash('Service nicht gefunden.')
    conn.close()
    return redirect(url_for('manage_services'))

@app.route('/admin/check_inventory/<service_id>')
@login_required
def check_inventory(service_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    service = database.get_service(service_id)
    if not service:
        flash('Service nicht gefunden.')
        return redirect(url_for('admin_panel'))
    
    # Suchbegriff aus dem Servicenamen extrahieren (vor Klammer oder Komma)
    full_name = service['name']
    search_term = full_name.split('(')[0].split(',')[0].strip()
    
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("SELECT asset_tag, geraetetyp, status FROM inventory WHERE geraetetyp LIKE ? OR hersteller_modell LIKE ?", 
              (f'%{search_term}%', f'%{search_term}%'))
    assets = c.fetchall()
    conn.close()
    
    if assets:
        asset_list = ", ".join([f"{a[0]} ({a[1]} - {a[2]})" for a in assets])
        flash(f'Gefundene Assets im Lager: {asset_list}')
    else:
        flash(f'Kein Asset vom Typ "{search_term}" im Lager gefunden. Bitte bestellen oder CMDB aktualisieren.')
    
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)