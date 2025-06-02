FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV EVENTLET_NO_GREENDNS=yes

# Set the working directory
WORKDIR /app/src

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Create directory for certificates
RUN mkdir -p /app/src/certs

# No need to copy code since we're using volume mount
# COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application with gunicorn
# CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:5000", "--log-level", "debug", "run:app"]

CMD ["gunicorn", "--worker-class", "eventlet", "--certfile", "/app/src/certs/server.cert", "--keyfile", "/app/src/certs/server.key", "--bind", "0.0.0.0:5000", "--log-level", "debug", "--capture-output", "--access-logfile", "-", "--error-logfile", "-", "run:app"] 
#CMD ["python", "run.py"]