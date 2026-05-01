FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Kolkata

WORKDIR /app

# System deps + tzdata for IST scheduling
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata wget gnupg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Playwright browser + system libs
RUN playwright install --with-deps chromium

# App code
COPY . .

RUN mkdir -p data logs/screenshots

EXPOSE 5050

# Run as non-root for safety (matches container user namespace)
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

CMD ["python", "-m", "scheduler.main_scheduler"]
