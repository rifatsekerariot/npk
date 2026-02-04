#!/bin/bash
###############################################################################
# NPK Sensor Monitor - Zero-Touch Installation Script
# For Raspberry Pi Zero 2W with Waveshare RS485 HAT
#
# This script installs and configures the NPK sensor monitoring system
# with automatic startup via systemd service
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/npk-monitor"
CONFIG_DIR="/etc/npk-monitor"
LOG_DIR="/var/log/npk-monitor"
SERVICE_NAME="npk-monitor"
PYTHON_BIN="/usr/bin/python3"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        echo "Please run: sudo $0"
        exit 1
    fi
}

###############################################################################
# Installation Steps
###############################################################################

step_greeting() {
    clear
    print_header "NPK Sensor Monitor - Installation"
    echo ""
    echo "This script will install and configure the NPK sensor monitoring system"
    echo "on your Raspberry Pi Zero 2W with Waveshare RS485 HAT."
    echo ""
    echo "The following will be installed:"
    echo "  • Python dependencies (pyserial, minimalmodbus, paho-mqtt)"
    echo "  • NPK Monitor application"
    echo "  • Systemd service for automatic startup"
    echo "  • RS485 UART configuration"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
}

step_system_update() {
    print_header "Step 1: Updating System"
    
    print_info "Updating package lists..."
    apt-get update -qq
    print_success "Package lists updated"
    
    print_info "Upgrading system packages (this may take a while)..."
    apt-get upgrade -y -qq
    print_success "System packages upgraded"
}

step_install_dependencies() {
    print_header "Step 2: Installing Dependencies"
    
    print_info "Installing Python3 and pip..."
    apt-get install -y python3 python3-pip python3-venv git -qq
    print_success "Python3 and pip installed"
    
    print_info "Installing system dependencies..."
    apt-get install -y build-essential python3-dev -qq
    print_success "System dependencies installed"
}

step_enable_uart() {
    print_header "Step 3: Enabling UART for RS485"
    
    print_info "Configuring UART in /boot/config.txt..."
    
    # Backup config.txt
    if [ ! -f /boot/config.txt.backup ]; then
        cp /boot/config.txt /boot/config.txt.backup
        print_info "Created backup: /boot/config.txt.backup"
    fi
    
    # Enable UART
    if ! grep -q "enable_uart=1" /boot/config.txt; then
        echo "enable_uart=1" >> /boot/config.txt
        print_success "UART enabled in config.txt"
    else
        print_warning "UART already enabled"
    fi
    
    # Disable Bluetooth to free up UART (for Pi Zero 2W)
    if ! grep -q "dtoverlay=disable-bt" /boot/config.txt; then
        echo "dtoverlay=disable-bt" >> /boot/config.txt
        print_success "Bluetooth disabled (UART freed)"
    else
        print_warning "Bluetooth overlay already configured"
    fi
    
    # Disable serial console
    print_info "Disabling serial console..."
    systemctl disable serial-getty@ttyS0.service 2>/dev/null || true
    systemctl mask serial-getty@ttyS0.service 2>/dev/null || true
    
    # Remove console from cmdline.txt
    if [ -f /boot/cmdline.txt ]; then
        sed -i 's/console=serial0,115200 //' /boot/cmdline.txt
        sed -i 's/console=ttyAMA0,115200 //' /boot/cmdline.txt
        print_success "Serial console disabled"
    fi
    
    print_success "UART configuration completed"
}

step_create_directories() {
    print_header "Step 4: Creating Directories"
    
    print_info "Creating application directory: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/src"
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/dashboard"
    print_success "Application directories created"
    
    print_info "Creating configuration directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
    print_success "Configuration directory created"
    
    print_info "Creating log directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    print_success "Log directory created"
}

