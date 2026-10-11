"""End-to-end smoke test against a temporary database: python smoke_test.py"""
import os, tempfile
os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ.update(ADMIN_EMAIL="admin@test.io", ADMIN_PASSWORD="admin-pass-123", HOLD_MINUTES="15")
import app as A
from datetime import datetime
assert "ready" in A.app.test_cli_runner().invoke(A.init_db).output
c = A.app.test_client(); j = lambda r: r.get_json()
rooms = j(c.get("/api/rooms"))["rooms"]; assert len(rooms) == 4 and rooms[0]["code"] == "RM-401"
room = rooms[1]
slot = next(s["t"] for s in room["slots"][1] if s["free"])
assert c.post("/api/bookings", json={"room_id": room["id"], "day": 1, "slot": slot}).status_code == 401
assert c.post("/api/register", json={"name": "Vlad", "email": "v@test.io", "password": "password1"}).status_code == 200
r = c.post("/api/bookings", json={"room_id": room["id"], "day": 1, "slot": slot}); assert r.status_code == 201, r.data
bid = j(r)["id"]
c2 = A.app.test_client(); c2.post("/api/register", json={"name": "Other", "email": "o@test.io", "password": "password1"})
assert c2.post("/api/bookings", json={"room_id": room["id"], "day": 1, "slot": slot}).status_code == 409   # double booking blocked
assert c2.post(f"/api/bookings/{bid}/confirm").status_code == 404                                        # not your booking
assert c.post(f"/api/bookings/{bid}/confirm").status_code == 200
assert j(c.get("/api/bookings/mine"))["bookings"][0]["status"] == "confirmed"
assert not next(s for s in j(c.get("/api/rooms"))["rooms"][1]["slots"][1] if s["t"] == slot)["free"]
assert c.get("/api/admin/overview").status_code == 403 and c.get("/admin").status_code == 302
assert c.post(f"/api/bookings/{bid}/cancel").status_code == 200
assert next(s for s in j(c.get("/api/rooms"))["rooms"][1]["slots"][1] if s["t"] == slot)["free"]
# hold expiry
r = c.post("/api/bookings", json={"room_id": room["id"], "day": 2, "slot": slot}); assert r.status_code == 201
with A.app.app_context():
    A.db().execute("UPDATE bookings SET expires_at='2000-01-01T00:00:00' WHERE status='pending'"); A.db().commit()
assert c.post(f"/api/bookings/{j(r)['id']}/confirm").status_code == 409
a = A.app.test_client(); assert a.post("/api/login", json={"email": "admin@test.io", "password": "bad"}).status_code == 401
assert a.post("/api/login", json={"email": "admin@test.io", "password": "admin-pass-123"}).status_code == 200
o = j(a.get("/api/admin/overview?status=cancelled,expired")); assert o["total"] == 2 and len(o["rows"]) == 2 and a.get("/admin").status_code == 200
print("ALL OK")
