FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pkg-config \
    gcc \
    g++ \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Step 1: Install PyTorch CPU (smallest version, no CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Step 2: Install av separately (needs FFmpeg dev libs)
RUN pip install --no-cache-dir "av==11.0.0"

# Step 3: Install transformers stack
RUN pip install --no-cache-dir \
    "transformers==4.40.2" \
    "tokenizers==0.19.1" \
    "sentence-transformers==2.7.0"

# Step 4: Install faster-whisper
RUN pip install --no-cache-dir "faster-whisper==1.0.1"

# Step 5: Install remaining dependencies
RUN pip install --no-cache-dir \
    "fastapi==0.111.0" \
    "uvicorn[standard]==0.30.1" \
    "python-multipart==0.0.9" \
    "streamlit==1.35.0" \
    "ffmpeg-python==0.2.0" \
    "keybert==0.8.4" \
    "groq>=0.9.0" \
    "python-dotenv==1.0.1" \
    "requests==2.32.3" \
    "pydantic==2.7.1"

COPY . .

RUN mkdir -p uploads

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]