step_install_application() {
    print_header "Step 5: Installing Application Files"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    print_info "Copying application files from $SCRIPT_DIR..."
    
    # Copy source files
    if [ -d "$SCRIPT_DIR/src" ]; then
        cp -r "$SCRIPT_DIR/src"/* "$INSTALL_DIR/src/"
        chmod +x "$INSTALL_DIR/src"/*.py
        print_success "Source files copied"
    else
        print_error "Source directory not found!"
        exit 1
    fi
    
    # Copy configuration
    if [ -f "$SCRIPT_DIR/config/config.yaml" ]; then
        cp "$SCRIPT_DIR/config/config.yaml" "$CONFIG_DIR/config.yaml"
        chmod 644 "$CONFIG_DIR/config.yaml"
        print_success "Configuration file copied"
    else
        print_error "Configuration file not found!"
        exit 1
    fi
    
    # Copy dashboard if exists
    if [ -d "$SCRIPT_DIR/dashboard" ]; then
        cp -r "$SCRIPT_DIR/dashboard"/* "$INSTALL_DIR/dashboard/" 2>/dev/null || true
        print_info "Dashboard files copied (optional)"
    fi
}

step_install_python_packages() {
    print_header "Step 6: Installing Python Packages"
    
    print_info "Installing Python dependencies..."
    
    # Install from requirements.txt
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet
        print_success "Python packages installed"
    else
        print_warning "requirements.txt not found, installing packages manually..."
        pip3 install pyserial minimalmodbus paho-mqtt PyYAML --quiet
        print_success "Core Python packages installed"
    fi
}

step_install_service() {
    print_header "Step 7: Installing Systemd Service"
    
    print_info "Creating systemd service file..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=NPK Sensor Monitor Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${PYTHON_BIN} -u ${INSTALL_DIR}/src/main.py --config ${CONFIG_DIR}/config.yaml
Restart=always
RestartSec=10
StandardOutput=append:${LOG_DIR}/npk-monitor.log
StandardError=append:${LOG_DIR}/npk-monitor.error.log

# Environment
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Service file created"
    
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
    
    print_info "Enabling service to start on boot..."
    systemctl enable "${SERVICE_NAME}.service"
    print_success "Service enabled"
}

step_configuration_prompt() {
    print_header "Step 8: Configuration"
    
    echo ""
    print_warning "IMPORTANT: You must configure the system before starting!"
    echo ""
    echo "Edit the configuration file:"
    echo "  ${GREEN}sudo nano ${CONFIG_DIR}/config.yaml${NC}"
    echo ""
    echo "Required settings:"
    echo "  1. ThingsBoard access token (thingsboard.access_token)"
    echo "  2. ThingsBoard host (if using self-hosted)"
    echo "  3. Sensor Modbus registers (if different from defaults)"
    echo ""
    read -p "Press Enter to open the configuration file now..."
    
    nano "${CONFIG_DIR}/config.yaml"
}

step_complete() {
    print_header "Installation Complete!"
    
    echo ""
    print_success "NPK Sensor Monitor has been installed successfully!"
    echo ""
    echo "Service management commands:"
    echo "  ${GREEN}sudo systemctl start ${SERVICE_NAME}${NC}   - Start the service"
    echo "  ${GREEN}sudo systemctl stop ${SERVICE_NAME}${NC}    - Stop the service"
    echo "  ${GREEN}sudo systemctl status ${SERVICE_NAME}${NC}  - Check service status"
    echo "  ${GREEN}sudo systemctl restart ${SERVICE_NAME}${NC} - Restart the service"
    echo ""
    echo "View logs:"
    echo "  ${GREEN}tail -f ${LOG_DIR}/npk-monitor.log${NC}       - Live log"
    echo "  ${GREEN}sudo journalctl -u ${SERVICE_NAME} -f${NC}     - Systemd journal"
    echo ""
    echo "Configuration file:"
    echo "  ${GREEN}${CONFIG_DIR}/config.yaml${NC}"
    echo ""
    print_warning "A system reboot is required for UART changes to take effect."
    echo ""
    read -p "Do you want to reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Rebooting in 3 seconds..."
        sleep 3
        reboot
    else
        print_info "Please reboot manually when ready: sudo reboot"
    fi
}

###############################################################################
# Main Installation Flow
###############################################################################

main() {
    check_root
    step_greeting
    step_system_update
    step_install_dependencies
    step_enable_uart
    step_create_directories
    step_install_application
    step_install_python_packages
    step_install_service
    step_configuration_prompt
    step_complete
}

# Run installation
main
