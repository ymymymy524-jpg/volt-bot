FROM python:3.11-slim

# تثبيت Rust + FFmpeg + git
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    ffmpeg \
    git \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]