#!/bin/bash

# Stop and remove containers, networks, volumes, and images created by docker-compose
echo "Stopping and removing Docker containers..."
docker-compose down

# Build or rebuild services in Docker Compose
echo "Building Docker services..."
docker-compose build

# Run Docker Compose in detached mode and output logs to output.log
echo "Starting Docker Compose in detached mode..."
nohup sudo docker-compose up -d > output.log 2>&1 &

# Wait for containers to start up (optional: adjust the sleep duration as needed)
echo "Waiting for Docker containers to start..."
sleep 5  # Adjust if your services take longer to start

# # Initialize the migration folder (if it doesn't exist)
# echo "Initializing the migrations directory..."
# docker exec -it flask_container flask --app src.main db init || echo "Migrations folder already initialized."

# ## Run Flask migrations (generate migration files)
# echo "Generating migration files..."
# docker exec -it flask_container flask --app src.main db migrate -m "Auto migration"

# # Apply the migrations to the database
# echo "Applying migrations to the database..."
# docker exec -it flask_container flask --app src.main db upgrade

# Generate self-signed certificate for HTTPS
py generate_cert.py

# Run the Flask initialization script in the container
echo "Running Flask initialization script in the container..."
docker exec -it flask_container python initialise_db.py

# # Run the insert_data.py script inside the container
# echo "Running data insertion script..."
# docker exec -it flask_container python insert_data.py

# Finish
echo "Initialization and data insertion complete!"