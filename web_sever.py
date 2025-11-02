import os
import logging
from flask import Flask, request, jsonify
from telegram import Update

from main import application 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

PORT = int(os.environ.get('PORT', 5000))
WEBHOOK_PATH = os.environ.get('WEBHOOK_PATH', '/telegram-webhook-secret')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

app = Flask(__name__)

if WEBHOOK_URL:
    try:
        logging.info("Setting up webhook...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=WEBHOOK_URL + WEBHOOK_PATH
        )
        logging.info(f"Webhook set to: {WEBHOOK_URL + WEBHOOK_PATH}")
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            application.process_update(update)
            return jsonify({ 'status': 'ok' }), 200
        except Exception as e:
            logging.error(f"Error processing update: {e}")
            return jsonify({ 'status': 'error', 'message': str(e) }), 500
    return "OK"

@app.route('/', methods=['GET'])
def index():
    return "Your service is live!", 200

if __name__ == '__main__':
    pass
