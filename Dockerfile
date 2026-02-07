# Define "Base Image"
FROM python:3.12-alpine

# Define the working directory of the app
WORKDIR /app

# Install needed libraries
RUN pip install --no-cache-dir \
    requests

# Copy scripts to working dir
COPY /src/notion_extract.py .

# Execute
CMD ["python", "notion_extract.py"]