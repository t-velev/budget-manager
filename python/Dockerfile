# Define "Base Image"
FROM python:3.12-alpine

# Define the working directory of the app
WORKDIR /app

COPY python/requirements.txt .

# Install needed libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts to working dir
COPY src/ ./src/