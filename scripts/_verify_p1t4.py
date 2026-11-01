"""One-shot P1 task-4 verification against the running skeleton (127.0.0.1:7860)."""
import hashlib
import json
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "http://127.0.0.1:7860"
TOKEN = "orvina-p1-verification-token-0001"


def get(path, token=None):
    req = urllib.request.Request(BASE + path)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", ""), e.read()


results = []

# 1. health (no auth)
st, ct, body = get("/api/health")
j = json.loads(body)
results.append(("health 200", st == 200, json.dumps(j)[:220]))

# 2. /api/me without token -> 401 unauthenticated, no stack trace
st, ct, body = get("/api/me")
j = json.loads(body)
results.append(("me no-token 401", st == 401, body.decode()))
results.append(("401 is JSON error", "error" in j and j["error"].get("code") == "unauthenticated", ""))

# 3. insert fake user + session
conn = sqlite3.connect(r"C:\tmp\orvina-p1\orvina.db", timeout=5)
conn.execute(
    "INSERT OR IGNORE INTO users (id, username, display_name, password_hash) VALUES (999999, 'p1verify', 'P1 Verify', 'x')"
)
exp = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
conn.execute(
    "INSERT OR REPLACE INTO sessions (token_hash, user_id, expires_at) VALUES (?, 999999, ?)",
    (hashlib.sha256(TOKEN.encode()).hexdigest(), exp),
)
conn.commit()
conn.close()

# 4. /api/me with token -> 501 not_implemented
st, ct, body = get("/api/me", TOKEN)
j = json.loads(body)
results.append(("me with-token 501", st == 501, body.decode()))

# 5. another stub (GET document)
st, ct, body = get("/api/documents/1", TOKEN)
j = json.loads(body)
results.append(("stub doc 501", st == 501 and j["error"]["code"] == "not_implemented", body.decode()[:120]))

# 6. SPA: / -> index.html
st, ct, body = get("/")
results.append(("spa / 200 html", st == 200 and "html" in ct, f"{ct} {len(body)}B"))

# 7. SPA fallback for a client route
st, ct, body = get("/dashboard")
results.append(("spa fallback 200", st == 200 and "html" in ct, f"{ct} {len(body)}B"))

# 8. unknown /api/* -> 404 JSON (not the SPA page)
st, ct, body = get("/api/nope")
results.append(("api 404 json", st == 404 and "json" in ct, body.decode()[:120]))

ok = True
for name, passed, detail in results:
    print(("PASS " if passed else "FAIL "), name, " |", detail)
    ok = ok and passed
print("ALL PASS" if ok else "SOME FAILED")
