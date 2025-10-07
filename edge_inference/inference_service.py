import os
import json
import time
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
from flask import Flask, request, jsonify

app = Flask(__name__)

class MaintenancePredictor:
    """
    Lightweight predictor for edge deployment.
    Loads trained Prophet models and provides inference capabilities.
    """
    
    def __init__(self, model_dir='../model_training/models'):
        self.model_dir = model_dir
        self.models = {}  # Equipment ID -> {target -> model}
        self.load_models()
    
    def load_models(self):
        """Load all available models from the model directory"""
        # List all model files
        model_files = [f for f in os.listdir(self.model_dir) if f.endswith('_model.pkl')]
        
        for model_file in model_files:
            # Parse equipment ID and target from filename
            parts = model_file.split('_')
            equipment_id = parts[0]
            target = '_'.join(parts[1:-1])  # Handle targets with underscores
            
            # Load the model
            model_path = os.path.join(self.model_dir, model_file)
            try:
                model = joblib.load(model_path)
                
                # Initialize equipment entry if needed
                if equipment_id not in self.models:
                    self.models[equipment_id] = {}
                
                # Store the model
                self.models[equipment_id][target] = model
                print(f"Loaded model for {equipment_id}, target: {target}")
                
            except Exception as e:
                print(f"Error loading model {model_file}: {e}")
    
    def predict(self, equipment_id, sensor_data, periods=24):
        """
        Make predictions for the specified equipment using the latest sensor data.
        Returns predictions for all available targets.
        """
        if equipment_id not in self.models:
            raise ValueError(f"No models available for equipment {equipment_id}")
        
        results = {}
        
        # Convert sensor data to DataFrame
        if isinstance(sensor_data, dict):
            sensor_data = [sensor_data]
        
        df = pd.DataFrame(sensor_data)
        
        # Convert timestamp to datetime if present
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            df['timestamp'] = datetime.now()
        
        # Make predictions for each target
        for target, model in self.models[equipment_id].items():
            # Create future dataframe starting from the latest timestamp
            latest_timestamp = df['timestamp'].max()
            future_dates = [latest_timestamp + timedelta(hours=i) for i in range(periods)]
            future = pd.DataFrame({'ds': future_dates})
            
            # Make prediction
            forecast = model.predict(future)
            
            # Extract relevant columns
            prediction = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
            prediction.columns = ['timestamp', 'prediction', 'lower_bound', 'upper_bound']
            
            # Convert timestamps to string for JSON serialization
            prediction['timestamp'] = prediction['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Add to results
            results[target] = prediction.to_dict(orient='records')
        
        return results

# Initialize predictor
predictor = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/models', methods=['GET'])
def list_models():
    """List available models"""
    if not predictor:
        return jsonify({'error': 'Predictor not initialized'}), 500
    
    models_info = {}
    for equipment_id, targets in predictor.models.items():
        models_info[equipment_id] = list(targets.keys())
    
    return jsonify({
        'models': models_info,
        'count': sum(len(targets) for targets in predictor.models.values())
    })

@app.route('/predict/<equipment_id>', methods=['POST'])
def predict(equipment_id):
    """Make predictions for the specified equipment"""
    if not predictor:
        return jsonify({'error': 'Predictor not initialized'}), 500
    
    # Get request data
    data = request.json
    
    if not data:
        return jsonify({'error': 'No sensor data provided'}), 400
    
    # Get prediction periods
    periods = int(request.args.get('periods', 24))
    
    try:
        # Make predictions
        results = predictor.predict(equipment_id, data, periods)
        
        return jsonify({
            'equipment_id': equipment_id,
            'predictions': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500

def main():
    parser = argparse.ArgumentParser(description='Run edge inference service for predictive maintenance')
    parser.add_argument('--model-dir', type=str, default='../model_training/models', help='Directory containing trained models')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    global predictor
    predictor = MaintenancePredictor(args.model_dir)
    
    # Start the Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()