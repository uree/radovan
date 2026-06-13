# TO DO: upgrade to latest
FROM python:3.12.3-slim  

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install the dependencies
RUN pip install uv && \
    uv pip install --system -r requirements.txt

COPY . .
# Run the command to start gunicorn
# CMD ["gunicorn", "--error-logfile", "app/logs/output/gunicorn-error.log", "--access-logfile", "app/logs/output/gunicorn-access.log", "app:create_app()", "-b", "0.0.0.0:9003", "-t 180"]

CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:9003", "-t 180"]
