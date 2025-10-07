import os
import json
import time
import argparse
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class MaintenanceDashboard:
    """
    Streamlit dashboard for visualizing equipment status and predictions.
    """
    
    def __init__(self, data_dir='../data_ingestion/data', inference_url='http://localhost:5000'):
        self.data_dir = data_dir
        self.inference_url = inference_url
        self.equipment_data = {}
        self.predictions = {}
    
    def load_data(self):
        """Load the latest data for all equipment"""
        # List all CSV files in the data directory
        if not os.path.exists(self.data_dir):
            st.error(f"Data directory {self.data_dir} does not exist")
            return
            
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        # Group files by equipment ID
        equipment_files = {}
        for file in csv_files:
            equipment_id = file.split('_')[0]
            if equipment_id not in equipment_files:
                equipment_files[equipment_id] = []
            equipment_files[equipment_id].append(file)
        
        # Load the latest file for each equipment
        for equipment_id, files in equipment_files.items():
            # Sort by timestamp in filename
            files.sort(reverse=True)
            latest_file = files[0]
            
            # Load the data
            file_path = os.path.join(self.data_dir, latest_file)
            df = pd.read_csv(file_path)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Store the data
            self.equipment_data[equipment_id] = df
    
    def get_predictions(self, equipment_id):
        """Get predictions from the inference service"""
        try:
            # Get the latest sensor data
            latest_data = self.equipment_data[equipment_id].iloc[-1].to_dict()
            
            # Make the request
            response = requests.post(
                f"{self.inference_url}/predict/{equipment_id}",
                json=latest_data,
                params={'periods': 48}  # 48 hours forecast
            )
            
            if response.status_code == 200:
                return response.json()['predictions']
            else:
                st.warning(f"Error getting predictions: {response.json().get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            st.warning(f"Error getting predictions: {e}")
            return None
    
    def run_dashboard(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="Predictive Maintenance Dashboard",
            page_icon="🔧",
            layout="wide"
        )
        
        st.title("Predictive Maintenance Dashboard")
        
        # Load data
        self.load_data()
        
        if not self.equipment_data:
            st.warning("No equipment data found. Please make sure the data directory contains CSV files.")
            return
        
        # Sidebar for equipment selection
        st.sidebar.title("Settings")
        selected_equipment = st.sidebar.selectbox(
            "Select Equipment",
            options=list(self.equipment_data.keys()),
            index=0
        )
        
        # Get predictions for the selected equipment
        with st.sidebar.spinner("Loading predictions..."):
            predictions = self.get_predictions(selected_equipment)
        
        # Display equipment overview
        st.header(f"Equipment Overview: {selected_equipment}")
        
        # Get the data for the selected equipment
        df = self.equipment_data[selected_equipment]
        
        # Display latest readings
        latest = df.iloc[-1]
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Temperature", 
                f"{latest['temperature']:.1f}°C",
                delta=f"{latest['temperature'] - df.iloc[-2]['temperature']:.1f}°C" if len(df) > 1 else None
            )
            
        with col2:
            st.metric(
                "Vibration", 
                f"{latest['vibration']:.3f} g",
                delta=f"{latest['vibration'] - df.iloc[-2]['vibration']:.3f} g" if len(df) > 1 else None
            )
            
        with col3:
            st.metric(
                "Pressure", 
                f"{latest['pressure']:.1f} kPa",
                delta=f"{latest['pressure'] - df.iloc[-2]['pressure']:.1f} kPa" if len(df) > 1 else None
            )
            
        with col4:
            st.metric(
                "Health Score", 
                f"{latest['health_score']:.1f}%",
                delta=f"{latest['health_score'] - df.iloc[-2]['health_score']:.1f}%" if len(df) > 1 else None,
                delta_color="inverse"  # Lower is worse for health score
            )
        
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["Sensor Readings", "Health Prediction", "Maintenance Recommendations"])
        
        with tab1:
            # Create time series plots for sensor readings
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Temperature", "Vibration", "Pressure", "Noise Level"),
                shared_xaxes=True
            )
            
            # Add temperature trace
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['temperature'], name="Temperature"),
                row=1, col=1
            )
            
            # Add vibration trace
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['vibration'], name="Vibration"),
                row=1, col=2
            )
            
            # Add pressure trace
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['pressure'], name="Pressure"),
                row=2, col=1
            )
            
            # Add noise level trace
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['noise_level'], name="Noise Level"),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                title_text="Sensor Readings Over Time",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Display health score history and prediction
            st.subheader("Health Score History and Prediction")
            
            if predictions and 'health_score' in predictions:
                # Create DataFrame for predictions
                pred_df = pd.DataFrame(predictions['health_score'])
                pred_df['timestamp'] = pd.to_datetime(pred_df['timestamp'])
                
                # Create figure
                fig = go.Figure()
                
                # Add historical data
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], 
                        y=df['health_score'],
                        name="Historical",
                        line=dict(color='blue')
                    )
                )
                
                # Add prediction
                fig.add_trace(
                    go.Scatter(
                        x=pred_df['timestamp'],
                        y=pred_df['prediction'],
                        name="Prediction",
                        line=dict(color='red', dash='dash')
                    )
                )
                
                # Add confidence interval
                fig.add_trace(
                    go.Scatter(
                        x=pd.concat([pred_df['timestamp'], pred_df['timestamp'].iloc[::-1]]),
                        y=pd.concat([pred_df['upper_bound'], pred_df['lower_bound'].iloc[::-1]]),
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        name="Confidence Interval"
                    )
                )
                
                # Add threshold line
                fig.add_shape(
                    type="line",
                    x0=df['timestamp'].min(),
                    y0=20,
                    x1=pred_df['timestamp'].max(),
                    y1=20,
                    line=dict(
                        color="Red",
                        width=2,
                        dash="dashdot",
                    )
                )
                
                fig.add_annotation(
                    x=df['timestamp'].min(),
                    y=20,
                    text="Critical Threshold",
                    showarrow=False,
                    yshift=10
                )
                
                # Update layout
                fig.update_layout(
                    title="Health Score Forecast",
                    xaxis_title="Time",
                    yaxis_title="Health Score (%)",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate time to maintenance
                health_forecast = pred_df['prediction'].values
                threshold = 20  # Critical health threshold
                
                time_to_critical = None
                for i, health in enumerate(health_forecast):
                    if health < threshold:
                        time_to_critical = i
                        break
                
                if time_to_critical is not None:
                    st.warning(f"⚠️ Equipment is predicted to reach critical health in {time_to_critical} hours!")
                else:
                    # Calculate minimum health
                    min_health = min(health_forecast)
                    if min_health < 50:
                        st.info(f"ℹ️ Equipment health is predicted to drop to {min_health:.1f}% in the next 48 hours.")
                    else:
                        st.success("✅ Equipment is predicted to maintain good health for the next 48 hours.")
            else:
                st.info("No health score predictions available. Make sure the inference service is running.")
        
        with tab3:
            # Display maintenance recommendations
            st.subheader("Maintenance Recommendations")
            
            # Calculate current health status
            current_health = latest['health_score']
            
            if current_health < 20:
                st.error("🚨 **CRITICAL**: Immediate maintenance required! Equipment is at high risk of failure.")
                st.markdown("""
                **Recommended Actions:**
                - Shut down equipment immediately
                - Schedule emergency maintenance
                - Inspect and replace worn components
                - Perform full system diagnostics
                """)
            elif current_health < 50:
                st.warning("⚠️ **WARNING**: Equipment health is degrading. Plan maintenance soon.")
                st.markdown("""
                **Recommended Actions:**
                - Schedule maintenance within the next 48 hours
                - Monitor temperature and vibration closely
                - Prepare replacement parts
                - Reduce operational load if possible
                """)
            elif current_health < 80:
                st.info("ℹ️ **ATTENTION**: Equipment showing early signs of wear.")
                st.markdown("""
                **Recommended Actions:**
                - Schedule routine maintenance within the next week
                - Inspect for unusual wear patterns
                - Check lubrication and cooling systems
                - Review recent operational patterns
                """)
            else:
                st.success("✅ **GOOD**: Equipment is in good health.")
                st.markdown("""
                **Recommended Actions:**
                - Continue regular maintenance schedule
                - No immediate action required
                """)
            
            # Display anomaly detection results
            st.subheader("Anomaly Detection")
            
            # Simple anomaly detection based on recent readings
            recent_df = df.iloc[-20:]
            
            # Calculate z-scores for each sensor
            z_temp = (recent_df['temperature'] - recent_df['temperature'].mean()) / recent_df['temperature'].std()
            z_vibration = (recent_df['vibration'] - recent_df['vibration'].mean()) / recent_df['vibration'].std()
            z_pressure = (recent_df['pressure'] - recent_df['pressure'].mean()) / recent_df['pressure'].std()
            z_noise = (recent_df['noise_level'] - recent_df['noise_level'].mean()) / recent_df['noise_level'].std()
            
            # Check for anomalies (z-score > 2)
            anomalies = []
            if abs(z_temp.iloc[-1]) > 2:
                anomalies.append(f"Temperature: {latest['temperature']:.1f}°C (z-score: {z_temp.iloc[-1]:.2f})")
            if abs(z_vibration.iloc[-1]) > 2:
                anomalies.append(f"Vibration: {latest['vibration']:.3f} g (z-score: {z_vibration.iloc[-1]:.2f})")
            if abs(z_pressure.iloc[-1]) > 2:
                anomalies.append(f"Pressure: {latest['pressure']:.1f} kPa (z-score: {z_pressure.iloc[-1]:.2f})")
            if abs(z_noise.iloc[-1]) > 2:
                anomalies.append(f"Noise Level: {latest['noise_level']:.1f} dB (z-score: {z_noise.iloc[-1]:.2f})")
            
            if anomalies:
                st.warning("Anomalies detected in recent readings:")
                for anomaly in anomalies:
                    st.markdown(f"- {anomaly}")
            else:
                st.success("No anomalies detected in recent readings.")
        
        # Add refresh button
        if st.button("Refresh Data"):
            st.experimental_rerun()
        
        # Add timestamp
        st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    parser = argparse.ArgumentParser(description='Run predictive maintenance dashboard')
    parser.add_argument('--data-dir', type=str, default='../data_ingestion/data', help='Directory containing sensor data')
    parser.add_argument('--inference-url', type=str, default='http://localhost:5000', help='URL of the inference service')
    args = parser.parse_args()
    
    dashboard = MaintenanceDashboard(args.data_dir, args.inference_url)
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()