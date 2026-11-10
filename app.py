import os
from flask import Flask, request, redirect, session, render_template_string, escape
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-key-123-random")

messages = []
profiles = {}  # number -> profile details

LOGIN_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login - My WhatsApp</title>
<style>
body{font-family:Arial;background:#075E54;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{background:white;padding:25px;border-radius:15px;width:90%;max-width:350px;text-align:center}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:8px;font-size:17px;font-weight:bold}
h2{color:#075E54}
</style></head>
<body><div class="box"><h2>💬 My WhatsApp</h2>
<form action="/login" method="post">
<input type="text" name="name" placeholder="Your Name" required maxlength="30">
<input type="text" name="number" placeholder="Your Number" required maxlength="15">
<button type="submit">Login</button>
</form></div></body></html>
"""

CHAT_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chat</title>
<style>
body{font-family:Arial;margin:0;background:#ECE5DD}
.header{background:#075E54;color:white;padding:15px;font-size:16px;font-weight:bold;position:fixed;top:0;left:0;right:0;display:flex;justify-content:space-between}
.chat{padding:70px 10px 80px 10px}
.msg{background:white;padding:10px 12px;border-radius:10px;margin:8px 0;max-width:80%;box-shadow:0 1px 1px #ccc}
.me{background:#DCF8C6;margin-left:auto}
small{color:#888;font-size:11px}
.sendbox{position:fixed;bottom:0;left:0;right:0;background:white;display:flex;padding:10px;gap:8px}
.sendbox input{flex:1;padding:12px;border:1px solid #ddd;border-radius:20px}
.sendbox button{background:#25D366;color:white;border:none;border-radius:50%;width:50px;height:50px;font-size:22px}
.avatar{width:32px;height:32px;border-radius:50%;background:#128C7E;display:inline-flex;justify-content:center;align-items:center;color:white;font-weight:bold;margin-right:6px}
</style></head>
<body>
<div class="header">
<span>💬 Chat</span>
<span><a href="/profile" style="color:white;text-decoration:none;">👤 {{name}}</a> | <a href="/logout" style="color:white;font-size:13px;">Logout</a></span>
</div>
<div class="chat">
{% for m in messages %}
<div class="msg {% if m['name']==name %}me{% endif %}">
<div style="display:flex;align-items:center"><div class="avatar">{{m['name'][0]|upper}}</div><b>{{m['name']}}</b></div>
<div style="margin-top:5px">{{m['text']}}</div>
<small>{{m['time']}} {% if m['bio'] %} - {{m['bio']}} {% endif %}</small>
</div>
{% endfor %}
</div>
<form class="sendbox" action="/send" method="post">
<input type="text" name="text" placeholder="Type a message..." required maxlength="500" autocomplete="off">
<button type="submit">➤</button>
</form>
<script>window.scrollTo(0,document.body.scrollHeight); setTimeout(()=>{location.reload()}, 5000);</script>
</body></html>
"""

PROFILE_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Profile</title>
<style>
body{font-family:Arial;background:#ECE5DD;margin:0}
.header{background:#075E54;color:white;padding:15px}
.box{background:white;padding:20px;border-radius:12px;width:90%;max-width:400px;margin:20px auto}
input, textarea{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:8px;font-weight:bold;font-size:16px}
.avatar-big{width:80px;height:80px;border-radius:50%;background:#128C7E;color:white;display:flex;justify-content:center;align-items:center;font-size:36px;margin:0 auto 10px}
</style></head>
<body>
<div class="header"><a href="/chat" style="color:white;text-decoration:none;">← Back to Chat</a> <b style="float:right">Profile</b></div>
<div class="box">
<div class="avatar-big">{{name[0]|upper}}</div>
<h3 style="text-align:center">{{name}}</h3>
<form action="/profile" method="post">
<input type="text" name="display_name" value="{{profile.display_name}}" placeholder="Display Name" required>
<input type="text" name="status" value="{{profile.status}}" placeholder="Status e.g. Available for chat" maxlength="50">
<textarea name="bio" placeholder="About you" rows="3" maxlength="100">{{profile.bio}}</textarea>
<input type="text" name="location" value="{{profile.location}}" placeholder="Location e.g. Kampala">
<button type="submit">Save Profile</button>
</form>
<p style="font-size:12px;color:#888;text-align:center">Number: {{number}} (private)</p>
</div>
</body></html>
"""

@app.route("/")
def home():
    if "name" in session: return redirect("/chat")
    return render_template_string(LOGIN_PAGE)

@app.route("/login", methods=["POST"])
def login():
    name = escape(request.form.get("name","").strip()[:30])
    number = escape(request.form.get("number","").strip()[:15])
    if name and number:
        session["name"] = name
        session["number"] = number
        if number not in profiles:
            profiles[number] = {"display_name": name, "status": "Hey there! I'm using My WhatsApp", "bio": "", "location": ""}
        return redirect("/profile")
    return redirect("/")

@app.route("/chat")
def chat():
    if "name" not in session: return redirect("/")
    return render_template_string(CHAT_PAGE, messages=messages, name=session["name"])

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "name" not in session: return redirect("/")
    number = session["number"]
    if request.method == "POST":
        profiles[number] = {
            "display_name": escape(request.form.get("display_name","")[:30]),
            "status": escape(request.form.get("status","")[:50]),
            "bio": escape(request.form.get("bio","")[:100]),
            "location": escape(request.form.get("location","")[:30]),
        }
        session["name"] = profiles[number]["display_name"]
        return redirect("/chat")
    prof = profiles.get(number, {"display_name": session["name"], "status": "", "bio": "", "location": ""})
    return render_template_string(PROFILE_PAGE, profile=prof, name=session["name"], number=number)

@app.route("/send", methods=["POST"])
def send():
    if "name" not in session: return redirect("/")
    text = request.form.get("text","").strip()
    if text:
        prof = profiles.get(session["number"], {})
        messages.append({
            "name": session["name"], 
            "text": escape(text[:500]), 
            "bio": prof.get("status",""),
            "time": datetime.now().strftime("%H:%M")
        })
        if len(messages) > 100: messages.pop(0)
    return redirect("/chat")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
