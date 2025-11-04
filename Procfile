web: python -c "import main; main.main(); import asyncio; asyncio.run(main.setup_bot(main.application))" && gunicorn main:app --workers 1 --bind 0.0.0.0:$PORT
