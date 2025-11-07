# Python image to use.
FROM python:3.11-alpine

# Set the working directory to /app
WORKDIR /app

# Set Env var
ENV PORT=8080

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . /app

# Tell Docker that the container listens on port 8080
EXPOSE 8080

# Run app.py when the container launches
ENTRYPOINT ["python", "app.py"]
