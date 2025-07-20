FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies that might be needed by Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# The default command is to run the FastAPI application.
# The rq-worker service in docker-compose.yml will override this command.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
