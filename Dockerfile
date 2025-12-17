FROM python:3.11-slim

WORKDIR /app

# Copy backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Railway provides PORT env variable (default 8000)
ENV PORT=8000
EXPOSE 8000

# Use shell form for variable expansion
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
