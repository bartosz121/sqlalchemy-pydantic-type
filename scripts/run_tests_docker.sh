#!/bin/bash

# This script automates running integration tests locally
set -e

cleanup() {
    echo "---"
    echo "Cleaning up containers..."
    docker kill $POSTGRES_CONTAINER_ID $MYSQL_CONTAINER_ID &> /dev/null || true
    echo "Cleanup complete."
}

trap cleanup EXIT

echo "Starting PostgreSQL (postgres:15) container..."
POSTGRES_CONTAINER_ID=$(docker run --rm -d \
    -e POSTGRES_USER=test_user \
    -e POSTGRES_PASSWORD=test_password \
    -e POSTGRES_DB=test_db \
    -p 5432:5432 \
    postgres:15)

echo "Starting MySQL (mysql:8.0) container..."
MYSQL_CONTAINER_ID=$(docker run --rm -d \
    -e MYSQL_ROOT_PASSWORD=root_password \
    -e MYSQL_DATABASE=test_db \
    -e MYSQL_USER=test_user \
    -e MYSQL_PASSWORD=test_password \
    -p 3306:3306 \
    mysql:8.0)

echo "Waiting for databases to initialize..."

echo -n "Waiting for PostgreSQL..."
until docker exec "$POSTGRES_CONTAINER_ID" pg_isready -U test_user -d test_db -q; do
    echo -n "."
    sleep 2
done
echo " PostgreSQL is ready."

echo -n "Waiting for MySQL..."
until docker exec "$MYSQL_CONTAINER_ID" mysqladmin ping -h localhost -u root -proot_password --silent; do
    echo -n "."
    sleep 2
done
sleep 5 # Mysql sometimes needs a bit more time to be fully ready
echo " MySQL is ready."
echo "---"


echo "Databases are running. Executing tests..."
hatch test --all
