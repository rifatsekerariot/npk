#!/usr/bin/env python3
"""
NPK Sensor Reader Module
Reads Nitrogen, Phosphorus, and Potassium values from NPK sensor via RS485/Modbus RTU
"""

import minimalmodbus
import serial
import time
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class NPKSensorReader:
    """
    NPK Sensor Reader using Modbus RTU protocol over RS485
    
    Typical NPK sensors use Modbus RTU with:
    - Slave ID: 1 (default)
    - Baud Rate: 4800 or 9600
    - Data bits: 8
    - Parity: None
    - Stop bits: 1
    """
    
    # Default Modbus register addresses for NPK sensors
    # These may vary by sensor model - configure in config.yaml
    DEFAULT_REGISTERS = {
        'nitrogen': 0x001E,   # Nitrogen content (mg/kg)
        'phosphorus': 0x001F, # Phosphorus content (mg/kg)
        'potassium': 0x0020,  # Potassium content (mg/kg)
        'temperature': 0x0012, # Temperature (°C) - optional
        'moisture': 0x0013,    # Moisture (%) - optional
        'ph': 0x0006,          # pH value - optional
        'ec': 0x0015,          # Electrical Conductivity (μS/cm) - optional
    }
    
    def __init__(self, 
                 port: str = '/dev/ttyS0',
                 slave_id: int = 1,
                 baudrate: int = 4800,
                 timeout: float = 1.0,
                 registers: Optional[Dict[str, int]] = None):
        """
        Initialize NPK Sensor Reader
        
        Args:
            port: Serial port for RS485 communication
            slave_id: Modbus slave ID of the sensor
            baudrate: Communication baud rate
            timeout: Serial communication timeout in seconds
            registers: Custom register addresses (optional)
        """
        self.port = port
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.timeout = timeout
        self.registers = registers or self.DEFAULT_REGISTERS.copy()
        
        self.instrument = None
        self._initialize_instrument()
        
    def _initialize_instrument(self):
        """Initialize Modbus RTU instrument"""
        try:
            self.instrument = minimalmodbus.Instrument(self.port, self.slave_id)
            self.instrument.serial.baudrate = self.baudrate
            self.instrument.serial.bytesize = 8
            self.instrument.serial.parity = serial.PARITY_NONE
            self.instrument.serial.stopbits = 1
            self.instrument.serial.timeout = self.timeout
            self.instrument.mode = minimalmodbus.MODE_RTU
            self.instrument.clear_buffers_before_each_transaction = True
            
            logger.info(f"Initialized NPK sensor on {self.port} (Slave ID: {self.slave_id}, Baudrate: {self.baudrate})")
        except Exception as e:
            logger.error(f"Failed to initialize sensor: {e}")
            raise
    
    def _read_register(self, register_address: int, decimals: int = 0, signed: bool = False) -> Optional[float]:
        """
        Read a single Modbus register
        
        Args:
            register_address: Modbus register address
            decimals: Number of decimal places
            signed: Whether the value is signed
            
        Returns:
            Register value or None on error
        """
        try:
            value = self.instrument.read_register(
                register_address, 
                numberOfDecimals=decimals,
                functioncode=3,  # Read Holding Registers
                signed=signed
            )
            return value
        except Exception as e:
            logger.error(f"Error reading register 0x{register_address:04X}: {e}")
            return None
    
    def read_nitrogen(self) -> Optional[float]:
        """Read nitrogen content (mg/kg or ppm)"""
        value = self._read_register(self.registers['nitrogen'], decimals=0)
        if value is not None:
            logger.debug(f"Nitrogen: {value} mg/kg")
        return value
    
    def read_phosphorus(self) -> Optional[float]:
        """Read phosphorus content (mg/kg or ppm)"""
        value = self._read_register(self.registers['phosphorus'], decimals=0)
        if value is not None:
            logger.debug(f"Phosphorus: {value} mg/kg")
        return value
    
    def read_potassium(self) -> Optional[float]:
        """Read potassium content (mg/kg or ppm)"""
        value = self._read_register(self.registers['potassium'], decimals=0)
        if value is not None:
            logger.debug(f"Potassium: {value} mg/kg")
        return value
    
    def read_temperature(self) -> Optional[float]:
        """Read soil temperature (°C) if available"""
        if 'temperature' in self.registers:
            value = self._read_register(self.registers['temperature'], decimals=1)
            if value is not None:
                logger.debug(f"Temperature: {value} °C")
            return value
        return None
    
    def read_moisture(self) -> Optional[float]:
        """Read soil moisture (%) if available"""
        if 'moisture' in self.registers:
            value = self._read_register(self.registers['moisture'], decimals=1)
            if value is not None:
                logger.debug(f"Moisture: {value} %")
            return value
        return None
    
    def read_ph(self) -> Optional[float]:
        """Read soil pH if available"""
        if 'ph' in self.registers:
            value = self._read_register(self.registers['ph'], decimals=1)
            if value is not None:
                logger.debug(f"pH: {value}")
            return value
        return None
    
    def read_ec(self) -> Optional[float]:
        """Read electrical conductivity (μS/cm) if available"""
        if 'ec' in self.registers:
            value = self._read_register(self.registers['ec'], decimals=0)
            if value is not None:
                logger.debug(f"EC: {value} μS/cm")
            return value
        return None
    
    def read_npk(self) -> Dict[str, Optional[float]]:
        """
        Read all NPK values
        
        Returns:
            Dictionary with N, P, K values
        """
        return {
            'nitrogen': self.read_nitrogen(),
            'phosphorus': self.read_phosphorus(),
            'potassium': self.read_potassium()
        }
    
    def read_all_sensors(self) -> Dict[str, Optional[float]]:
        """
        Read all available sensor values including NPK and optional parameters
        
        Returns:
            Dictionary with all sensor readings
        """
        data = self.read_npk()
        
        # Add optional sensors if configured
        temp = self.read_temperature()
        if temp is not None:
            data['temperature'] = temp
            
        moisture = self.read_moisture()
        if moisture is not None:
            data['moisture'] = moisture
            
        ph = self.read_ph()
        if ph is not None:
            data['ph'] = ph
            
        ec = self.read_ec()
        if ec is not None:
            data['ec'] = ec
        
        return data
    
    def test_connection(self) -> bool:
        """
        Test sensor connection by attempting to read nitrogen value
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            value = self.read_nitrogen()
            if value is not None:
                logger.info(f"Connection test successful! Read nitrogen value: {value} mg/kg")
                return True
            else:
                logger.warning("Connection test failed: could not read nitrogen value")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close serial connection"""
        if self.instrument and self.instrument.serial:
            try:
                self.instrument.serial.close()
                logger.info("Serial connection closed")
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")


