# PurpleAir Relay Control System

A complete air quality monitoring and HVAC control system using PurpleAir sensors, Arduino relay control, and web-based data visualization.

## System Overview

This project monitors indoor air quality using PurpleAir sensors and automatically controls ventilation through Arduino-based relays. Data is logged to Google Sheets and visualized through an interactive web dashboard.

## Components

### 1. Arduino Relay Control (`/arduino`)
- Monitors PurpleAir sensor data (local sensor or API access)
- Indoor and outdoor station support
- Controls ventilation based on configurable air quality thresholds
- Logs data to Google Sheets
- Manual override capability

### 2. Web Dashboard (`/dashboard`)
- Interactive visualization of air quality trends
- Identifies spike times and trends
- Real-time updates from Google Sheets

**Live Demo:** [https://jcdoll.github.io/purpleAirRelayControl](https://jcdoll.github.io/purpleAirRelayControl)

## Quick Start

### Arduino Setup
- Configure WiFi credentials and PurpleAir sensor IDs
- Upload sketch to Arduino using Arduino IDE
```

### Dashboard Setup
```bash
cd dashboard
npm install
npm start  # Run locally
npm run deploy  # Deploy to GitHub Pages
```

## Data Flow

1. **PurpleAir Sensor** → Measures PM2.5 levels
2. **Arduino** → Reads sensor data and controls relay
3. **Google Sheets** → Logs all measurements
4. **Web Dashboard** → Visualizes patterns and trends

## Configuration

### Arduino Configuration
- Set WiFi credentials in the sketch
- Configure PurpleAir sensor IDs
- Adjust relay control thresholds

### Dashboard Configuration
- Update Google Sheets CSV URL in `dashboard/src/App.js`
- Customize visualization preferences

## Hardware Requirements

- Arduino (ESP32 future work) - see detailed Arduino README
- Relay module
- PurpleAir sensor
- Ventilation system connection know how

## Software Requirements

- Arduino IDE
- Google account for spreadsheet logging
- Node.js and npm (for dashboard)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
