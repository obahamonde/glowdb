FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    build-essential \
    curl \
    wget \
    software-properties-common \
    openssl \
    git \
    git-lfs \
    librocksdb-dev \
    chromium \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


ENV PORT=8888
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE $PORT

CMD ["python", "main.py"]