def main():
    """Test NPK sensor reading"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NPK Sensor Reader Test')
    parser.add_argument('--port', default='/dev/ttyS0', help='Serial port (default: /dev/ttyS0)')
    parser.add_argument('--slave-id', type=int, default=1, help='Modbus slave ID (default: 1)')
    parser.add_argument('--baudrate', type=int, default=4800, help='Baud rate (default: 4800)')
    parser.add_argument('--test', action='store_true', help='Run connection test')
    parser.add_argument('--continuous', action='store_true', help='Continuous reading mode')
    parser.add_argument('--interval', type=int, default=5, help='Reading interval in seconds (default: 5)')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize sensor
        sensor = NPKSensorReader(
            port=args.port,
            slave_id=args.slave_id,
            baudrate=args.baudrate
        )
        
        if args.test:
            # Run connection test
            print("\n=== Connection Test ===")
            success = sensor.test_connection()
            print(f"Connection test: {'PASSED' if success else 'FAILED'}\n")
            return 0 if success else 1
        
        if args.continuous:
            # Continuous reading mode
            print(f"\n=== Continuous Reading Mode (Interval: {args.interval}s) ===")
            print("Press Ctrl+C to stop\n")
            
            try:
                while True:
                    data = sensor.read_all_sensors()
                    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}]")
                    print(f"  Nitrogen (N):   {data.get('nitrogen', 'N/A')} mg/kg")
                    print(f"  Phosphorus (P): {data.get('phosphorus', 'N/A')} mg/kg")
                    print(f"  Potassium (K):  {data.get('potassium', 'N/A')} mg/kg")
                    
                    if 'temperature' in data:
                        print(f"  Temperature:    {data['temperature']} °C")
                    if 'moisture' in data:
                        print(f"  Moisture:       {data['moisture']} %")
                    if 'ph' in data:
                        print(f"  pH:             {data['ph']}")
                    if 'ec' in data:
                        print(f"  EC:             {data['ec']} μS/cm")
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n\nStopped by user")
        else:
            # Single reading
            print("\n=== Single Reading ===")
            data = sensor.read_all_sensors()
            print(f"Nitrogen (N):   {data.get('nitrogen', 'N/A')} mg/kg")
            print(f"Phosphorus (P): {data.get('phosphorus', 'N/A')} mg/kg")
            print(f"Potassium (K):  {data.get('potassium', 'N/A')} mg/kg")
            
            if 'temperature' in data:
                print(f"Temperature:    {data['temperature']} °C")
            if 'moisture' in data:
                print(f"Moisture:       {data['moisture']} %")
            if 'ph' in data:
                print(f"pH:             {data['ph']}")
            if 'ec' in data:
                print(f"EC:             {data['ec']} μS/cm")
            print()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        sensor.close()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
