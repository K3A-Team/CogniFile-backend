#!/bin/bash

if docker-compose -f docker-compose.prod.yaml ps | grep "Up"; then
    echo "Services are already running. Stopping them..."
    docker-compose -f docker-compose.prod.yaml down
else
    echo "No services are running. Continuing..."
fi

echo "Starting services..."
docker-compose -f docker-compose.prod.yaml up -d

if docker-compose -f docker-compose.prod.yaml ps | grep "Up"; then
    echo "Services started successfully."
else
    echo "Failed to start services."
    exit 1
fi
