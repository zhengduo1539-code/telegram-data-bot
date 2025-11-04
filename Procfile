web: python -c "import asyncio, main; asyncio.run(main.setup_bot(main.application))" && gunicorn main:app --workers 1 --bind 0.0.0.0:$PORT
