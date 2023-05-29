# Use the official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Uninstall the bson package
RUN pip uninstall -y bson

# Install the pymongo package
RUN pip install --no-cache-dir pymongo

# Copy the consumer.py file to the container
COPY consumer.py .

# Start the consumer script when the container starts
CMD ["python3", "consumer.py"]