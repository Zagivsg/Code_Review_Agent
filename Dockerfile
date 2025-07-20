FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies, including Node.js and npm for JS tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy application code before installing dependencies to leverage caching
COPY . .

# Install JavaScript dependencies defined in package.json
RUN npm install

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# The default command is to run the FastAPI application.
# The rq-worker service in docker-compose.yml will override this command.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]