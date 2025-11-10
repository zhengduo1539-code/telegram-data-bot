from flask import Flask
from threading import Thread
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask('')
@app.route('/')
def home():
    return "Telegram Bot is Running and Alive!"
def run():
    print("✨ Keep Alive Web Server Starting on 0.0.0.0:8080...")
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
    print("✅ Keep Alive System (Web Server) initialized in background thread.")
if __name__ == '__main__':
    run()
