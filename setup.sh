#!/bin/bash

echo "========================================"
echo "AI Log Intelligence System Setup"
echo "========================================"

echo "Checking Docker..."

if ! command -v docker &> /dev/null
then
    echo "Docker not installed!"
    exit
fi

echo "Docker OK"

echo "Checking Docker Compose..."

if ! command -v docker compose &> /dev/null
then
    echo "Docker Compose missing!"
    exit
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