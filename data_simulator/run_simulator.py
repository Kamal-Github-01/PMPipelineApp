import argparse
import threading
from sensor_simulator import SensorSimulator

def main():
    parser = argparse.ArgumentParser(description='Run sensor data simulator')
    parser.add_argument('--equipment', type=int, default=3, help='Number of equipment to simulate')
    parser.add_argument('--interval', type=float, default=1.0, help='Data generation interval in seconds')
    parser.add_argument('--kafka', action='store_true', help='Enable Kafka streaming')
    parser.add_argument('--kafka-server', type=str, default='localhost:9092', help='Kafka bootstrap server')
    args = parser.parse_args()
    
    # Kafka configuration if enabled
    kafka_config = None
    if args.kafka:
        kafka_config = {
            'bootstrap.servers': args.kafka_server,
            'client.id': 'sensor-simulator'
        }
    
    # Create and start simulators in separate threads
    simulators = []
    threads = []
    
    try:
        for i in range(1, args.equipment + 1):
            simulator = SensorSimulator(f"EQUIP-{i:03d}", kafka_config)
            simulators.append(simulator)
            
            thread = threading.Thread(
                target=simulator.start_simulation,
                kwargs={
                    'interval': args.interval,
                    'kafka_enabled': args.kafka
                }
            )
            threads.append(thread)
            thread.daemon = True
            thread.start()
            
        print(f"Started {len(simulators)} equipment simulators")
        print("Press Ctrl+C to stop")
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print("\nStopping simulators...")
        for simulator in simulators:
            simulator.stop_simulation()

if __name__ == "__main__":
    main()