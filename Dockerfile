FROM python:3.11-slim

WORKDIR /app

# Copy backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway provides PORT env variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
