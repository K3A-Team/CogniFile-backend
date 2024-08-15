#!/bin/bash

if docker-compose ps | grep "Up"; then
    echo "Services are already running. Stopping them..."
    docker-compose down
else
    echo "No services are running. Continuing..."
fi

echo "Starting services..."
docker-compose up --build -d

if docker-compose ps | grep "Up"; then
    echo "Services started successfully."
else
    echo "Failed to start services."
    exit 1
fi
