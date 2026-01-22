FROM python:3.14-slim

# Системні залежності (включно з ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіюємо файли
COPY . /app

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Запуск
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
