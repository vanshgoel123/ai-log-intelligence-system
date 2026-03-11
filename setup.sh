#!/bin/bash
set -e

echo "AI Log Intelligence System Setup"

echo "Checking Docker..."
if ! command -v docker > /dev/null 2>&1
then
    echo "Docker not installed!"
    exit 1
fi
echo "Docker OK"

echo "Checking Docker Compose..."
if ! docker compose version > /dev/null 2>&1
then
    echo "Docker Compose missing!"
    exit 1
fi
echo "Docker Compose OK"

echo ""
echo "Creating logs directory..."
mkdir -p logs

echo ""
echo "Starting monitoring system..."
docker compose down
docker compose up -d --build

echo ""
echo "System started!"

echo ""
echo "Services:"
echo "Elasticsearch -> http://localhost:9200"
echo "Kibana -> http://localhost:5601"

echo ""
echo "Checking containers..."
docker ps

echo ""
echo "Setup complete!"