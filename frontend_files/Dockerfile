# Lightweight Python base image
FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Install the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the Streamlit app
COPY . .

# Address of the backend container on the shared Docker network (can be overridden with -e BACKEND_URL=...)
ENV BACKEND_URL=http://superkart-backend:7860

# Streamlit listens on port 8501
EXPOSE 8501

# XSRF protection is disabled so that file uploads work through the Codespaces port-forwarding proxy
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false", "--server.enableCORS=false"]
