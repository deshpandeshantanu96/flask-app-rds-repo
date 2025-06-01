# Use official Python slim image for smaller size
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire app code
COPY . .

# Expose the port your FastAPI app will run on
EXPOSE 8000

# Default command to run your FastAPI app with Uvicorn
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
