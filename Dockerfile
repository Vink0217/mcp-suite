# Dockerfile

# Use the Python 3.10 image we know works
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your server code
COPY ./mcp_server /app/mcp_server
# COPY ./client_runner /app/client_runner # Optional: Only if needed inside the container

# Expose the port the server will run on (Railway uses this info)
EXPOSE 8000

# --- Correct CMD using Uvicorn ---
# This tells Uvicorn to run the 'app' object found in mcp_server/main.py
# It uses the PORT environment variable provided by Railway (defaulting to 8000 if not set)
CMD uvicorn mcp_server.main:app --host 0.0.0.0 --port ${PORT:-8000}