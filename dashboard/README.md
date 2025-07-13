# Air Quality Dashboard

This React dashboard visualizes air quality data from the PurpleAir sensor connected via Arduino.

## Features

- **Heat Map**: Visualize PM2.5 patterns by hour across days
- **Hourly Analysis**: Identify which hours typically have highest PM2.5
- **Timeline View**: Explore historical data with zoom and pan
- **Correlation Analysis**: Compare indoor vs outdoor air quality
- **Day of Week Patterns**: See if patterns vary by day
- **Auto-refresh**: Data updates every 5 minutes from Google Sheets

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Update the Google Sheets CSV URL in `src/App.js`

3. Run locally:
   ```bash
   npm start
   ```

4. Deploy to GitHub Pages:
   ```bash
   npm run deploy
   ```

## Data Source

Data is fetched from a Google Sheets CSV file that's updated in real-time by the Arduino logger.

## Technologies

- React
- Plotly.js for interactive charts
- PapaParse for CSV parsing
- GitHub Pages for hosting 