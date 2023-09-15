# Use an official Python runtime as the base image
FROM python:3.8

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy requirements.txt to the container
COPY requirements.txt ./

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code to the container
COPY . .

# Start the backend app
CMD ["python", "server/app.py"]
