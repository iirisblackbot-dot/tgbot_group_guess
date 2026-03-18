FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tgbot/ .

ENV BOT_TOKEN=""
ENV OPENAI_API_KEY=""

CMD ["python3", "bot.py"]
