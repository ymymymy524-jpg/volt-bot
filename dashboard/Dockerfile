FROM python:3.11-slim

# ═══ تثبيت المكتبات الأساسية ═══
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    ffmpeg \
    git \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ═══ PATH لـ Rust ═══
ENV PATH="/root/.cargo/bin:${PATH}"

# ═══ مكان العمل ═══
WORKDIR /app

# ═══ تثبيت المتطلبات ═══
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ═══ نسخ المشروع ═══
COPY . .

# ═══ تشغيل الداشبورد ═══
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]