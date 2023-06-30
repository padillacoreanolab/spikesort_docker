@echo off

echo Logging into Docker...
docker login
if %errorlevel% neq 0 (
    echo Login failed!
    exit /b %errorlevel%
)

@REM docker login  --username padillacoreanolab --password dckr_pat_colSv-sFqYi6S29DFTRN5Mycjz4

echo Pulling latest version of ...
docker pull padillacoreanolab/spikesort:latest

echo Shutting Down Open Docker Container ...
docker stop spikesort_c
docker rm spikesort_c

echo Starting Docker Container ...
docker-compose -f docker-compose.yml up -d 
timeout /T 5
start http://localhost:7000

pause

echo Shutting Down Open Docker Container ...
docker stop spikesort_c
docker rm spikesort_c