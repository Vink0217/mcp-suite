# Dockerfile

# Use the Python 3.10 image we know works
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install packages using uv (faster)
# RUN pip install --no-cache-dir uv # Uncomment if uv isn't pre-installed in the base image
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your server code
COPY ./mcp_server /app/mcp_server
COPY ./client_runner /app/client_runner 

# Expose the port the server will run on
EXPOSE 8000

# --- Correct CMD using Uvicorn ---
# This tells Uvicorn to run the 'app' object found in the mcp_server/main.py file
CMD ["uvicorn", "mcp_server.main:app", "--host", "0.0.0.0", "--port", "8000"]