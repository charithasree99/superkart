# Lightweight Python base image
FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Install the Python dependencies first (cached layer when only the code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the Flask app and the serialized model
COPY . .

# The API listens on port 7860
EXPOSE 7860

# Serve the Flask app "superkart_api" defined in app.py with gunicorn (4 workers)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:superkart_api"]
