# Dockerfile

# Use an official, slim Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements file first
COPY requirements.txt /app/

# Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your server code
COPY ./mcp_server /app/mcp_server
COPY ./client_runner /app/client_runner

# This is the command that starts your server
CMD ["python", "-m", "mcp_server.main"]