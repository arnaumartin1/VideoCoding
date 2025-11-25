FROM python:3.11

WORKDIR /app

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements_minimal.txt .

RUN pip install --no-cache-dir -r requirements_minimal.txt

COPY . .

CMD ["uvicorn", "first_practice:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
