@echo off

echo Pulling latest version of ...
docker pull spikesort:latest

echo Running Docker Compose...
docker-compose -f docker-compose.yml up -d