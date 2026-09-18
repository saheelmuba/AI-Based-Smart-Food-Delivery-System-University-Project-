FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r requirements_backend.txt

# Create uploads dir
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
