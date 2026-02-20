# Use the official Python image as a base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements if exists, else skip
COPY backend/requirements.txt ./backend/requirements.txt
RUN if [ -f backend/requirements.txt ]; then pip install --upgrade pip && pip install -r backend/requirements.txt; fi

# Copy backend and frontend code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port (adjust if needed)
EXPOSE 5000

# Set default command to run the backend (adjust as needed)
CMD ["python", "backend/run.py"]
