# Air Quality Dashboard Implementation Plan

## Overview
This document contains complete instructions and source code for adding an interactive web dashboard to the existing `purpleAirRelayControl` repository. The dashboard will visualize air quality data from Google Sheets and be hosted on GitHub Pages.

## Repository Structure After Implementation

```
purpleAirRelayControl/
├── arduino/                      # Existing Arduino code (moved)
│   ├── purpleAirRelayControl.ino
│   └── [other Arduino files]
├── dashboard/                    # New React dashboard
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   ├── src/
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   ├── package.json
│   └── README.md
├── README.md                     # Updated main README
└── .gitignore                    # Updated gitignore
```

## Step 1: Reorganize Existing Repository

```bash
# Clone the repository
git clone https://github.com/jcdoll/purpleAirRelayControl.git
cd purpleAirRelayControl

# Create arduino subdirectory
mkdir arduino

# Move all Arduino-related files to arduino/
# Adjust these commands based on actual files in your repo
git mv *.ino arduino/ 2>/dev/null || true
git mv *.cpp arduino/ 2>/dev/null || true
git mv *.h arduino/ 2>/dev/null || true

# Update .gitignore at root level
cat >> .gitignore << 'EOF'

# React dashboard
dashboard/node_modules/
dashboard/build/
dashboard/.env.local
dashboard/.env.development.local
dashboard/.env.test.local
dashboard/.env.production.local
dashboard/npm-debug.log*
dashboard/yarn-debug.log*
dashboard/yarn-error.log*
.DS_Store
EOF

# Commit reorganization
git add .
git commit -m "Reorganize: Move Arduino code to subdirectory for dashboard addition"
git push
```

## Step 2: Set Up Google Sheets Data Source

### Publishing Google Sheets as CSV

ALREADY DONE: https://docs.google.com/spreadsheets/d/e/2PACX-1vRN0PHzfkvu7IMHEf2PG6_Ne4Vr-Pstsg0Sa8-WNBSy9a_-10Vvpr_jYGZxLszyMw8CybUq_7tDGkBq/pub?gid=394013654&single=true&output=csv

1. Open your Google Sheet with the air quality data
2. Go to **File → Share → Publish to web**
3. In the dropdown, choose **Comma-separated values (.csv)**
4. Select the specific sheet if you have multiple sheets
5. Click **Publish**
6. Copy the generated URL - it will look like:
   ```
   https://docs.google.com/spreadsheets/d/e/[LONG-ID]/pub?gid=0&single=true&output=csv
   ```
7. Save this URL - you'll need it in Step 3

## Step 3: Create React Dashboard

```bash
# From the root of purpleAirRelayControl
npx create-react-app dashboard
cd dashboard

# Install required dependencies
npm install papaparse react-plotly.js plotly.js
npm install --save-dev gh-pages

# Remove default React files we'll replace
rm src/App.js src/App.css src/App.test.js src/logo.svg
```

## Step 4: Add Dashboard Source Code

### File: `dashboard/package.json`
Update the existing package.json by adding these lines:

```json
{
  "name": "dashboard",
  "version": "0.1.0",
  "private": true,
  "homepage": "https://jcdoll.github.io/purpleAirRelayControl",
  "dependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "papaparse": "^5.4.1",
    "plotly.js": "^2.27.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-plotly.js": "^2.6.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "predeploy": "npm run build",
    "deploy": "gh-pages -d build"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "gh-pages": "^6.1.1"
  }
}
```

### File: `dashboard/src/App.js`

