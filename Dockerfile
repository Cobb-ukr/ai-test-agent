# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# By default, Flask runs on 127.0.0.1; we want 0.0.0.0 in Docker
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port Flask uses
EXPOSE 5000

# Use environment variable for Groq API key (do NOT hardcode in image)
#ENV GROQ_API_KEY=""

# Make sure the reports directory exists
RUN mkdir -p reports

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
