import os
from flask import Flask, request, redirect, session, render_template_string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "whatsapp-secret-123"
messages = []

LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login - My WhatsApp</title>
<style>
body{font-family:Arial;background:#075E54;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{background:white;padding:25px;border-radius:15px;width:90%;max-width:350px;text-align:center}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box;font-size:16px}
button{width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:8px;font-size:17px;font-weight:bold;cursor:pointer}
h2{color:#075E54}
</style></head>
<body><div class="box"><h2>💬 My WhatsApp</h2><p>Enter your details</p>
<form action="/login" method="post">
<input type="text" name="name" placeholder="Your Name" required>
<input type="text" name="number" placeholder="Your Number" required>
<button type="submit">Login / Start Chatting</button>
</form></div></body></html>
"""

CHAT_PAGE = """
<!DOCTYPE html>
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chat</title>
<style>
body{font-family:Arial;margin:0;background:#ECE5DD}
.header{background:#075E54;color:white;padding:15px;font-size:18px;font-weight:bold;position:fixed;top:0;left:0;right:0}
.chat{padding:70px 10px 80px 10px}
.msg{background:white;padding:10px 12px;border-radius:10px;margin:8px 0;max-width:80%;word-wrap:break-word}
.me{background:#DCF8C6;margin-left:auto}
small{color:#888;font-size:11px}
.sendbox{position:fixed;bottom:0;left:0;right:0;background:white;display:flex;padding:10px;gap:8px}
.sendbox input{flex:1;padding:12px;border:1px solid #ddd;border-radius:20px;font-size:15px}
.sendbox button{background:#25D366;color:white;border:none;border-radius:50%;width:50px;height:50px;font-size:22px}
</style></head>
<body>
<div class="header">💬 My WhatsApp - Hi {{name}}! <a href="/logout" style="color:white;float:right;font-size:14px;">Logout</a></div>
<div class="chat">
{% for m in messages %}
<div class="msg {% if m['name']==name %}me{% endif %}"><b>{{m['name']}}</b><br>{{m['text']}}<br><small>{{m['time']}}</small></div>
{% endfor %}
{% if not messages %}<p style="text-align:center;color:#888;">No messages yet. Say hi! 👋</p>{% endif %}
</div>
<form class="sendbox" action="/send" method="post">
<input type="text" name="text" placeholder="Type a message..." required autocomplete="off">
<button type="submit">➤</button>
</form>
<script>window.scrollTo(0,document.body.scrollHeight); let i=document.querySelector('.sendbox input'); i.value=localStorage.getItem('draft')||''; i.addEventListener('input',()=>{localStorage.setItem('draft', i.value)}); document.querySelector('.sendbox').addEventListener('submit',()=>{localStorage.removeItem('draft')});</script>
</body></html>
"""

@app.route("/")
def home():
    if "name" in session: return redirect("/chat")
    return render_template_string(LOGIN_PAGE)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        number = request.form.get("number")
        if name and number:
            session["name"] = name
            session["number"] = number
            return redirect("/chat")
    return render_template_string(LOGIN_PAGE)

@app.route("/chat")
def chat():
    if "name" not in session: return redirect("/")
    return render_template_string(CHAT_PAGE, messages=messages, name=session["name"])

@app.route("/send", methods=["POST"])
def send():
    if "name" not in session: return redirect("/")
    text = request.form.get("text")
    if text:
        messages.append({"name": session["name"], "text": text, "time": datetime.now().strftime("%H:%M")})
    return redirect("/chat")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