```javascript
import React, { useState, useEffect } from 'react';
import Papa from 'papaparse';
import Plot from 'react-plotly.js';
import './App.css';

// IMPORTANT: Replace this with your Google Sheets CSV URL from Step 2
const CSV_URL = 'YOUR_GOOGLE_SHEETS_CSV_URL_HERE';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState(30);
  const [selectedView, setSelectedView] = useState('heatmap');
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    fetchData();
    // Refresh data every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch(CSV_URL);
      const text = await response.text();
      
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          const processedData = results.data
            .filter(row => row.Timestamp && row.IndoorAirQuality !== null && row.IndoorAirQuality !== '')
            .map(row => ({
              ...row,
              timestamp: new Date(row.Timestamp),
              hour: new Date(row.Timestamp).getHours(),
              date: new Date(row.Timestamp).toISOString().split('T')[0],
              dayOfWeek: new Date(row.Timestamp).toLocaleDateString('en-US', { weekday: 'long' })
            }))
            .filter(row => !isNaN(row.timestamp.getTime())); // Filter out invalid dates
          
          setData(processedData);
          setLoading(false);
          setLastUpdate(new Date());
        },
        error: (error) => {
          setError(error.message);
          setLoading(false);
        }
      });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getHeatmapData = () => {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - dateRange);
    
    const recentData = data.filter(d => d.timestamp > cutoffDate);
    
    // Create pivot table
    const pivotData = {};
    recentData.forEach(row => {
      if (!pivotData[row.date]) {
        pivotData[row.date] = {};
      }
      if (!pivotData[row.date][row.hour]) {
        pivotData[row.date][row.hour] = [];
      }
      pivotData[row.date][row.hour].push(row.IndoorAirQuality);
    });
    
    // Calculate averages
    const dates = Object.keys(pivotData).sort();
    const hours = Array.from({length: 24}, (_, i) => i);
    const zValues = [];
    
    dates.forEach(date => {
      const row = [];
      hours.forEach(hour => {
        const values = pivotData[date][hour] || [];
        const avg = values.length > 0 ? values.reduce((a, b) => a + b) / values.length : null;
        row.push(avg);
      });
      zValues.push(row);
    });
    
    return {
      z: zValues,
      x: hours.map(h => `${h}:00`),
      y: dates,
      type: 'heatmap',
      colorscale: 'RdYlBu_r',
      reversescale: false,
      colorbar: {
        title: 'PM2.5<br>(µg/m³)',
        titleside: 'right'
      },
      hoverongaps: false,
      hovertemplate: 'Date: %{y}<br>Hour: %{x}<br>PM2.5: %{z:.1f} µg/m³<extra></extra>'
    };
  };

  const getHourlyStats = () => {
    const hourlyData = {};
    
    data.forEach(row => {
      if (!hourlyData[row.hour]) {
        hourlyData[row.hour] = [];
      }
      hourlyData[row.hour].push(row.IndoorAirQuality);
    });
    
    const hours = Array.from({length: 24}, (_, i) => i);
    const stats = hours.map(hour => {
      const values = hourlyData[hour] || [];
      return {
        hour,
        mean: values.length > 0 ? values.reduce((a, b) => a + b) / values.length : 0,
        max: values.length > 0 ? Math.max(...values) : 0,
        min: values.length > 0 ? Math.min(...values) : 0,
        count: values.length,
        spikes: values.filter(v => v > 50).length
      };
    });
    
    return stats;
  };

  const getTimeSeriesData = () => {
    const recentData = data.slice(-2000); // Last 2000 points
    
    return [
      {
        x: recentData.map(d => d.timestamp),
        y: recentData.map(d => d.IndoorAirQuality),
        type: 'scatter',
        mode: 'lines',
        name: 'Indoor PM2.5',
        line: { color: 'red', width: 2 }
      },
      {
        x: recentData.map(d => d.timestamp),
        y: recentData.map(d => d.OutdoorAirQuality),
        type: 'scatter',
        mode: 'lines',
        name: 'Outdoor PM2.5',
        line: { color: 'blue', width: 1 }
      }
    ];
  };

  const getDayOfWeekAnalysis = () => {
    const dayData = {};
    const dayOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    data.forEach(row => {
      const key = `${row.dayOfWeek}-${row.hour}`;
      if (!dayData[key]) {
        dayData[key] = [];
      }
      dayData[key].push(row.IndoorAirQuality);
    });
    
    return dayOrder.map(day => ({
      x: Array.from({length: 24}, (_, i) => i),
      y: Array.from({length: 24}, (_, hour) => {
        const key = `${day}-${hour}`;
        const values = dayData[key] || [];
        return values.length > 0 ? values.reduce((a, b) => a + b) / values.length : 0;
      }),
      type: 'scatter',
      mode: 'lines',
      name: day,
      line: { width: 2 }
    }));
  };

  const getCorrelationData = () => {
    return {
      x: data.map(d => d.OutdoorAirQuality),
      y: data.map(d => d.IndoorAirQuality),
      mode: 'markers',
      type: 'scatter',
      marker: {
        color: data.map(d => d.hour),
        colorscale: 'Viridis',
        showscale: true,
        colorbar: {
          title: 'Hour',
          titleside: 'right'
        },
        size: 4
      },
      text: data.map(d => `Hour: ${d.hour}:00`),
      hovertemplate: 'Outdoor: %{x:.1f}<br>Indoor: %{y:.1f}<br>%{text}<extra></extra>'
    };
  };

  const calculatePatternSummary = () => {
    if (data.length === 0) return null;
    
    const hourlyStats = getHourlyStats();
    const peakHour = hourlyStats.reduce((prev, current) => 
      prev.mean > current.mean ? prev : current
    );
    
    const totalSpikes = data.filter(d => d.IndoorAirQuality > 50).length;
    const avgIndoor = data.reduce((sum, d) => sum + d.IndoorAirQuality, 0) / data.length;
    const avgOutdoor = data.reduce((sum, d) => sum + d.OutdoorAirQuality, 0) / data.length;
    
    // Find most consistent spike hours
    const spikesByHour = hourlyStats
      .map(h => ({ hour: h.hour, spikeRate: h.spikes / h.count }))
      .sort((a, b) => b.spikeRate - a.spikeRate)
      .slice(0, 3);
    
    return {
      peakHour: peakHour.hour,
      peakValue: peakHour.mean.toFixed(1),
      totalSpikes,
      avgIndoor: avgIndoor.toFixed(1),
      avgOutdoor: avgOutdoor.toFixed(1),
      dataPoints: data.length,
      topSpikeHours: spikesByHour
    };
  };

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading air quality data...</h2>
        <div className="spinner"></div>
        <p>Fetching data from Google Sheets...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h2>Error loading data</h2>
        <p>{error}</p>
        <p>Make sure your Google Sheet is published to web as CSV</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  const summary = calculatePatternSummary();
  const hourlyStats = getHourlyStats();

  return (
    <div className="App">
      <header>
        <h1>🏠 Air Quality Pattern Explorer</h1>
        <p>Analyzing {summary?.dataPoints.toLocaleString()} measurements from PurpleAir sensor</p>
        <p className="last-update">Last updated: {lastUpdate.toLocaleString()}</p>
      </header>

      <div className="summary-cards">
        <div className="card">
          <h3>Peak Hour</h3>
          <div className="value">{summary?.peakHour}:00</div>
          <div className="label">{summary?.peakValue} µg/m³ avg</div>
        </div>
        <div className="card">
          <h3>Total Spikes</h3>
          <div className="value">{summary?.totalSpikes}</div>
          <div className="label">&gt;50 µg/m³</div>
        </div>
        <div className="card">
          <h3>Indoor Average</h3>
          <div className="value">{summary?.avgIndoor}</div>
          <div className="label">µg/m³</div>
        </div>
        <div className="card">
          <h3>Outdoor Average</h3>
          <div className="value">{summary?.avgOutdoor}</div>
          <div className="label">µg/m³</div>
        </div>
      </div>

      {summary?.topSpikeHours && (
        <div className="spike-summary">
          <p>🎯 Most frequent spike hours: {
            summary.topSpikeHours.map(h => `${h.hour}:00 (${(h.spikeRate * 100).toFixed(0)}%)`).join(', ')
          }</p>
        </div>
      )}

      <div className="controls">
        <div className="view-selector">
          <button 
            className={selectedView === 'heatmap' ? 'active' : ''}
            onClick={() => setSelectedView('heatmap')}
          >
            Heat Map
          </button>
          <button 
            className={selectedView === 'hourly' ? 'active' : ''}
            onClick={() => setSelectedView('hourly')}
          >
            Hourly Analysis
          </button>
          <button 
            className={selectedView === 'timeline' ? 'active' : ''}
            onClick={() => setSelectedView('timeline')}
          >
            Timeline
          </button>
          <button 
            className={selectedView === 'correlation' ? 'active' : ''}
            onClick={() => setSelectedView('correlation')}
          >
            Correlation
          </button>
          <button 
            className={selectedView === 'dayofweek' ? 'active' : ''}
            onClick={() => setSelectedView('dayofweek')}
          >
            Day Patterns
          </button>
        </div>
        
        {selectedView === 'heatmap' && (
          <div className="date-range">
            <label>Days to show: </label>
            <select value={dateRange} onChange={(e) => setDateRange(Number(e.target.value))}>
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        )}
        
        <button onClick={fetchData} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      <div className="chart-container">
        {selectedView === 'heatmap' && data.length > 0 && (
          <div>
            <h2>PM2.5 Levels by Hour - Last {dateRange} Days</h2>
            <p className="subtitle">Look for vertical patterns (time-based) or horizontal patterns (day-specific)</p>
            <Plot
              data={[getHeatmapData()]}
              layout={{
                xaxis: { title: 'Hour of Day', tickmode: 'linear' },
                yaxis: { title: 'Date', tickmode: 'auto', nticks: 20 },
                margin: { l: 100, r: 50, t: 50, b: 50 }
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '600px' }}
            />
          </div>
        )}

        {selectedView === 'hourly' && (
          <div>
            <h2>Hourly Pattern Analysis</h2>
            <Plot
              data={[
                {
                  x: hourlyStats.map(h => `${h.hour}:00`),
                  y: hourlyStats.map(h => h.mean),
                  type: 'bar',
                  name: 'Average PM2.5',
                  marker: {
                    color: hourlyStats.map(h => h.mean),
                    colorscale: 'RdYlBu_r',
                    showscale: false
                  },
                  text: hourlyStats.map(h => `${h.mean.toFixed(1)} µg/m³`),
                  textposition: 'auto',
                },
                {
                  x: hourlyStats.map(h => `${h.hour}:00`),
                  y: hourlyStats.map(h => h.spikes),
                  type: 'scatter',
                  mode: 'lines+markers',
                  name: 'Spike Count (>50)',
                  yaxis: 'y2',
                  line: { color: 'orange', width: 2 },
                  marker: { size: 8 }
                }
              ]}
              layout={{
                xaxis: { title: 'Hour of Day' },
                yaxis: { title: 'Average PM2.5 (µg/m³)' },
                yaxis2: {
                  title: 'Number of Spikes',
                  overlaying: 'y',
                  side: 'right'
                },
                showlegend: true,
                legend: { x: 0.1, y: 0.9 }
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '500px' }}
            />
          </div>
        )}

        {selectedView === 'timeline' && (
          <div>
            <h2>Recent Timeline</h2>
            <p className="subtitle">Zoom and pan to explore specific time periods</p>
            <Plot
              data={getTimeSeriesData()}
              layout={{
                xaxis: { 
                  title: 'Time',
                  rangeslider: { visible: true }
                },
                yaxis: { title: 'PM2.5 (µg/m³)' },
                showlegend: true,
                legend: { x: 0.1, y: 0.9 }
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '500px' }}
            />
          </div>
        )}

        {selectedView === 'correlation' && (
          <div>
            <h2>Indoor vs Outdoor Correlation</h2>
            <p className="subtitle">Colors represent hour of day - look for time-based patterns</p>
            <Plot
              data={[getCorrelationData()]}
              layout={{
                xaxis: { title: 'Outdoor PM2.5 (µg/m³)' },
                yaxis: { title: 'Indoor PM2.5 (µg/m³)' },
                showlegend: false
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '600px' }}
            />
          </div>
        )}

        {selectedView === 'dayofweek' && (
          <div>
            <h2>Day of Week Patterns</h2>
            <p className="subtitle">Compare hourly patterns across different days</p>
            <Plot
              data={getDayOfWeekAnalysis()}
              layout={{
                xaxis: { 
                  title: 'Hour of Day',
                  tickmode: 'linear',
                  tick0: 0,
                  dtick: 1
                },
                yaxis: { title: 'Average PM2.5 (µg/m³)' },
                showlegend: true,
                legend: { x: 1.02, y: 0.5 }
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '500px' }}
            />
          </div>
        )}
      </div>

      <footer>
        <p>Data source: Google Sheets (auto-refreshes every 5 minutes)</p>
        <p>
          <a href="https://github.com/jcdoll/purpleAirRelayControl" target="_blank" rel="noopener noreferrer">
            View on GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
```

