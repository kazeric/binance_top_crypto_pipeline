#!/bin/bash

# Register Postgres and Cassandra connectors to Kafka Connect

curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @register-postgres.json

echo "✓ Postgres connector registered"

curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @register_cassandra.json

echo "✓ Cassandra connector registered"
