#!/bin/bash

python -c "import main; main.main()"

python -c "import asyncio, main; asyncio.run(main.setup_bot(main.application))"

echo "Starting Gunicorn..."
gunicorn main:app --workers 1 --bind 0.0.0.0:$PORT
