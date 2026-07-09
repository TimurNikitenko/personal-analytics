FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests apscheduler Pillow

COPY telegram_bot/ /app/

CMD ["python", "bot.py"]
