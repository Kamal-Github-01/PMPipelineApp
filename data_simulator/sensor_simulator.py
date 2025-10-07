import time
import json
import random
import numpy as np
from datetime import datetime, timedelta
from confluent_kafka import Producer

class SensorSimulator:
    """
    Simulates sensor data from industrial equipment for predictive maintenance.
    Generates realistic time-series data with patterns, trends, and anomalies.
    """
    
    def __init__(self, equipment_id, kafka_config=None):
        self.equipment_id = equipment_id
        self.running = False
        self.normal_temp_range = (60, 80)  # Normal operating temperature
        self.normal_vibration_range = (0.1, 0.5)  # Normal vibration levels
        self.normal_pressure_range = (95, 105)  # Normal pressure levels
        self.normal_noise_range = (60, 75)  # Normal noise levels in dB
        
        # Degradation parameters
        self.health_score = 100.0  # Equipment starts at 100% health
        self.degradation_rate = random.uniform(0.01, 0.05)  # Random degradation rate
        
        # Kafka producer setup
        self.kafka_config = kafka_config or {
            'bootstrap.servers': 'localhost:9092',
            'client.id': f'sensor-simulator-{equipment_id}'
        }
        self.producer = Producer(self.kafka_config) if kafka_config else None
        self.topic = 'equipment-sensors'
        
    def generate_sensor_reading(self):
        """Generate a single sensor reading with realistic patterns"""
        # Time component
        timestamp = datetime.now().isoformat()
        
        # Calculate health-based degradation
        self.health_score -= self.degradation_rate
        self.health_score = max(0, self.health_score)
        
        # Add daily and weekly patterns
        current_time = datetime.now()
        hour_of_day = current_time.hour
        day_of_week = current_time.weekday()
        
        # Daily pattern: equipment runs hotter during peak hours
        time_factor = 1.0 + 0.2 * np.sin(np.pi * hour_of_day / 12)
        
        # Weekly pattern: more wear on weekdays
        day_factor = 1.0 + 0.1 * (1 if day_of_week < 5 else -1)
        
        # Health degradation effect
        health_factor = (100 - self.health_score) / 100
        
        # Generate sensor values with patterns and some randomness
        temperature = self._generate_value(
            self.normal_temp_range, 
            base_multiplier=time_factor,
            health_effect=health_factor * 30,  # Temperature rises as health decreases
            noise_level=2.0
        )
        
        vibration = self._generate_value(
            self.normal_vibration_range,
            base_multiplier=day_factor,
            health_effect=health_factor * 1.5,  # Vibration increases as health decreases
            noise_level=0.05
        )
        
        pressure = self._generate_value(
            self.normal_pressure_range,
            base_multiplier=1.0,
            health_effect=health_factor * -15,  # Pressure drops as health decreases
            noise_level=3.0
        )
        
        noise_level = self._generate_value(
            self.normal_noise_range,
            base_multiplier=day_factor,
            health_effect=health_factor * 25,  # Noise increases as health decreases
            noise_level=2.0
        )
        
        # Occasional anomalies
        if random.random() < 0.01 + (health_factor * 0.1):  # More anomalies as health decreases
            # Choose one sensor to show an anomaly
            anomaly_sensor = random.choice(['temperature', 'vibration', 'pressure', 'noise_level'])
            if anomaly_sensor == 'temperature':
                temperature += random.uniform(10, 30)
            elif anomaly_sensor == 'vibration':
                vibration += random.uniform(0.5, 2.0)
            elif anomaly_sensor == 'pressure':
                pressure -= random.uniform(10, 30)
            elif anomaly_sensor == 'noise_level':
                noise_level += random.uniform(10, 20)
        
        # Create the sensor reading
        reading = {
            'equipment_id': self.equipment_id,
            'timestamp': timestamp,
            'temperature': round(temperature, 2),
            'vibration': round(vibration, 3),
            'pressure': round(pressure, 2),
            'noise_level': round(noise_level, 2),
            'health_score': round(self.health_score, 2)
        }
        
        return reading
    
    def _generate_value(self, normal_range, base_multiplier=1.0, health_effect=0, noise_level=1.0):
        """Helper to generate a sensor value with the specified parameters"""
        base_value = random.uniform(*normal_range)
        value = base_value * base_multiplier + health_effect + random.uniform(-noise_level, noise_level)
        return value
    
    def send_to_kafka(self, reading):
        """Send the sensor reading to Kafka"""
        if self.producer:
            try:
                self.producer.produce(
                    self.topic,
                    key=str(self.equipment_id),
                    value=json.dumps(reading)
                )
                self.producer.flush(timeout=1)
                return True
            except Exception as e:
                print(f"Error sending to Kafka: {e}")
                return False
        return False
    
    def start_simulation(self, interval=1.0, duration=None, kafka_enabled=True):
        """Start the simulation, generating data at the specified interval"""
        self.running = True
        start_time = time.time()
        
        print(f"Starting simulation for equipment {self.equipment_id}")
        
        try:
            while self.running:
                if duration and (time.time() - start_time) > duration:
                    break
                    
                reading = self.generate_sensor_reading()
                print(f"Generated: {reading}")
                
                if kafka_enabled and self.producer:
                    self.send_to_kafka(reading)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Simulation stopped by user")
        finally:
            self.running = False
            if self.producer:
                self.producer.flush()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False