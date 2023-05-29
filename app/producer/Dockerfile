# Use the official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the producer.py file to the container
COPY producer.py .

# Expose the port on which the FastAPI application will run
EXPOSE 8088

# Start the FastAPI application when the container starts
CMD ["python3", "producer.py"]