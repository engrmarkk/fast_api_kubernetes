#! /bin/bash
docker image prune -a
docker-compose up --build -d

# to update the database, uncomment the line below
#docker exec -it fast_api alembic upgrade head
docker ps
docker image prune -a
