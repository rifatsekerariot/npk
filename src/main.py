#!/usr/bin/env python3
"""
NPK Sensor to ThingsBoard - Main Application
Reads NPK sensor data via RS485 and publishes to ThingsBoard via MQTT
"""

import yaml
import time
import signal
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from npk_reader import NPKSensorReader
from mqtt_publisher import ThingsBoardMQTTPublisher


class NPKMonitor:
    """Main NPK monitoring application"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize NPK Monitor
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        
        # Initialize components
        self.sensor: Optional[NPKSensorReader] = None
        self.publisher: Optional[ThingsBoardMQTTPublisher] = None
        
        # Statistics
        self.stats = {
            'start_time': None,
            'readings_count': 0,
            'publish_success': 0,
            'publish_failed': 0,
            'sensor_errors': 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def _initialize_sensor(self) -> bool:
        """Initialize NPK sensor"""
        try:
            sensor_config = self.config['sensor']
            
            self.sensor = NPKSensorReader(
                port=sensor_config.get('port', '/dev/ttyS0'),
                slave_id=sensor_config.get('slave_id', 1),
                baudrate=sensor_config.get('baudrate', 4800),
                timeout=sensor_config.get('timeout', 1.0),
                registers=sensor_config.get('registers')
            )
            
            # Test connection
            logger.info("Testing sensor connection...")
            if self.sensor.test_connection():
                logger.info("Sensor initialized successfully")
                return True
            else:
                logger.error("Sensor connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize sensor: {e}")
            return False
    
    def _initialize_publisher(self) -> bool:
        """Initialize MQTT publisher"""
        try:
            mqtt_config = self.config['mqtt']
            tb_config = self.config['thingsboard']
            
            self.publisher = ThingsBoardMQTTPublisher(
                host=tb_config['host'],
                port=mqtt_config.get('port', 1883),
                access_token=tb_config['access_token'],
                keepalive=mqtt_config.get('keepalive', 60),
                qos=mqtt_config.get('qos', 1)
            )
            
            # Connect to broker
            logger.info("Connecting to ThingsBoard MQTT broker...")
            if self.publisher.connect():
                logger.info("Publisher initialized successfully")
                
                # Publish initial attributes
                self._publish_device_attributes()
                return True
            else:
                logger.error("Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize publisher: {e}")
            return False
    
    def _publish_device_attributes(self):
        """Publish device attributes to ThingsBoard"""
        try:
            attributes = {
                'device_type': 'NPK Soil Sensor',
                'firmware_version': '1.0.0',
                'model': self.config['sensor'].get('model', 'Generic NPK'),
                'location': self.config.get('device', {}).get('location', 'Unknown'),
                'reading_interval': self.config.get('application', {}).get('reading_interval', 60)
            }
            
            self.publisher.publish_attributes(attributes)
            logger.info("Published device attributes")
        except Exception as e:
            logger.error(f"Error publishing device attributes: {e}")
    
    def _read_sensor_data(self) -> Optional[Dict]:
        """Read all available sensor data"""
        try:
            data = self.sensor.read_all_sensors()
            
            # Validate data - ensure at least NPK values are present
            if data.get('nitrogen') is None and data.get('phosphorus') is None and data.get('potassium') is None:
                logger.warning("No valid NPK data read from sensor")
                self.stats['sensor_errors'] += 1
                return None
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            self.stats['readings_count'] += 1
            return data
            
        except Exception as e:
            logger.error(f"Error reading sensor data: {e}")
            self.stats['sensor_errors'] += 1
            return None
    
    def _publish_data(self, data: Dict) -> bool:
        """Publish sensor data to ThingsBoard"""
        try:
            # Add timestamp
            use_timestamp = self.config.get('mqtt', {}).get('include_timestamp', False)
            timestamp = int(datetime.now().timestamp() * 1000) if use_timestamp else None
            
            if self.publisher.publish_telemetry(data, timestamp):
                self.stats['publish_success'] += 1
                return True
            else:
                self.stats['publish_failed'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error publishing data: {e}")
            self.stats['publish_failed'] += 1
            return False
    
    def _ensure_mqtt_connection(self):
        """Ensure MQTT connection is active, reconnect if needed"""
        if not self.publisher.is_connected():
            logger.warning("MQTT connection lost, attempting to reconnect...")
            try:
                self.publisher.connect()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
    
    def start(self):
        """Start the monitoring application"""
        logger.info("Starting NPK Monitor application...")
        
        # Initialize components
        if not self._initialize_sensor():
            logger.error("Failed to initialize sensor, aborting")
            return False
        
        if not self._initialize_publisher():
            logger.error("Failed to initialize publisher, aborting")
            return False
        
        # Get application config
        app_config = self.config.get('application', {})
        reading_interval = app_config.get('reading_interval', 60)
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info(f"NPK Monitor started (reading interval: {reading_interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Ensure MQTT connection
                self._ensure_mqtt_connection()
                
                # Read sensor data
                logger.info("Reading sensor data...")
                data = self._read_sensor_data()
                
                if data:
                    logger.info(f"Sensor data: {data}")
                    
                    # Publish to ThingsBoard
                    if self._publish_data(data):
                        logger.info("Data published successfully")
                    else:
                        logger.warning("Failed to publish data")
                else:
                    logger.warning("No valid sensor data to publish")
                
                # Wait for next reading
                logger.debug(f"Waiting {reading_interval} seconds until next reading...")
                time.sleep(reading_interval)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            return False
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the monitoring application"""
        if not self.running:
            return
        
        logger.info("Stopping NPK Monitor application...")
        self.running = False
        
        # Print statistics
        self._print_statistics()
        
        # Close connections
        if self.sensor:
            self.sensor.close()
        
        if self.publisher:
            self.publisher.disconnect()
        
        logger.info("NPK Monitor stopped")
    
    def _print_statistics(self):
        """Print application statistics"""
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            
            logger.info("=== Statistics ===")
            logger.info(f"Uptime: {uptime}")
            logger.info(f"Total readings: {self.stats['readings_count']}")
            logger.info(f"Successful publishes: {self.stats['publish_success']}")
            logger.info(f"Failed publishes: {self.stats['publish_failed']}")
            logger.info(f"Sensor errors: {self.stats['sensor_errors']}")
            
            if self.stats['readings_count'] > 0:
                success_rate = (self.stats['publish_success'] / self.stats['readings_count']) * 100
                logger.info(f"Success rate: {success_rate:.1f}%")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NPK Sensor to ThingsBoard Monitor')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Test mode - read sensor and print data without publishing')
    args = parser.parse_args()
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/npk-monitor.log') if Path('/var/log').exists() else logging.NullHandler()
        ]
    )
    
    global logger
    logger = logging.getLogger(__name__)
    
    if args.dry_run:
        logger.info("Running in DRY-RUN mode")
        # TODO: Implement dry-run mode
        logger.warning("Dry-run mode not yet implemented")
        return 1
    
    try:
        # Create and start monitor
        monitor = NPKMonitor(config_path=args.config)
        success = monitor.start()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
