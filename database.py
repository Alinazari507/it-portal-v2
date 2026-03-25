import sqlite3
import os
from datetime import datetime, timedelta

if not os.path.exists('data'):
    os.makedirs('data')

DB_PATH = 'data/it_portal_v2.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS services (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT, availability TEXT, 
        description_business TEXT, description_technical TEXT, sla TEXT, costs TEXT, active INTEGER DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        service_id TEXT, user_name TEXT, user_dept TEXT, status TEXT, reason TEXT, 
        priority TEXT DEFAULT 'P3', 
        sla_deadline TIMESTAMP,
        ticket_type TEXT DEFAULT 'ServiceRequest',
        resolved_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', fullname TEXT, department TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE,
        geraetetyp TEXT,
        hersteller_modell TEXT,
        seriennummer TEXT,
        kaufdatum TEXT,
        status TEXT,
        nutzer_standort TEXT,
        garantie_bis TEXT,
        lizenz_bis TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT,
        action TEXT,
        user TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(asset_tag) REFERENCES inventory(asset_tag))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sla_targets (
        priority TEXT PRIMARY KEY,
        response_minutes INTEGER,
        resolution_minutes INTEGER)''')
    c.execute("INSERT OR IGNORE INTO sla_targets VALUES ('P1', 15, 240)")
    c.execute("INSERT OR IGNORE INTO sla_targets VALUES ('P2', 30, 480)")
    c.execute("INSERT OR IGNORE INTO sla_targets VALUES ('P3', 120, 1440)")
    c.execute("INSERT OR IGNORE INTO sla_targets VALUES ('P4', 240, 2880)")
    
    c.execute('''CREATE TABLE IF NOT EXISTS known_errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        error_code TEXT,
        description TEXT,
        workaround TEXT,
        solution TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, fullname, department) VALUES (?, ?, ?, ?, ?)",
                  ('admin', 'Kein-Zugriff-fur-User-2026!', 'admin', 'System Administrator', 'IT Management'))
    
    conn.commit()
    conn.close()
    seed_data()

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        services = [
            ('HW-001', 'Standard Laptop', 'Hardware', 'Sofort', 
             'Ein voll ausgestatteter Laptop für mobile Arbeit (Windows 11, Office 365, VPN-Client).',
             'HP EliteBook 840 G10, Autopilot-Profil "Standard", BitLocker aktiviert.', 
             '3 Werktage (intern: < 4 Std.)', '0€'),
            ('SW-001', 'Adobe Acrobat', 'Software', '24h', 
             'PDF-Editor für die Bearbeitung von Dokumenten.',
             'Adobe Acrobat Pro, Lizenzzuweisung über Intune', 
             '1 Tag', '15€/Monat'),
            ('ACC-001', 'VPN-Zugang', 'Zugang & Berechtigungen', '2h', 
             'Sicherer Fernzugriff auf das Firmennetzwerk',
             'MFA via Microsoft Authenticator, Zertifikat aus Active Directory',
             '2 Stunden nach Genehmigung', '0€'),
        ]
        c.executemany("INSERT INTO services (id, name, category, availability, description_business, description_technical, sla, costs, active) VALUES (?,?,?,?,?,?,?,?,1)", services)
        conn.commit()
    conn.close()

def get_resolution_minutes(priority):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT resolution_minutes FROM sla_targets WHERE priority=?", (priority,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 1440

def calculate_priority(service_id, reason):
    service = get_service(service_id)
    if service and service['category'] == 'Hardware' and 'defekt' in reason.lower():
        return 'P2'
    return 'P3'

def get_services(category=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM services WHERE category=? AND active=1", (category,))
    else:
        c.execute("SELECT * FROM services WHERE active=1")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'category': r[2], 'availability': r[3], 
             'description_business': r[4], 'description_technical': r[5], 'sla': r[6], 'costs': r[7]} for r in rows]

def get_service(service_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM services WHERE id=?", (service_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'category': row[2], 'availability': row[3],
                'description_business': row[4], 'description_technical': row[5], 'sla': row[6], 'costs': row[7]}
    return None

