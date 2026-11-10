Got it — here's your full Campus Chat file now with Online Users list + Login with password. Copy this to app.py:pythonimport os
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime, timedelta
from html import escape
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campus-chat-change-this-key")
messages = []
profiles = {}
users = {}  # nickname -> hash
online = {}  # nickname -> last_seen datetime

LOGIN_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Campus Chat</title>
<style>
body{font-family:Arial;background:#1e293b;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0}
.box{background:white;padding:25px;border-radius:16px;width:90%;max-width:360px;text-align:center}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #cbd5e1;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin-top:6px}
hr{margin:18px 0;border:none;border-top:1px solid #e2e8f0}
.small{font-size:11px;color:#64748b}
</style></head>
<body><div class="box">
<h2>🎓 Campus Chat</h2>
<form action="/register" method="post">
<input name="nickname" placeholder="Choose nickname" required maxlength="20">
<input name="password" type="password" placeholder="Choose password" required>
<button>Register</button>
</form>
<hr>
<form action="/login" method="post">
<input name="nickname" placeholder="Nickname" required>
<input name="password" type="password" placeholder="Password" required>
<button style="background:#0f172a;">Login</button>
</form>
<p class="small">Student project. Not WhatsApp.</p>
</div></body></html>
"""

CHAT_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Campus Chat</title>
<style>
body{font-family:Arial;margin:0;background:#f1f5f9;display:flex}
.sidebar{width:32%;max-width:220px;background:white;border-right:1px solid #e2e8f0;height:100vh;position:fixed;left:0;top:0;overflow-y:auto;padding-top:56px}
.main{margin-left:32%;flex:1}
@media(max-width:700px){.sidebar{display:none}.main{margin-left:0}}
.header{background:#1e293b;color:white;padding:14px 16px;position:fixed;top:0;left:0;right:0;z-index:10;display:flex;justify-content:space-between}
.chat{padding:70px 12px 80px 12px}
.msg{background:white;padding:10px 12px;border-radius:12px;margin:8px 0;max-width:80%;box-shadow:0 1px 2px rgba(0,0,0,0.08)}
.me{background:#dbeafe;margin-left:auto}
.meta{font-size:11px;color:#64748b}
.sendbox{position:fixed;bottom:0;right:0;left:32%;background:white;display:flex;padding:10px;gap:8px;border-top:1px solid #e2e8f0}
@media(max-width:700px){.sendbox{left:0}}
.sendbox input{flex:1;padding:12px;border:1px solid #cbd5e1;border-radius:24px}
.sendbox button{background:#3b82f6;color:white;border:none;border-radius:20px;padding:0 20px;font-weight:bold}
.online-item{padding:10px 14px;border-bottom:1px solid #f1f5f9;font-size:14px}
.dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;margin-right:6px}
</style></head>
<body>
<div class="header"><b>🎓 Campus Chat</b><span><a href="/profile" style="color:white;text-decoration:none;">👤 {{name}}</a> | <a href="/logout" style="color:white;font-size:13px;margin-left:10px;">Logout</a></span></div>

<div class="sidebar">
<div style="padding:12px;font-weight:bold;border-bottom:1px solid #e2e8f0;">Online ({{online_users|length}})</div>
{% for u in online_users %}
<div class="online-item"><span class="dot"></span>{{u}}</div>
{% endfor %}
{% if not online_users %}<div style="padding:12px;color:#94a3b8;font-size:13px;">No one online</div>{% endif %}
</div>

<div class="main">
<div class="chat">
{% for m in messages %}<div class="msg {% if m.name==name %}me{% endif %}"><b>{{m.name}}</b><br>{{m.text}}<div class="meta">{{m.time}}</div></div>{% endfor %}
</div>
<form class="sendbox" action="/send" method="post">
<input name="text" placeholder="Write a message..." required maxlength="300" autocomplete="off"><button>Send</button>
</form>
</div>
<script>window.scrollTo(0,document.body.scrollHeight);</script>
</body></html>
"""

PROFILE_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Profile</title>
<style>body{font-family:Arial;background:#f1f5f9;margin:0}.header{background:#1e293b;color:white;padding:14px}
.box{background:white;padding:20px;border-radius:12px;width:90%;max-width:400px;margin:20px auto}
input,textarea{width:100%;padding:12px;margin:8px 0;border:1px solid #cbd5e1;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;font-weight:bold}
</style></head>
<body>
<div class="header"><a href="/chat" style="color:white;">← Back</a><b style="float:right">Profile</b></div>
<div class="box">
<form action="/profile" method="post">
<input name="display_name" value="{{profile.display_name}}" maxlength="20" required>
<input name="status" value="{{profile.status}}" placeholder="Status" maxlength="40">
<textarea name="bio" maxlength="80" placeholder="About you">{{profile.bio}}</textarea>
<button>Save</button>
</form>
</div>
</body></html>
"""

def cleanup_online():
    now = datetime.now()
    for n in list(online.keys()):
        if now - online[n] > timedelta(minutes=5):
            del online[n]

@app.route("/")
def home():
    return redirect("/chat") if "name" in session else render_template_string(LOGIN_PAGE)

@app.route("/register", methods=["POST"])
def register():
    nick = escape(request.form.get("nickname","").strip()[:20])
    pwd = request.form.get("password","")
    if not nick or not pwd: return redirect("/")
    if nick in users: return "Nickname taken <a href='/'>Go back</a>"
    users[nick] = generate_password_hash(pwd)
    session["name"] = nick
    profiles[nick] = {"display_name": nick, "status": "Online", "bio": ""}
    online[nick] = datetime.now()
    return redirect("/profile")

@app.route("/login", methods=["POST"])
def login():
    nick = escape(request.form.get("nickname","").strip()[:20])
    pwd = request.form.get("password","")
    if nick in users and check_password_hash(users[nick], pwd):
        session["name"] = nick
        online[nick] = datetime.now()
        return redirect("/chat")
    return "Wrong login <a href='/'>Go back</a>"

@app.route("/chat")
def chat():
    if "name" not in session: return redirect("/")
    online[session["name"]] = datetime.now()
    cleanup_online()
    return render_template_string(CHAT_PAGE, messages=messages, name=session["name"], online_users=list(online.keys()))

@app.route("/profile", methods=["GET","POST"])
def profile_route():
    if "name" not in session: return redirect("/")
    name = session["name"]
    online[name] = datetime.now()
    if request.method == "POST":
        profiles[name] = {
            "display_name": escape(request.form.get("display_name","")[:20]),
            "status": escape(request.form.get("status","")[:40]),
            "bio": escape(request.form.get("bio","")[:80]),
        }
        session["name"] = profiles[name]["display_name"]
        return redirect("/chat")
    prof = profiles.get(name, {"display_name": name, "status": "", "bio": ""})
    return render_template_string(PROFILE_PAGE, profile=prof)

@app.route("/send", methods=["POST"])
def send():
    if "name" not in session: return redirect("/")
    online[session["name"]] = datetime.now()
    text = request.form.get("text","").strip()
    if text:
        messages.append({"name": session["name"], "text": escape(text[:300]), "time": datetime.now().strftime("%H:%M")})
        if len(messages) > 150: messages.pop(0)
    return redirect("/chat")

@app.route("/logout")
def logout():
    if "name" in session and session["name"] in online:
        del online[session["name"]]
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
