@echo off

echo Logging Into Docker...
docker login
if %errorlevel% neq 0 (
    echo Login failed!
    exit /b %errorlevel%
)

echo Pulling Latest Version of Image: spikesort...
docker pull padillacoreanolab/spikesort:latest

echo Shutting Down Open Docker Containers With The Same Name ...
docker stop spikesort_c
docker rm spikesort_c

set /p path_variable="ENTER THE FULL PATH TO THE PARENT FOLDER OF THE SPIKESORT DATA FOLDER: "

echo Running Docker Container:  spikesort_c...
@REM docker-compose -f docker-compose.yml up -d
docker run --name spikesort_c --log-driver=json-file -v %path_variable%:/spikesort -p 7000:7000 padillacoreanolab/spikesort:latest

pause

echo Shutting Down Open Docker Container: spikesort_c ...
docker stop spikesort_c
docker rm spikesort_c