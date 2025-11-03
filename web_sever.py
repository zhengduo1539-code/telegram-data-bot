import os
import logging
from flask import Flask
from telegram import Update
import threading
import sys

app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@app.route("/")
def index():
    return "OK - Service is running", 200

WEBHOOK_PATH = os.environ.get('WEBHOOK_PATH', '/telegram-webhook-secret')

try:
    from main import main
    
    def run_main():
        main()

    bot_thread = threading.Thread(target=run_main)
    bot_thread.daemon = True
    bot_thread.start()

except ImportError:
    logging.error("Failed to import main function from main.py.")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
