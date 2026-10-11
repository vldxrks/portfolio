import os, json, sqlite3, click
from datetime import datetime, timedelta, date
from functools import wraps
from flask import Flask, g, jsonify, request, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

DB = os.environ.get("DATABASE_PATH", "slotflow.db")
HOLD = int(os.environ.get("HOLD_MINUTES", "15"))
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  pw TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user');
CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT, floor TEXT, tag TEXT,
  badge TEXT, price INTEGER, capacity INTEGER, area INTEGER, class TEXT, description TEXT,
  equipment TEXT, slots TEXT, image TEXT, featured INTEGER DEFAULT 0, kind TEXT);
CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY, code TEXT, user_id INTEGER REFERENCES users(id),
  room_id INTEGER REFERENCES rooms(id), day TEXT, slot TEXT, status TEXT, amount INTEGER,
  created_at TEXT, expires_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS uq_active ON bookings(room_id, day, slot) WHERE status IN ('pending','confirmed');
"""
EQ = ["4K Projector", "Whiteboard", "Polycom Video", "Acoustic Panels"]
ROOMS = [
 ("RM-401","Fokus Sal","4th Floor (Quiet Zone)","central","Flagship Room",45,14,48,"Class A+ (Sweden)",
  "Flagship hall featuring Scandinavian wood panels, panoramic natural light, and acoustic insulation for strategic sessions.",
  EQ,["08:30-10:00","10:00-11:30","11:30-13:00","14:00-15:30","16:00-17:30","18:00-19:30"],"room-401.jpg",1,"Boardroom"),
 ("RM-204","Arkiv Studio","2nd Floor (Workshop Hub)","","",30,8,0,"",
  "Creative studio with mobile whiteboards, warm lighting, and ergonomic furniture for design sprints.",
  ["Whiteboard","4K Projector","Acoustic Panels"],["09:00-10:30","11:00-12:30","13:00-14:30","15:00-16:30","17:00-18:30"],"room-204.jpg",0,"Studio"),
 ("RM-312","Lys Kammer","3rd Floor (Riverside)","","",22,4,0,"",
  "Compact executive Zoom pod with clear glass perimeter, climate control, and soundproofing.",
  ["Polycom Video","Acoustic Panels"],["09:30-10:30","11:00-12:00","12:30-13:30","14:00-15:00","15:30-16:30"],"room-312.jpg",0,"Focus Pod"),
 ("RM-101","Nord Forum","1st Floor (Atrium)","","",65,22,0,"",
  "Spacious lecture hall for all-hands meetings, product demos, and hybrid conferences with dual-channel audio.",
  EQ,["10:00-12:00","13:00-15:00","15:30-17:30","18:00-20:00"],"room-101.jpg",0,"Conference"),
]

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def _close(_):
    d = g.pop("db", None)
    if d: d.close()

def now(): return datetime.now().replace(microsecond=0)

def expire():
    db().execute("UPDATE bookings SET status='expired' WHERE status='pending' AND expires_at<?", (now().isoformat(),))
    db().commit()

def err(msg, code=400): return jsonify(error=msg), code

def login_required(admin=False):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if "uid" not in session: return err("Authentication required", 401)
            if admin and session.get("role") != "admin": return err("Forbidden", 403)
            return f(*a, **k)
        return w
    return deco

def user_json(u): return dict(id=u["id"], name=u["name"], email=u["email"], role=u["role"])

# ---------- auth ----------
@app.post("/api/register")
def register():
    d = request.get_json(silent=True) or {}
    email, pw, name = (d.get("email") or "").strip().lower(), d.get("password") or "", (d.get("name") or "").strip()
    if "@" not in email or len(pw) < 8 or not name: return err("Name, valid email and a password of 8+ characters are required")
    try:
        cur = db().execute("INSERT INTO users(email,name,pw) VALUES(?,?,?)", (email, name, generate_password_hash(pw)))
        db().commit()
    except sqlite3.IntegrityError:
        return err("Email already registered", 409)
    session.update(uid=cur.lastrowid, role="user")
    return jsonify(user_json(db().execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()))

@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    u = db().execute("SELECT * FROM users WHERE email=?", ((d.get("email") or "").strip().lower(),)).fetchone()
    if not u or not check_password_hash(u["pw"], d.get("password") or ""): return err("Invalid email or password", 401)
    session.update(uid=u["id"], role=u["role"])
    return jsonify(user_json(u))

@app.post("/api/logout")
def logout(): session.clear(); return jsonify(ok=True)

@app.get("/api/me")
def me():
    if "uid" not in session: return jsonify(user=None)
    u = db().execute("SELECT * FROM users WHERE id=?", (session["uid"],)).fetchone()
    return jsonify(user=user_json(u) if u else None)

# ---------- catalog ----------
@app.get("/api/rooms")
def rooms():
    expire(); n = now()
    busy = {(r["room_id"], r["day"], r["slot"]) for r in db().execute(
        "SELECT room_id,day,slot FROM bookings WHERE status IN ('pending','confirmed')")}
    out = []
    for r in db().execute("SELECT * FROM rooms ORDER BY featured DESC, id"):
        days = []
        for off in range(3):
            day = (date.today() + timedelta(off)).isoformat()
            days.append([dict(t=s, free=(r["id"], day, s) not in busy and datetime.fromisoformat(f"{day}T{s[:5]}") > n)
                         for s in json.loads(r["slots"])])
        today = days[0]
        status = "Available now" if any(s["free"] for s in today) else "Fully booked today"
        out.append(dict(id=r["id"], code=r["code"], name=r["name"], floor=r["floor"], tag=r["tag"], badge=r["badge"],
            price=r["price"], capacity=r["capacity"], area=r["area"], cls=r["class"], description=r["description"],
            equipment=json.loads(r["equipment"]), image="/static/img/" + r["image"], featured=bool(r["featured"]),
            status=status, slots=days))
    return jsonify(rooms=out)

# ---------- bookings ----------
def day_label(d):
    off = (date.fromisoformat(d) - date.today()).days
    return "Today" if off == 0 else "Tomorrow" if off == 1 else d

def booking_json(b):
    return dict(id=b["id"], code=b["code"], room=b["room"], floor=b["floor"], day=day_label(b["day"]), slot=b["slot"],
                amount=b["amount"], status=b["status"], expires_at=b["expires_at"])

@app.post("/api/bookings")
@login_required()
def create_booking():
    expire(); d = request.get_json(silent=True) or {}
    room = db().execute("SELECT * FROM rooms WHERE id=?", (d.get("room_id"),)).fetchone()
    if not room: return err("Room not found", 404)
    try: off = int(d.get("day"))
    except (TypeError, ValueError): return err("Invalid day")
    slot = d.get("slot")
    if not 0 <= off <= 2 or slot not in json.loads(room["slots"]): return err("Invalid slot")
    day = (date.today() + timedelta(off)).isoformat()
    if datetime.fromisoformat(f"{day}T{slot[:5]}") <= now(): return err("This slot has already started", 409)
    a, b = slot.split("-")
    mins = (int(b[:2]) * 60 + int(b[3:])) - (int(a[:2]) * 60 + int(a[3:]))
    n = now()
    try:
        cur = db().execute("INSERT INTO bookings(user_id,room_id,day,slot,status,amount,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)",
            (session["uid"], room["id"], day, slot, "pending", round(room["price"] * mins / 60), n.isoformat(),
             (n + timedelta(minutes=HOLD)).isoformat()))
    except sqlite3.IntegrityError:
        return err("Slot is already held or booked", 409)
    db().execute("UPDATE bookings SET code=? WHERE id=?", (f"SF-{1000 + cur.lastrowid}", cur.lastrowid)); db().commit()
    return jsonify(id=cur.lastrowid, expires_at=(n + timedelta(minutes=HOLD)).isoformat()), 201

def own(bid):
    return db().execute("SELECT * FROM bookings WHERE id=? AND user_id=?", (bid, session["uid"])).fetchone()

@app.post("/api/bookings/<int:bid>/confirm")
@login_required()
def confirm(bid):
    expire(); b = own(bid)
    if not b: return err("Not found", 404)
    if b["status"] != "pending": return err("Hold is no longer active", 409)
    db().execute("UPDATE bookings SET status='confirmed', expires_at=NULL WHERE id=?", (bid,)); db().commit()
    return jsonify(ok=True)

@app.post("/api/bookings/<int:bid>/cancel")
@login_required()
def cancel(bid):
    expire(); b = own(bid)
    if not b: return err("Not found", 404)
    if b["status"] not in ("pending", "confirmed"): return err("Booking is not active", 409)
    start = datetime.fromisoformat(f"{b['day']}T{b['slot'][:5]}")
    if b["status"] == "confirmed" and start - now() < timedelta(minutes=30):
        return err("Free cancellation is available up to 30 minutes before the start", 409)
    db().execute("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,)); db().commit()
    return jsonify(ok=True)

@app.get("/api/bookings/mine")
@login_required()
def mine():
    expire()
    rows = db().execute("""SELECT b.*, r.name room, r.floor FROM bookings b JOIN rooms r ON r.id=b.room_id
        WHERE b.user_id=? AND b.status IN ('pending','confirmed') ORDER BY b.day, b.slot""", (session["uid"],)).fetchall()
    return jsonify(bookings=[booking_json(b) for b in rows])

# ---------- admin ----------
@app.get("/api/admin/overview")
@login_required(admin=True)
def overview():
    expire(); n = now(); today = date.today().isoformat()
    statuses = [s for s in (request.args.get("status") or "").split(",") if s in ("pending", "confirmed", "cancelled", "expired")]
    q = "%" + (request.args.get("q") or "").strip().lower() + "%"
    sql = """SELECT b.*, r.name room, r.floor, r.kind, u.name uname, u.email FROM bookings b
        JOIN rooms r ON r.id=b.room_id JOIN users u ON u.id=b.user_id
        WHERE (lower(b.code) LIKE ? OR lower(u.name) LIKE ? OR lower(u.email) LIKE ? OR lower(r.name) LIKE ?)"""
    args = [q] * 4
    if statuses: sql += " AND b.status IN (%s)" % ",".join("?" * len(statuses)); args += statuses
    rows = [dict(code=r["code"], created_at=r["created_at"], user=r["uname"], email=r["email"], room=r["room"],
                 floor=r["floor"], kind=r["kind"], day=day_label(r["day"]), slot=r["slot"], status=r["status"],
                 amount=r["amount"]) for r in db().execute(sql + " ORDER BY b.id DESC LIMIT 200", args)]
    c = lambda w, *a: db().execute("SELECT COUNT(*) FROM bookings WHERE " + w, a).fetchone()[0]
    soon = (n + timedelta(minutes=5)).isoformat()
    rooms_ = db().execute("SELECT * FROM rooms ORDER BY id").fetchall()
    act = db().execute("""SELECT b.room_id,b.slot,b.status,u.name FROM bookings b JOIN users u ON u.id=b.user_id
        WHERE b.day=? AND b.status IN ('pending','confirmed')""", (today,)).fetchall()
    grid, occupied = [], 0
    for r in rooms_:
        cells = []
        for h in range(8, 22):
            hit = next((a for a in act if a["room_id"] == r["id"] and int(a["slot"][:2]) * 60 + int(a["slot"][3:5]) < (h + 1) * 60
                        and int(a["slot"][6:8]) * 60 + int(a["slot"][9:]) > h * 60), None)
            occupied += bool(hit)
            cells.append(dict(h=h, status=hit["status"] if hit else None, label=hit["name"].split()[0] if hit else None))
        grid.append(dict(name=r["name"], kind=r["kind"], cells=cells))
    return jsonify(total=c("1=1"), holds=c("status='pending'"), expiring=c("status='pending' AND expires_at<?", soon),
        occupancy=round(100 * occupied / (len(rooms_) * 14)) if rooms_ else 0, hold_minutes=HOLD,
        rooms=len(rooms_), grid=grid, rows=rows, synced=n.isoformat())

# ---------- pages ----------
@app.get("/")
def index(): return send_from_directory("static", "index.html")

@app.get("/admin")
def admin_page():
    if session.get("role") != "admin": return redirect("/?login=admin")
    return send_from_directory("static", "admin.html")

# ---------- CLI ----------
def make_user(con, email, name, pw, role):
    con.execute("INSERT INTO users(email,name,pw,role) VALUES(?,?,?,?) ON CONFLICT(email) DO UPDATE SET pw=excluded.pw, role=excluded.role",
                (email.lower(), name, generate_password_hash(pw), role))

@app.cli.command("init-db")
def init_db():
    """Create tables, seed rooms and (if ADMIN_EMAIL/ADMIN_PASSWORD are set) the admin user."""
    con = sqlite3.connect(DB); con.executescript(SCHEMA)
    for r in ROOMS:
        con.execute("INSERT OR IGNORE INTO rooms(code,name,floor,tag,badge,price,capacity,area,class,description,equipment,slots,image,featured,kind) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], json.dumps(r[10]), json.dumps(r[11]), r[12], r[13], r[14]))
    if os.environ.get("ADMIN_EMAIL") and os.environ.get("ADMIN_PASSWORD"):
        make_user(con, os.environ["ADMIN_EMAIL"], "Duty Manager", os.environ["ADMIN_PASSWORD"], "admin")
    con.commit(); con.close(); click.echo("Database ready: " + DB)

@app.cli.command("create-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
def create_admin(email, password):
    """Create or update an administrator."""
    con = sqlite3.connect(DB); con.executescript(SCHEMA)
    make_user(con, email, "Duty Manager", password, "admin"); con.commit(); con.close(); click.echo("Admin saved: " + email)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
