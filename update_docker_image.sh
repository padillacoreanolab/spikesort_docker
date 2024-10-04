set -e

# Build the docker Image (--no-cache can be excluded to cache previous builds to speed up the process)
docker build -t spikesort:latest .

# Tag the Docker Iamge as the latest version
docker tag spikesort padillacoreanolab/spikesort:latest

# Push the Docker image to DockerHub
docker push padillacoreanolab/spikesort:latest