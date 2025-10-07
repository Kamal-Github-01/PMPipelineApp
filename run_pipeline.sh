#!/bin/bash

# Predictive Maintenance Pipeline Runner
# This script sets up and runs all components of the predictive maintenance pipeline

# Create necessary directories
mkdir -p data_ingestion/data
mkdir -p model_training/models/plots

# Check if Kafka is running
if ! nc -z localhost 9092 >/dev/null 2>&1; then
    echo "Kafka is not running. Please start Kafka before running this script."
    echo "You can use Docker to run Kafka:"
    echo "docker run -p 2181:2181 -p 9092:9092 --env ADVERTISED_HOST=localhost --env ADVERTISED_PORT=9092 spotify/kafka"
    exit 1
fi

# Function to run a component in the background
run_component() {
    echo "Starting $1..."
    cd "$2" && python "$3" "$4" &
    sleep 2
    cd ..
}

# Start data simulator
run_component "Data Simulator" "data_simulator" "run_simulator.py" "--equipment 3 --interval 1.0 --kafka"

# Start data consumer
run_component "Data Consumer" "data_ingestion" "kafka_consumer.py" "--output-dir ./data"

# Wait for some data to be collected
echo "Collecting initial data for 30 seconds..."
sleep 30

# Train models
echo "Training predictive models..."
cd model_training
python train_prophet_model.py --data-dir ../data_ingestion/data
cd ..

# Start inference service
run_component "Inference Service" "edge_inference" "inference_service.py" "--model-dir ../model_training/models"

# Start dashboard
run_component "Dashboard" "dashboard" "app.py" "--data-dir ../data_ingestion/data"

echo "All components started. Dashboard available at http://localhost:8501"
echo "Press Ctrl+C to stop all components"

# Wait for Ctrl+C
trap "kill 0" EXIT
wait