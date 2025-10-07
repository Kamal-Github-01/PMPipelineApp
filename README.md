# Predictive Maintenance Pipeline

A comprehensive application for predictive maintenance that demonstrates:
- Time-series modeling
- Streaming data ingestion
- Edge inference

## Components
- Data Simulator: Generates sensor data mimicking industrial equipment
- Data Ingestion: Kafka-based streaming data pipeline
- Model Training: Time-series forecasting with Prophet
- Edge Inference: Lightweight model deployment for real-time predictions
- Dashboard: Visualization of equipment status and predictions

## Setup and Usage
See the installation and usage instructions in each component's directory.

----

Notes

This completes the implementation of our predictive maintenance pipeline application. The application demonstrates:

1. 1.
   Time-series modeling : Using Prophet for forecasting equipment health and sensor values
2. 2.
   Streaming ingestion : Kafka-based data pipeline for real-time sensor data
3. 3.
   Edge inference : Lightweight model deployment for real-time predictions
To run the application:

1. 1.
   Install the required dependencies: pip install -r requirements.txt
2. 2.
   Start Kafka (using Docker or locally)
3. 3.
   Run the pipeline: bash run_pipeline.sh


The dashboard will be available at http://localhost:8501 , 
and the inference service at http://localhost:5000 .