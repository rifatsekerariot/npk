#!/usr/bin/env python3
"""
MQTT Publisher Module for ThingsBoard
Publishes sensor telemetry data to ThingsBoard platform
"""

import paho.mqtt.client as mqtt
import json
import time
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ThingsBoardMQTTPublisher:
    """
    MQTT Publisher for ThingsBoard Platform
    
    ThingsBoard expects telemetry data in JSON format:
    {"temperature": 25.5, "humidity": 60}
    
    Connection uses device access token as username
    """
    
    def __init__(self,
                 host: str,
                 port: int = 1883,
                 access_token: str = None,
                 client_id: str = None,
                 keepalive: int = 60,
                 qos: int = 1):
        """
        Initialize ThingsBoard MQTT Publisher
        
        Args:
            host: MQTT broker hostname (e.g., 'demo.thingsboard.io')
            port: MQTT broker port (default: 1883)
            access_token: ThingsBoard device access token
            client_id: MQTT client ID (default: auto-generated)
            keepalive: Keep-alive interval in seconds
            qos: Quality of Service level (0, 1, or 2)
        """
        self.host = host
        self.port = port
        self.access_token = access_token
        self.client_id = client_id or f"npk_sensor_{int(time.time())}"
        self.keepalive = keepalive
        self.qos = qos
        
        self.connected = False
        self.client = None
        self.last_publish_time = None
        self.publish_count = 0
        
        # Callbacks
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        self.on_publish_callback: Optional[Callable] = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize MQTT client"""
        try:
            # Create MQTT client instance
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Set access token as username (ThingsBoard requirement)
            if self.access_token:
                self.client.username_pw_set(self.access_token)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            # Enable automatic reconnection
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            
            logger.info(f"Initialized MQTT client (ID: {self.client_id})")
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to ThingsBoard MQTT broker at {self.host}:{self.port}")
            if self.on_connect_callback:
                self.on_connect_callback()
        else:
            self.connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error (code: {rc})")
            logger.error(f"Connection failed: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        self.connected = False
        if rc == 0:
            logger.info("Disconnected from MQTT broker (clean)")
        else:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
        
        if self.on_disconnect_callback:
            self.on_disconnect_callback(rc)
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        logger.debug(f"Message published (mid: {mid})")
        if self.on_publish_callback:
            self.on_publish_callback(mid)
    
    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to MQTT broker
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.host}:{self.port}...")
            self.client.connect(self.host, self.port, self.keepalive)
            self.client.loop_start()
            
            # Wait for connection
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("Connection established")
                return True
            else:
                logger.error(f"Connection timeout after {timeout} seconds")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def publish_telemetry(self, data: Dict, timestamp: Optional[int] = None) -> bool:
        """
        Publish telemetry data to ThingsBoard
        
        Args:
            data: Dictionary of telemetry key-value pairs
            timestamp: Unix timestamp in milliseconds (optional)
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected:
            logger.error("Cannot publish: not connected to MQTT broker")
            return False
        
        try:
            # Prepare payload
            if timestamp:
                # With timestamp
                payload = {
                    "ts": timestamp,
                    "values": data
                }
            else:
                # Without timestamp (ThingsBoard will use server time)
                payload = data
            
            # Convert to JSON
            json_payload = json.dumps(payload)
            
            # Publish to ThingsBoard telemetry topic
            topic = "v1/devices/me/telemetry"
            result = self.client.publish(topic, json_payload, qos=self.qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.last_publish_time = datetime.now()
                self.publish_count += 1
                logger.info(f"Published telemetry: {json_payload}")
                return True
            else:
                logger.error(f"Publish failed (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing telemetry: {e}")
            return False
    
    def publish_attributes(self, data: Dict) -> bool:
        """
        Publish device attributes to ThingsBoard
        
        Args:
            data: Dictionary of attribute key-value pairs
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected:
            logger.error("Cannot publish: not connected to MQTT broker")
            return False
        
        try:
            # Convert to JSON
            json_payload = json.dumps(data)
            
            # Publish to ThingsBoard attributes topic
            topic = "v1/devices/me/attributes"
            result = self.client.publish(topic, json_payload, qos=self.qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published attributes: {json_payload}")
                return True
            else:
                logger.error(f"Publish failed (rc: {result.rc})")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing attributes: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected
    
    def get_statistics(self) -> Dict:
        """Get publisher statistics"""
        return {
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'publish_count': self.publish_count,
            'last_publish_time': self.last_publish_time.isoformat() if self.last_publish_time else None
        }


def main():
    """Test MQTT publisher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ThingsBoard MQTT Publisher Test')
    parser.add_argument('--host', required=True, help='MQTT broker host')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port (default: 1883)')
    parser.add_argument('--token', required=True, help='ThingsBoard device access token')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize publisher
        publisher = ThingsBoardMQTTPublisher(
            host=args.host,
            port=args.port,
            access_token=args.token
        )
        
        # Connect
        print(f"\nConnecting to {args.host}:{args.port}...")
        if not publisher.connect():
            print("Connection failed!")
            return 1
        
        print("Connected successfully!")
        
        if args.test:
            # Send test telemetry
            print("\nSending test telemetry...")
            test_data = {
                'nitrogen': 100,
                'phosphorus': 50,
                'potassium': 75,
                'temperature': 25.5,
                'test': True
            }
            
            if publisher.publish_telemetry(test_data):
                print("Test telemetry sent successfully!")
                print(f"Data: {json.dumps(test_data, indent=2)}")
            else:
                print("Failed to send test telemetry")
            
            # Send test attributes
            print("\nSending test attributes...")
            test_attrs = {
                'device_type': 'NPK Sensor',
                'firmware_version': '1.0.0',
                'location': 'Test Field'
            }
            
            if publisher.publish_attributes(test_attrs):
                print("Test attributes sent successfully!")
                print(f"Attributes: {json.dumps(test_attrs, indent=2)}")
            else:
                print("Failed to send test attributes")
            
            # Wait a bit
            time.sleep(2)
        
        # Show statistics
        stats = publisher.get_statistics()
        print("\n=== Statistics ===")
        print(f"Connected: {stats['connected']}")
        print(f"Broker: {stats['host']}:{stats['port']}")
        print(f"Client ID: {stats['client_id']}")
        print(f"Publish Count: {stats['publish_count']}")
        print(f"Last Publish: {stats['last_publish_time']}")
        print()
        
        # Disconnect
        publisher.disconnect()
        print("Disconnected\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