### File: `dashboard/src/App.css`

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5;
}

.App {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 30px;
}

header h1 {
  color: #333;
  margin-bottom: 10px;
  font-size: 2.5rem;
}

header p {
  color: #666;
  font-size: 1.1rem;
  margin: 5px 0;
}

.last-update {
  font-size: 0.9rem;
  color: #888;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card .value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2196F3;
  margin: 10px 0;
}

.card .label {
  color: #888;
  font-size: 0.9rem;
}

/* Spike Summary */
.spike-summary {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
}

.spike-summary p {
  margin: 0;
  color: #856404;
  font-weight: 500;
}

/* Controls */
.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.view-selector {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.view-selector button {
  padding: 10px 20px;
  border: 2px solid #ddd;
  background: white;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
}

.view-selector button:hover {
  border-color: #2196F3;
  color: #2196F3;
}

.view-selector button.active {
  background: #2196F3;
  color: white;
  border-color: #2196F3;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-range label {
  font-weight: 500;
  color: #666;
}

.date-range select {
  padding: 8px 15px;
  border: 2px solid #ddd;
  border-radius: 5px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
}

.refresh-btn {
  padding: 10px 20px;
  border: 2px solid #4CAF50;
  background: white;
  color: #4CAF50;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.refresh-btn:hover {
  background: #4CAF50;
  color: white;
}

/* Chart Container */
.chart-container {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.chart-container h2 {
  margin-top: 0;
  color: #333;
}

.subtitle {
  color: #666;
  margin-bottom: 20px;
  font-style: italic;
}

/* Loading and Error States */
.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: white;
  border-radius: 8px;
  padding: 40px;
  margin: 40px auto;
  max-width: 500px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.loading h2, .error h2 {
  color: #333;
  margin-bottom: 20px;
}

.error p {
  color: #666;
  margin-bottom: 10px;
  text-align: center;
}

.error button {
  padding: 10px 20px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 10px;
}

.error button:hover {
  background: #1976D2;
}

/* Spinner */
.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2196F3;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 20px 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Footer */
footer {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 0.9rem;
}

footer a {
  color: #2196F3;
  text-decoration: none;
}

footer a:hover {
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 768px) {
  .App {
    padding: 10px;
  }
  
  header h1 {
    font-size: 2rem;
  }
  
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .card {
    padding: 15px;
  }
  
  .card .value {
    font-size: 2rem;
  }
  
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .view-selector {
    justify-content: center;
  }
  
  .view-selector button {
    padding: 8px 15px;
    font-size: 0.9rem;
  }
  
  .chart-container {
    padding: 15px;
  }
  
  .date-range {
    justify-content: center;
  }
}

/* Print Styles */
@media print {
  .controls {
    display: none;
  }
  
  .chart-container {
    box-shadow: none;
    break-inside: avoid;
  }
  
  footer {
    display: none;
  }
}
```

### File: `dashboard/public/index.html`
Update the existing file with:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#2196F3" />
    <meta
      name="description"
      content="Air Quality Dashboard - Monitor indoor PM2.5 patterns from PurpleAir sensor"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>Air Quality Dashboard</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

### File: `dashboard/public/manifest.json`
Update the existing file with:

```json
{
  "short_name": "Air Quality",
  "name": "Air Quality Dashboard",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#2196F3",
  "background_color": "#ffffff"
}
```

### File: `dashboard/README.md`

```markdown
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
```

## Step 5: Update Main README

### File: `README.md` (root level)

```markdown
# PurpleAir Relay Control System

A complete air quality monitoring and control system using PurpleAir sensors, Arduino relay control, and web-based data visualization.

## System Overview

This project monitors indoor air quality using PurpleAir sensors and automatically controls ventilation through Arduino-based relays. Data is logged to Google Sheets and visualized through an interactive web dashboard.

## Components

### 1. Arduino Relay Control (`/arduino`)
- Monitors PurpleAir sensor data
- Controls ventilation based on air quality thresholds
- Logs data to Google Sheets
- Responds to outdoor air quality conditions

**Key Features:**
- Automatic ventilation control
- Real-time data logging
- Configurable thresholds
- Manual override capability

### 2. Web Dashboard (`/dashboard`)
- Interactive visualization of air quality patterns
- Pattern discovery without assumptions
- Identifies spike times and trends
- Real-time updates from Google Sheets

**Live Demo:** [https://jcdoll.github.io/purpleAirRelayControl](https://jcdoll.github.io/purpleAirRelayControl)

## Quick Start

### Arduino Setup
```bash
cd arduino
# Upload sketch to Arduino using Arduino IDE
# Configure WiFi credentials and PurpleAir sensor IDs
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

- Arduino (ESP8266/ESP32 recommended)
- Relay module
- PurpleAir sensor
- Ventilation system connection

## Software Requirements

- Arduino IDE
- Node.js and npm (for dashboard)
- Google Sheets account

## Contributing

Pull requests are welcome! Please open an issue first to discuss proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PurpleAir for their excellent air quality sensors
- The open-source community for various libraries used

## Support

For issues or questions:
- Open a GitHub issue
- Check existing issues for solutions
- Review the wiki for detailed documentation
```

## Step 6: Deploy to GitHub Pages

```bash
# From the root of the repository
cd dashboard

# Build and deploy
npm run deploy

# This will:
# 1. Build the React app
# 2. Create/update the gh-pages branch
# 3. Deploy only the built files
# 4. Your dashboard will be live at https://jcdoll.github.io/purpleAirRelayControl
```

## Step 7: Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Scroll to "Pages" section
3. Source should be set to "Deploy from a branch"
4. Branch should be "gh-pages" and folder should be "/ (root)"
5. Save the settings

## Final Steps

1. **Update the CSV URL**: In `dashboard/src/App.js`, replace `YOUR_GOOGLE_SHEETS_CSV_URL_HERE` with your actual Google Sheets published CSV URL

2. **Test locally first**:
   ```bash
   cd dashboard
   npm start
   ```

3. **Deploy when ready**:
   ```bash
   npm run deploy
   ```

4. **Verify deployment**: Visit https://jcdoll.github.io/purpleAirRelayControl

## Troubleshooting

### Common Issues

1. **CORS errors with Google Sheets**:
   - Make sure the sheet is published as CSV (not just shared)
   - Use the published URL, not the regular sheet URL

2. **Page not loading after deploy**:
   - Wait 5-10 minutes for GitHub Pages to update
   - Check repository settings to ensure Pages is enabled
   - Clear browser cache

3. **Data not updating**:
   - Verify Google Sheets is updating correctly
   - Check browser console for errors
   - Ensure CSV URL is correct

### Data Requirements

Your Google Sheets CSV should have these columns:
- `Timestamp` (in a parseable date format)
- `IndoorAirQuality` (numeric PM2.5 values)
- `OutdoorAirQuality` (numeric PM2.5 values)
- `VentilationState` (optional)
- `SwitchState` (optional)

## Success Checklist

- [ ] Arduino code moved to `/arduino` subdirectory
- [ ] Dashboard created in `/dashboard` subdirectory
- [ ] Google Sheets published as CSV
- [ ] CSV URL updated in App.js
- [ ] Dependencies installed (`npm install`)
- [ ] Local testing successful (`npm start`)
- [ ] Deployed to GitHub Pages (`npm run deploy`)
- [ ] Live site accessible at GitHub Pages URL
- [ ] README files updated

## Next Steps

After implementation, you can:
1. Add weather data integration
2. Implement email alerts for high PM2.5
3. Add data export functionality
4. Create mobile app version
5. Add historical comparisons
```
