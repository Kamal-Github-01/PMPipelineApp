import os
import argparse
import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

class MaintenancePredictor:
    """
    Time-series forecasting model for predictive maintenance using Prophet.
    """
    
    def __init__(self, data_dir='../data_ingestion/data', model_dir='./models'):
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.models = {}  # Equipment ID -> Prophet model
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
    
    def load_data(self, equipment_id=None):
        """Load and preprocess data for training"""
        all_data = []
        
        # List all CSV files in the data directory
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        # Filter by equipment ID if specified
        if equipment_id:
            csv_files = [f for f in csv_files if f.startswith(equipment_id)]
        
        # Load and concatenate all files
        for file in csv_files:
            file_path = os.path.join(self.data_dir, file)
            df = pd.read_csv(file_path)
            all_data.append(df)
        
        if not all_data:
            raise ValueError(f"No data found for equipment_id={equipment_id}")
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert timestamp to datetime
        combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
        
        # Sort by timestamp
        combined_df = combined_df.sort_values('timestamp')
        
        # Group by equipment_id
        grouped = combined_df.groupby('equipment_id')
        
        return grouped
    
    def prepare_prophet_data(self, df, target_column):
        """Prepare data for Prophet model"""
        # Prophet requires columns named 'ds' and 'y'
        prophet_df = df[['timestamp', target_column]].copy()
        prophet_df.columns = ['ds', 'y']
        
        return prophet_df
    
    def train_model(self, equipment_id=None, target_column='health_score', 
                    train_ratio=0.8, forecast_periods=24, plot=True):
        """Train Prophet model for the specified equipment and target column"""
        # Load data
        grouped_data = self.load_data(equipment_id)
        
        results = {}
        
        # Train a model for each equipment
        for equip_id, df in grouped_data:
            if equipment_id and equip_id != equipment_id:
                continue
                
            print(f"Training model for equipment {equip_id}, target: {target_column}")
            
            # Prepare data for Prophet
            prophet_df = self.prepare_prophet_data(df, target_column)
            
            # Split into train and test
            train_size = int(len(prophet_df) * train_ratio)
            train_df = prophet_df.iloc[:train_size]
            test_df = prophet_df.iloc[train_size:]
            
            # Create and fit the model
            model = Prophet(
                changepoint_prior_scale=0.05,
                seasonality_mode='multiplicative',
                daily_seasonality=True,
                weekly_seasonality=True
            )
            
            model.fit(train_df)
            
            # Make future dataframe for prediction
            if len(test_df) > 0:
                future = test_df[['ds']].copy()
            else:
                # If no test data, forecast into the future
                future = model.make_future_dataframe(periods=forecast_periods, freq='H')
            
            # Forecast
            forecast = model.predict(future)
            
            # Calculate metrics if test data is available
            metrics = {}
            if len(test_df) > 0:
                y_true = test_df['y'].values
                y_pred = forecast['yhat'].values[:len(y_true)]
                
                mae = mean_absolute_error(y_true, y_pred)
                rmse = np.sqrt(mean_squared_error(y_true, y_pred))
                
                metrics = {
                    'mae': mae,
                    'rmse': rmse
                }
                
                print(f"  MAE: {mae:.4f}, RMSE: {rmse:.4f}")
            
            # Plot if requested
            if plot:
                fig = model.plot(forecast)
                if len(test_df) > 0:
                    plt.scatter(test_df['ds'], test_df['y'], color='red', alpha=0.5, label='Test Data')
                plt.title(f"Forecast for {equip_id} - {target_column}")
                plt.legend()
                
                # Save plot
                plot_dir = os.path.join(self.model_dir, 'plots')
                os.makedirs(plot_dir, exist_ok=True)
                plt.savefig(os.path.join(plot_dir, f"{equip_id}_{target_column}_forecast.png"))
                plt.close()
            
            # Save the model
            model_path = os.path.join(self.model_dir, f"{equip_id}_{target_column}_model.pkl")
            joblib.dump(model, model_path)
            print(f"  Model saved to {model_path}")
            
            # Store model and results
            self.models[equip_id] = model
            results[equip_id] = {
                'model': model,
                'forecast': forecast,
                'metrics': metrics
            }
        
        return results
    
    def export_onnx_model(self, equipment_id, target_column='health_score'):
        """Export the Prophet model to ONNX format for edge deployment"""
        # This is a placeholder as Prophet doesn't directly support ONNX export
        # In a real implementation, you would:
        # 1. Extract the key components of the Prophet model
        # 2. Implement a simplified version using a framework that supports ONNX (like PyTorch or scikit-learn)
        # 3. Export that simplified model to ONNX
        
        print(f"ONNX export for Prophet models is not directly supported.")
        print(f"For edge deployment, consider implementing a simplified version of the model.")

def main():
    parser = argparse.ArgumentParser(description='Train Prophet model for predictive maintenance')
    parser.add_argument('--data-dir', type=str, default='../data_ingestion/data', help='Directory containing sensor data')
    parser.add_argument('--model-dir', type=str, default='./models', help='Directory to save models')
    parser.add_argument('--equipment-id', type=str, help='Specific equipment ID to train for')
    parser.add_argument('--target', type=str, default='health_score', help='Target column to predict')
    parser.add_argument('--train-ratio', type=float, default=0.8, help='Ratio of data to use for training')
    parser.add_argument('--forecast-periods', type=int, default=24, help='Number of periods to forecast')
    parser.add_argument('--no-plot', action='store_true', help='Disable plotting')
    args = parser.parse_args()
    
    predictor = MaintenancePredictor(args.data_dir, args.model_dir)
    
    try:
        results = predictor.train_model(
            equipment_id=args.equipment_id,
            target_column=args.target,
            train_ratio=args.train_ratio,
            forecast_periods=args.forecast_periods,
            plot=not args.no_plot
        )
        
        # Export to ONNX if requested
        if args.equipment_id:
            predictor.export_onnx_model(args.equipment_id, args.target)
            
    except Exception as e:
        print(f"Error training model: {e}")

if __name__ == "__main__":
    main()