def add_request(service_id, user_name, user_dept, reason="", priority="P3", sla_deadline=None, ticket_type="ServiceRequest"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO requests 
        (service_id, user_name, user_dept, status, reason, priority, sla_deadline, ticket_type) 
        VALUES (?,?,?,?,?,?,?,?)""",
        (service_id, user_name, user_dept, 'Pending', reason, priority, sla_deadline, ticket_type))
    conn.commit()
    conn.close()

def _convert_sla_deadline(value):
    """تبدیل رشته ISO به datetime (در صورت امکان)"""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None

def get_requests(user_name=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_name:
        c.execute("SELECT id, service_id, user_name, user_dept, status, reason, priority, sla_deadline, ticket_type, created_at FROM requests WHERE user_name=? ORDER BY created_at DESC", (user_name,))
    else:
        c.execute("SELECT id, service_id, user_name, user_dept, status, reason, priority, sla_deadline, ticket_type, created_at FROM requests ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            'id': r[0],
            'service_id': r[1],
            'user_name': r[2],
            'user_dept': r[3],
            'status': r[4],
            'reason': r[5],
            'priority': r[6],
            'sla_deadline': _convert_sla_deadline(r[7]),   # تبدیل به datetime
            'ticket_type': r[8],
            'date': r[9]
        })
    return result

def get_all_requests():
    return get_requests()

def update_request_status(request_id, new_status, admin_note=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if new_status in ['Completed', 'Rejected']:
        resolved_at = datetime.now().isoformat()
        if admin_note:
            c.execute("UPDATE requests SET status = ?, reason = ?, resolved_at = ? WHERE id = ?", 
                      (new_status, admin_note, resolved_at, request_id))
        else:
            c.execute("UPDATE requests SET status = ?, resolved_at = ? WHERE id = ?", 
                      (new_status, resolved_at, request_id))
    else:
        if admin_note:
            c.execute("UPDATE requests SET status = ?, reason = ? WHERE id = ?", (new_status, admin_note, request_id))
        else:
            c.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, request_id))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'password': row[2], 'role': row[3], 'fullname': row[4], 'department': row[5]}
    return None

def add_user(username, password, role='user', fullname='', department=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role, fullname, department) VALUES (?, ?, ?, ?, ?)", 
              (username, password, role, fullname, department))
    conn.commit()
    conn.close()

def add_service(s):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO services (id, name, category, availability, description_business, description_technical, sla, costs) VALUES (?,?,?,?,?,?,?,?)", 
              (s['id'], s['name'], s['category'], s['availability'], s['description_business'], s['description_technical'], s['sla'], s['costs']))
    conn.commit()
    conn.close()

def get_ticket_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) FROM requests GROUP BY status")
    stats = dict(c.fetchall())
    conn.close()
    return {'Pending': stats.get('Pending', 0), 'In Progress': stats.get('In Progress', 0), 
            'Completed': stats.get('Completed', 0), 'Approved': stats.get('Approved', 0), 
            'Rejected': stats.get('Rejected', 0), 'Checking Inventory': stats.get('Checking Inventory', 0),
            'To be Ordered': stats.get('To be Ordered', 0)}

def get_inventory_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
    conn.close()
    return count

def get_inventory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, asset_tag, geraetetyp, hersteller_modell, seriennummer, kaufdatum, status, nutzer_standort, garantie_bis, lizenz_bis FROM inventory")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'asset_tag': r[1], 'geraetetyp': r[2], 'hersteller_modell': r[3], 
             'seriennummer': r[4], 'kaufdatum': r[5], 'status': r[6], 'nutzer_standort': r[7], 
             'garantie_bis': r[8], 'lizenz_bis': r[9]} for r in rows]

def add_inventory_item(data):
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO inventory 
            (asset_tag, geraetetyp, hersteller_modell, seriennummer, kaufdatum, status, nutzer_standort, garantie_bis, lizenz_bis) 
            VALUES (?,?,?,?,?,?,?,?,?)''', 
            (data['asset_tag'], data['geraetetyp'], data['hersteller_modell'], 
             data['seriennummer'], data['kaufdatum'], data['status'], 
             data['nutzer_standort'], data['garantie_bis'], data['lizenz_bis']))
        conn.commit()
        log_inventory_action(data['asset_tag'], 'Install', data.get('user', 'system'), 'Asset hinzugefügt')
        return True
    except:
        return False
    finally:
        conn.close()

def log_inventory_action(asset_tag, action, user, details=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO inventory_log (asset_tag, action, user, details) VALUES (?,?,?,?)",
              (asset_tag, action, user, details))
    conn.commit()
    conn.close()

def update_inventory_status(asset_tag, new_status, user, details=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE inventory SET status=? WHERE asset_tag=?", (new_status, asset_tag))
    conn.commit()
    conn.close()
    log_inventory_action(asset_tag, 'Change', user, f"Status geändert zu {new_status}: {details}")

def add_known_error(error_code, description, workaround, solution):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO known_errors (error_code, description, workaround, solution) VALUES (?,?,?,?)",
              (error_code, description, workaround, solution))
    conn.commit()
    conn.close()

def get_known_errors():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, error_code, description, workaround, solution, created_at FROM known_errors ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'error_code': r[1], 'description': r[2], 'workaround': r[3], 'solution': r[4], 'created_at': r[5]} for r in rows]