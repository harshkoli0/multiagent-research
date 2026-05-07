# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir \
    langchain \
    langchain-groq \
    langgraph \
    python-dotenv \
    requests \
    tavily-python

# Expose port for API (if needed)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "app.py"]
