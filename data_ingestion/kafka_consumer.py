import json
import argparse
import pandas as pd
from confluent_kafka import Consumer, KafkaError
from datetime import datetime
import os

class SensorDataConsumer:
    """
    Consumes sensor data from Kafka and stores it for processing.
    """
    
    def __init__(self, kafka_config, topic, output_dir='./data'):
        self.kafka_config = kafka_config
        self.topic = topic
        self.output_dir = output_dir
        self.consumer = Consumer(kafka_config)
        self.consumer.subscribe([topic])
        self.running = False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Data storage
        self.data_buffer = {}  # Equipment ID -> list of readings
        self.buffer_size = 100  # Number of readings before writing to disk
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        self.running = True
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        print(f"Reached end of partition {msg.partition()}")
                    else:
                        print(f"Error: {msg.error()}")
                else:
                    # Process the message
                    self._process_message(msg)
                    
        except KeyboardInterrupt:
            print("Consumption stopped by user")
        finally:
            self._save_all_buffers()
            self.consumer.close()
            self.running = False
    
    def _process_message(self, msg):
        """Process a single Kafka message"""
        try:
            # Parse the message value
            value_str = msg.value().decode('utf-8')
            data = json.loads(value_str)
            
            # Extract equipment ID
            equipment_id = data.get('equipment_id')
            
            if equipment_id:
                # Add to buffer
                if equipment_id not in self.data_buffer:
                    self.data_buffer[equipment_id] = []
                
                self.data_buffer[equipment_id].append(data)
                
                # If buffer is full, save to disk
                if len(self.data_buffer[equipment_id]) >= self.buffer_size:
                    self._save_buffer(equipment_id)
                    
                print(f"Processed message for {equipment_id}: {data}")
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _save_buffer(self, equipment_id):
        """Save the buffer for a specific equipment to disk"""
        if equipment_id in self.data_buffer and self.data_buffer[equipment_id]:
            # Convert to DataFrame
            df = pd.DataFrame(self.data_buffer[equipment_id])
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{equipment_id}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            print(f"Saved {len(self.data_buffer[equipment_id])} records to {filepath}")
            
            # Clear buffer
            self.data_buffer[equipment_id] = []
    
    def _save_all_buffers(self):
        """Save all buffers to disk"""
        for equipment_id in list(self.data_buffer.keys()):
            self._save_buffer(equipment_id)
    
    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Consume sensor data from Kafka')
    parser.add_argument('--kafka-server', type=str, default='localhost:9092', help='Kafka bootstrap server')
    parser.add_argument('--topic', type=str, default='equipment-sensors', help='Kafka topic to consume from')
    parser.add_argument('--group-id', type=str, default='sensor-consumer-group', help='Consumer group ID')
    parser.add_argument('--output-dir', type=str, default='./data', help='Output directory for data files')
    args = parser.parse_args()
    
    # Kafka configuration
    kafka_config = {
        'bootstrap.servers': args.kafka_server,
        'group.id': args.group_id,
        'auto.offset.reset': 'earliest'
    }
    
    # Create and start consumer
    consumer = SensorDataConsumer(kafka_config, args.topic, args.output_dir)
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("\nStopping consumer...")
    finally:
        consumer.stop_consuming()

if __name__ == "__main__":
    main()