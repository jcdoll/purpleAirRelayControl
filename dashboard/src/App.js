import React, { useState, useEffect, useCallback } from 'react';
import Papa from 'papaparse';
import Plot from 'react-plotly.js';
import './App.css';

// Google Sheets CSV URL
const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRN0PHzfkvu7IMHEf2PG6_Ne4Vr-Pstsg0Sa8-WNBSy9a_-10Vvpr_jYGZxLszyMw8CybUq_7tDGkBq/pub?gid=394013654&single=true&output=csv';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState(30);
  const [selectedView, setSelectedView] = useState('heatmap');

  const [annualHeatmapAggregation, setAnnualHeatmapAggregation] = useState('average');
  const [selectedYear, setSelectedYear] = useState(() => new Date().getFullYear());
  const [timeRangeType, setTimeRangeType] = useState('recent'); // 'recent' or 'previous_year'
  
  // Function to get available years from data
  const getAvailableYears = useCallback(() => {
    if (data.length === 0) return [new Date().getFullYear()];
    
    const years = [...new Set(data.map(row => row.timestamp.getFullYear()))];
    return years.sort((a, b) => b - a); // Sort in descending order (newest first)
  }, [data]);
  const [dateRangeMode, setDateRangeMode] = useState('predefined'); // 'predefined' or 'custom'
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedTimezone, setSelectedTimezone] = useState(() => {
    // Auto-detect local timezone offset
    const now = new Date();
    const offset = -now.getTimezoneOffset() / 60; // Convert to hours, flip sign
    return offset;
  });
  
  const [sourceTimezone, setSourceTimezone] = useState(() => {
    // Default to assuming source data is in local timezone
    const now = new Date();
    const offset = -now.getTimezoneOffset() / 60; // Convert to hours, flip sign
    return offset;
  });

  // Common timezone options
  const timezoneOptions = [
    { value: -12, label: 'UTC-12 (Baker Island)' },
    { value: -11, label: 'UTC-11 (Samoa)' },
    { value: -10, label: 'UTC-10 (Hawaii)' },
    { value: -9, label: 'UTC-9 (Alaska)' },
    { value: -8, label: 'UTC-8 (Pacific Standard)' },
    { value: -7, label: 'UTC-7 (Mountain/Pacific Daylight)' },
    { value: -6, label: 'UTC-6 (Central)' },
    { value: -5, label: 'UTC-5 (Eastern)' },
    { value: -4, label: 'UTC-4 (Atlantic)' },
    { value: -3, label: 'UTC-3 (Argentina)' },
    { value: -2, label: 'UTC-2 (Mid-Atlantic)' },
    { value: -1, label: 'UTC-1 (Azores)' },
    { value: 0, label: 'UTC (GMT)' },
    { value: 1, label: 'UTC+1 (Central European)' },
    { value: 2, label: 'UTC+2 (Eastern European)' },
    { value: 3, label: 'UTC+3 (Moscow)' },
    { value: 4, label: 'UTC+4 (Gulf)' },
    { value: 5, label: 'UTC+5 (Pakistan)' },
    { value: 6, label: 'UTC+6 (Bangladesh)' },
    { value: 7, label: 'UTC+7 (Indochina)' },
    { value: 8, label: 'UTC+8 (China)' },
    { value: 9, label: 'UTC+9 (Japan)' },
    { value: 10, label: 'UTC+10 (Australia East)' },
    { value: 11, label: 'UTC+11 (Solomon Islands)' },
    { value: 12, label: 'UTC+12 (Fiji)' }
  ];

  // Function to convert timestamp based on source timezone
  const convertToTimezone = (sourceDate, sourceTimezoneOffset, targetTimezoneOffset) => {
    // If source and target are the same, no conversion needed
    if (sourceTimezoneOffset === targetTimezoneOffset) {
      return sourceDate;
    }
    
    // Convert to UTC first, then to target timezone
    const sourceTime = sourceDate.getTime();
    const utcTime = sourceTime - (sourceTimezoneOffset * 60 * 60 * 1000);
    const localTime = utcTime + (targetTimezoneOffset * 60 * 60 * 1000);
    

    
    return new Date(localTime);
  };

  // Helper function to get a description of the current time range
  const getTimeRangeDescription = () => {
    if (dateRangeMode === 'custom') {
      if (!customStartDate || !customEndDate) return 'custom dates';
      const start = new Date(customStartDate).toLocaleDateString();
      const end = new Date(customEndDate).toLocaleDateString();
      return `${start} to ${end}`;
    }
    
    if (timeRangeType === 'previous_year') {
      return 'previous year';
    }
    
    if (dateRange === 180) return 'last 6 months';
    if (dateRange === 365) return 'last 12 months';
    return `last ${dateRange} days`;
  };

  // Function to get AQI color based on AQI value
  const getAQIColor = (aqiValue) => {
    if (aqiValue <= 50) return '#00E400';       // Green (Good)
    if (aqiValue <= 100) return '#FFDC00';     // Yellow (Moderate)
    if (aqiValue <= 150) return '#FF7E00';     // Orange (Unhealthy for Sensitive)
    if (aqiValue <= 200) return '#FF0000';     // Red (Unhealthy)
    if (aqiValue <= 300) return '#8F3F97';     // Purple (Very Unhealthy)
    return '#7E0023';                           // Maroon (Hazardous)
  };

  // Function to get AQI CSS class based on AQI value
  const getAQIClass = (aqiValue) => {
    if (aqiValue <= 50) return 'aqi-good';
    if (aqiValue <= 100) return 'aqi-moderate';
    if (aqiValue <= 150) return 'aqi-unhealthy-sensitive';
    if (aqiValue <= 200) return 'aqi-unhealthy';
    if (aqiValue <= 300) return 'aqi-very-unhealthy';
    return 'aqi-hazardous';
  };

  // Helper function to get filtered data based on current date range settings
  const getFilteredData = () => {
    // Get current time - since we're comparing with data that's already in display timezone,
    // we need current time in the same timezone
    const now = new Date();
    
    // If user browser is in same timezone as display, no conversion needed
    const browserTZOffset = -now.getTimezoneOffset() / 60;
    let displayNow;
    
    if (browserTZOffset === selectedTimezone) {
      displayNow = now;
    } else {
      // Convert current time to display timezone
      const offsetDiff = selectedTimezone - browserTZOffset;
      displayNow = new Date(now.getTime() + (offsetDiff * 60 * 60 * 1000));
    }
    

    
    let filteredData;
    
    if (dateRangeMode === 'custom') {
      if (!customStartDate || !customEndDate) return data;
      // Convert custom dates to display timezone
      const start = convertToTimezone(new Date(customStartDate), 0, selectedTimezone);
      const end = convertToTimezone(new Date(customEndDate), 0, selectedTimezone);
      end.setHours(23, 59, 59, 999); // Include the full end date
      filteredData = data.filter(d => d.timestamp >= start && d.timestamp <= end && d.timestamp <= displayNow);
    }
    else if (timeRangeType === 'previous_year') {
      const oneYearAgo = new Date(displayNow.getFullYear() - 1, displayNow.getMonth(), displayNow.getDate());
      const twoYearsAgo = new Date(displayNow.getFullYear() - 2, displayNow.getMonth(), displayNow.getDate());
      filteredData = data.filter(d => d.timestamp >= twoYearsAgo && d.timestamp <= oneYearAgo);
    }
    else {
      // Recent data (predefined ranges)
      const cutoffDate = new Date(displayNow);
      cutoffDate.setDate(cutoffDate.getDate() - dateRange);
      
      filteredData = data.filter(d => d.timestamp > cutoffDate && d.timestamp <= displayNow);
    }
    
    return filteredData;
  };

  const fetchData = useCallback(async () => {
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
            .map(row => {
              const sourceTimestamp = new Date(row.Timestamp);
              const displayTimestamp = convertToTimezone(sourceTimestamp, sourceTimezone, selectedTimezone);
              
              // Fix: Use consistent timezone for both date and hour extraction
              // Don't use toISOString() as it converts back to UTC
              const year = displayTimestamp.getFullYear();
              const month = String(displayTimestamp.getMonth() + 1).padStart(2, '0');
              const day = String(displayTimestamp.getDate()).padStart(2, '0');
              const dateString = `${year}-${month}-${day}`;
              
              return {
                ...row,
                timestamp: displayTimestamp,
                hour: displayTimestamp.getHours(),
                date: dateString,
                dayOfWeek: displayTimestamp.toLocaleDateString('en-US', { weekday: 'long' })
              };
            })
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
  }, [selectedTimezone, sourceTimezone]);

  useEffect(() => {
    fetchData();
    // Refresh data every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Re-process data when timezone changes
  useEffect(() => {
    if (data.length > 0) {
      fetchData();
    }
  }, [data.length, fetchData]);

  // Update selectedYear when data changes
  useEffect(() => {
    if (data.length > 0) {
      const availableYears = getAvailableYears();
      // If current selectedYear is not in available years, select the most recent available year
      if (!availableYears.includes(selectedYear)) {
        setSelectedYear(availableYears[0]);
      }
    }
  }, [data, selectedYear, getAvailableYears]);

  const getHeatmapData = () => {
    const recentData = getFilteredData();
    
    // Helper function to create pivot table for a data source
    const createPivotData = (dataSource) => {
      const pivotData = {};
      recentData.forEach(row => {
        if (!pivotData[row.date]) {
          pivotData[row.date] = {};
        }
        if (!pivotData[row.date][row.hour]) {
          pivotData[row.date][row.hour] = [];
        }
        const value = dataSource === 'indoor' ? row.IndoorAirQuality : row.OutdoorAirQuality;
        if (value !== null && value !== undefined) {
          pivotData[row.date][row.hour].push(value);
        }
      });
      return pivotData;
    };

    // Create pivot tables for both indoor and outdoor
    const indoorPivotData = createPivotData('indoor');
    const outdoorPivotData = createPivotData('outdoor');
    
    // Calculate averages for both datasets
    const dates = Object.keys(indoorPivotData).sort();
    const hours = Array.from({length: 24}, (_, i) => i);
    const indoorZValues = [];
    const outdoorZValues = [];
    

    
    dates.forEach(date => {
      const indoorRow = [];
      const outdoorRow = [];
      hours.forEach(hour => {
        const indoorValues = indoorPivotData[date]?.[hour] || [];
        const outdoorValues = outdoorPivotData[date]?.[hour] || [];
        const indoorAvg = indoorValues.length > 0 ? indoorValues.reduce((a, b) => a + b) / indoorValues.length : null;
        const outdoorAvg = outdoorValues.length > 0 ? outdoorValues.reduce((a, b) => a + b) / outdoorValues.length : null;
        indoorRow.push(indoorAvg);
        outdoorRow.push(outdoorAvg);
      });
      indoorZValues.push(indoorRow);
      outdoorZValues.push(outdoorRow);
    });

    // Format y-axis labels based on date range - consistent timezone handling
    const yLabels = dates.map(date => {
      if (dateRange <= 14) {
        // For short periods, show just month and day
        // Parse the date in the display timezone to avoid UTC midnight issues
        const [year, month, day] = date.split('-').map(Number);
        const dateInDisplayTZ = new Date(year, month - 1, day); // month is 0-based
        return dateInDisplayTZ.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } else {
        // For longer periods, show full date
        return date;
      }
    });
    
    const commonConfig = {
      x: hours.map(h => `${h}:00`),
      y: yLabels,
      type: 'heatmap',
      colorscale: [
        [0, '#00E400'],      // Green (Good: 0-50)
        [0.1, '#00E400'],    // Green (50/500)
        [0.1, '#FFDC00'],    // Yellow (Moderate: 51-100)
        [0.2, '#FFDC00'],    // Yellow (100/500)
        [0.2, '#FF7E00'],    // Orange (Unhealthy for Sensitive: 101-150)
        [0.3, '#FF7E00'],    // Orange (150/500)
        [0.3, '#FF0000'],    // Red (Unhealthy: 151-200)
        [0.4, '#FF0000'],    // Red (200/500)
        [0.4, '#8F3F97'],    // Purple (Very Unhealthy: 201-300)
        [0.6, '#8F3F97'],    // Purple (300/500)
        [0.6, '#7E0023'],    // Maroon (Hazardous: 301-500)
        [1.0, '#7E0023']     // Maroon (500/500)
      ],
      zmin: 0,
      zmax: 500,
      showscale: false,
      hoverongaps: false
    };
    
    return [
      {
        ...commonConfig,
        z: indoorZValues,
        name: 'Indoor AQI',
        hovertemplate: 'Indoor<br>Date: %{y}<br>Hour: %{x}<br>AQI: %{z:.1f}<extra></extra>'
      },
      {
        ...commonConfig,
        z: outdoorZValues,
        name: 'Outdoor AQI',
        yaxis: 'y2',
        hovertemplate: 'Outdoor<br>Date: %{y}<br>Hour: %{x}<br>AQI: %{z:.1f}<extra></extra>'
      }
    ];
  };

  const getHourlyStats = () => {
    const recentData = getFilteredData();
    const indoorHourlyData = {};
    const outdoorHourlyData = {};
    
    recentData.forEach(row => {
      if (!indoorHourlyData[row.hour]) {
        indoorHourlyData[row.hour] = [];
        outdoorHourlyData[row.hour] = [];
      }
      indoorHourlyData[row.hour].push(row.IndoorAirQuality);
      outdoorHourlyData[row.hour].push(row.OutdoorAirQuality);
    });
    
    const hours = Array.from({length: 24}, (_, i) => i);
    const indoorStats = hours.map(hour => {
      const values = indoorHourlyData[hour] || [];
      return {
        hour,
        mean: values.length > 0 ? values.reduce((a, b) => a + b) / values.length : 0,
        max: values.length > 0 ? Math.max(...values) : 0,
        min: values.length > 0 ? Math.min(...values) : 0,
        count: values.length
      };
    });
    
    const outdoorStats = hours.map(hour => {
      const values = outdoorHourlyData[hour] || [];
      return {
        hour,
        mean: values.length > 0 ? values.reduce((a, b) => a + b) / values.length : 0,
        max: values.length > 0 ? Math.max(...values) : 0,
        min: values.length > 0 ? Math.min(...values) : 0,
        count: values.length
      };
    });
    
    return [
      {
        name: 'Indoor AQI',
        x: hours,
        y: indoorStats.map(s => s.mean),
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: 'red', width: 2 },
        marker: { 
          color: 'white',
          size: 8,
          line: { color: 'red', width: 2 }
        },
        hovertemplate: 'Hour: %{x}:00<br>Indoor AQI: %{y:.1f}<extra></extra>'
      },
      {
        name: 'Outdoor AQI',
        x: hours,
        y: outdoorStats.map(s => s.mean),
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: 'blue', width: 2 },
        marker: { 
          color: 'blue',
          size: 8
        },
        hovertemplate: 'Hour: %{x}:00<br>Outdoor AQI: %{y:.1f}<extra></extra>'
      }
    ];
  };

  const getTimeSeriesData = () => {
    const filteredData = getFilteredData();
    const recentData = filteredData.slice(-2000); // Last 2000 points from filtered data
    
    return [
      {
        x: recentData.map(d => d.timestamp),
        y: recentData.map(d => d.IndoorAirQuality),
        type: 'scatter',
        mode: 'lines',
        name: 'Indoor AQI',
        line: { color: 'red', width: 2 }
      },
      {
        x: recentData.map(d => d.timestamp),
        y: recentData.map(d => d.OutdoorAirQuality),
        type: 'scatter',
        mode: 'lines',
        name: 'Outdoor AQI',
        line: { color: 'blue', width: 1 }
      }
    ];
  };

  const getCorrelationData = () => {
    const filteredData = getFilteredData();
    return {
      x: filteredData.map(d => d.OutdoorAirQuality),
      y: filteredData.map(d => d.IndoorAirQuality),
      mode: 'markers',
      type: 'scatter',
      marker: {
        color: filteredData.map(d => getAQIColor(d.IndoorAirQuality)),
        size: 4,
        line: {
          color: 'rgba(0,0,0,0.3)',
          width: 1
        }
      },
      text: filteredData.map(d => `Hour: ${d.hour}:00<br>Indoor: ${d.IndoorAirQuality.toFixed(1)} AQI`),
      hovertemplate: 'Outdoor: %{x:.1f}<br>Indoor: %{y:.1f}<br>%{text}<extra></extra>'
    };
  };

  const getAnnualHeatmapData = (aggregation = 'average') => {
    // Helper function to create daily data for a data source
    const createDailyData = (dataSource) => {
      // Filter data to selected year only
      const yearData = data.filter(d => d.timestamp.getFullYear() === selectedYear);
      
      // Group data by date
      const dailyData = {};
      yearData.forEach(row => {
        const date = row.date; // Already in format YYYY-MM-DD
        if (!dailyData[date]) {
          dailyData[date] = [];
        }
        const value = dataSource === 'indoor' ? row.IndoorAirQuality : row.OutdoorAirQuality;
        if (value !== null && value !== undefined) {
          dailyData[date].push(value);
        }
      });
      
      // Calculate daily aggregations
      const dailyValues = {};
      Object.keys(dailyData).forEach(date => {
        const values = dailyData[date];
        if (values.length > 0) {
          dailyValues[date] = aggregation === 'average' 
            ? values.reduce((a, b) => a + b) / values.length
            : Math.max(...values);
        }
      });
      
      return dailyValues;
    };

    // Get current time in display timezone
    const now = new Date();
    const browserTZOffset = -now.getTimezoneOffset() / 60;
    let displayNow;
    
    if (browserTZOffset === selectedTimezone) {
      displayNow = now;
    } else {
      const offsetDiff = selectedTimezone - browserTZOffset;
      displayNow = new Date(now.getTime() + (offsetDiff * 60 * 60 * 1000));
    }
    
    // Create daily values for both indoor and outdoor
    const indoorDailyValues = createDailyData('indoor');
    const outdoorDailyValues = createDailyData('outdoor');
    
    // Create GitHub-style calendar for the selected year
    const yearStart = new Date(selectedYear, 0, 1);
    const firstSunday = new Date(yearStart);
    firstSunday.setDate(firstSunday.getDate() - firstSunday.getDay());
    
    let currentDate = new Date(firstSunday);
    const indoorHeatmapData = [];
    const outdoorHeatmapData = [];
    const indoorHeatmapText = [];
    const outdoorHeatmapText = [];
    const heatmapX = [];
    const heatmapY = [];
    
    // Generate 52 weeks × 7 days
    for (let week = 0; week < 52; week++) {
      for (let day = 0; day < 7; day++) {
        const dateStr = currentDate.toISOString().split('T')[0];
        const isTargetYear = currentDate.getFullYear() === selectedYear;
        const isFuture = selectedYear === displayNow.getFullYear() && currentDate > displayNow;
        
        heatmapX.push(week);
        heatmapY.push(day);
        
        if (isTargetYear && !isFuture) {
          const indoorValue = indoorDailyValues[dateStr];
          const outdoorValue = outdoorDailyValues[dateStr];
          
          indoorHeatmapData.push(indoorValue !== undefined ? indoorValue : null);
          outdoorHeatmapData.push(outdoorValue !== undefined ? outdoorValue : null);
          
          indoorHeatmapText.push(indoorValue !== undefined 
            ? `${dateStr}<br>Indoor AQI: ${indoorValue.toFixed(1)}` 
            : `${dateStr}<br>No indoor data`);
          outdoorHeatmapText.push(outdoorValue !== undefined 
            ? `${dateStr}<br>Outdoor AQI: ${outdoorValue.toFixed(1)}` 
            : `${dateStr}<br>No outdoor data`);
        } else {
          // No data for dates outside target year or future dates
          indoorHeatmapData.push(null);
          outdoorHeatmapData.push(null);
          indoorHeatmapText.push(`${dateStr}<br>No data`);
          outdoorHeatmapText.push(`${dateStr}<br>No data`);
        }
        
        currentDate.setDate(currentDate.getDate() + 1);
      }
    }
    
    const commonConfig = {
      x: heatmapX,
      y: heatmapY,
      hoverinfo: 'text',
      type: 'heatmap',
      colorscale: [
        [0, '#f0f0f0'],      // Light gray for no data
        [0.001, '#00E400'],  // Green (Good: 0-50)
        [0.1, '#00E400'],    // Green (50/500)
        [0.1, '#FFDC00'],    // Yellow (Moderate: 51-100)
        [0.2, '#FFDC00'],    // Yellow (100/500)
        [0.2, '#FF7E00'],    // Orange (Unhealthy for Sensitive: 101-150)
        [0.3, '#FF7E00'],    // Orange (150/500)
        [0.3, '#FF0000'],    // Red (Unhealthy: 151-200)
        [0.4, '#FF0000'],    // Red (200/500)
        [0.4, '#8F3F97'],    // Purple (Very Unhealthy: 201-300)
        [0.6, '#8F3F97'],    // Purple (300/500)
        [0.6, '#7E0023'],    // Maroon (Hazardous: 301-500)
        [1.0, '#7E0023']     // Maroon (500/500)
      ],
      zmin: 0,
      zmax: 500,
      showscale: false,
      xgap: 3,
      ygap: 3,
      hoverongaps: false
    };
    
    return [
      {
        ...commonConfig,
        z: indoorHeatmapData,
        text: indoorHeatmapText,
        name: 'Indoor AQI'
      },
      {
        ...commonConfig,
        z: outdoorHeatmapData,
        text: outdoorHeatmapText,
        name: 'Outdoor AQI',
        yaxis: 'y2'
      }
    ];
  };

  const calculatePatternSummary = () => {
    if (data.length === 0) return null;
    
    const recentData = getFilteredData();
    
    // Get indoor stats from the new getHourlyStats format
    const hourlyStats = getHourlyStats();
    const indoorStats = hourlyStats[0]; // Indoor AQI is first in the array
    
    // Find peak hour from indoor data
    const peakHour = indoorStats.x.reduce((peakIdx, hour, idx) => 
      indoorStats.y[idx] > indoorStats.y[peakIdx] ? idx : peakIdx
    , 0);
    
    const avgIndoor = recentData.reduce((sum, d) => sum + d.IndoorAirQuality, 0) / recentData.length;
    const avgOutdoor = recentData.reduce((sum, d) => sum + d.OutdoorAirQuality, 0) / recentData.length;
    
    return {
      peakHour: indoorStats.x[peakHour],
      peakValue: indoorStats.y[peakHour].toFixed(1),
      avgIndoor: avgIndoor.toFixed(1),
      avgOutdoor: avgOutdoor.toFixed(1),
      dataPoints: recentData.length
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

  return (
    <div className="App">
      <header>
        <div className="header-content">
          <div className="header-text">
            <h1>🏠 Air Quality Pattern Explorer</h1>
            <p>Analyzing {summary?.dataPoints.toLocaleString()} measurements from PurpleAir sensor ({getTimeRangeDescription()})</p>
            <p className="last-update">Last updated: {lastUpdate.toLocaleString()}</p>
          </div>
          <button onClick={fetchData} className="refresh-btn refresh-btn-header">
            🔄 Refresh
          </button>
        </div>
      </header>

      <div className="summary-cards">
        <div className="card">
          <h3>Peak Hour</h3>
          <div className="value">{summary?.peakHour}:00</div>
          <div className="label">{summary?.peakValue} AQI avg</div>
        </div>
        <div className="card">
          <h3>Indoor Average</h3>
          <div className={`value ${getAQIClass(parseFloat(summary?.avgIndoor || 0))}`}>{summary?.avgIndoor}</div>
          <div className="label">AQI</div>
        </div>
        <div className="card">
          <h3>Outdoor Average</h3>
          <div className={`value ${getAQIClass(parseFloat(summary?.avgOutdoor || 0))}`}>{summary?.avgOutdoor}</div>
          <div className="label">AQI</div>
        </div>
      </div>

      <div className="controls">
        <div className="view-selector">
          <button 
            className={selectedView === 'heatmap' ? 'active' : ''}
            onClick={() => setSelectedView('heatmap')}
          >
            Recent
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
            className={selectedView === 'annual-heatmap' ? 'active' : ''}
            onClick={() => setSelectedView('annual-heatmap')}
          >
            Annual
          </button>
        </div>
        
        {selectedView === 'heatmap' && (
          <div className="heatmap-controls">
            <div className="date-range">
              <label>Time frame: </label>
              <div className="time-range-toggle">
                <label>
                  <input 
                    type="radio" 
                    name="dateRangeMode" 
                    value="predefined" 
                    checked={dateRangeMode === 'predefined'} 
                    onChange={(e) => setDateRangeMode(e.target.value)} 
                  />
                  Predefined
                </label>
                <label>
                  <input 
                    type="radio" 
                    name="dateRangeMode" 
                    value="custom" 
                    checked={dateRangeMode === 'custom'} 
                    onChange={(e) => setDateRangeMode(e.target.value)} 
                  />
                  Custom
                </label>
              </div>
              {dateRangeMode === 'predefined' ? (
                <select value={timeRangeType === 'previous_year' ? 'previous_year' : dateRange} onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'previous_year') {
                    setTimeRangeType('previous_year');
                    setDateRange(365);
                  } else {
                    setTimeRangeType('recent');
                    setDateRange(Number(value));
                  }
                }}>
                  <option value={7}>Last 7 days</option>
                  <option value={14}>Last 14 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={60}>Last 60 days</option>
                  <option value={90}>Last 90 days</option>
                  <option value={180}>Last 6 months</option>
                  <option value={365}>Last 12 months</option>
                  <option value="previous_year">Previous year</option>
                </select>
              ) : (
                <div className="custom-date-range">
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    placeholder="Start date"
                  />
                  <span>to</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    placeholder="End date"
                  />
                </div>
              )}
            </div>

          </div>
        )}
        
        {selectedView === 'hourly' && (
          <div className="hourly-controls">
            <div className="date-range">
              <label>Time frame: </label>
              <div className="time-range-toggle">
                <label>
                  <input 
                    type="radio" 
                    name="dateRangeMode" 
                    value="predefined" 
                    checked={dateRangeMode === 'predefined'} 
                    onChange={(e) => setDateRangeMode(e.target.value)} 
                  />
                  Predefined
                </label>
                <label>
                  <input 
                    type="radio" 
                    name="dateRangeMode" 
                    value="custom" 
                    checked={dateRangeMode === 'custom'} 
                    onChange={(e) => setDateRangeMode(e.target.value)} 
                  />
                  Custom
                </label>
              </div>
              {dateRangeMode === 'predefined' ? (
                <select value={timeRangeType === 'previous_year' ? 'previous_year' : dateRange} onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'previous_year') {
                    setTimeRangeType('previous_year');
                    setDateRange(365);
                  } else {
                    setTimeRangeType('recent');
                    setDateRange(Number(value));
                  }
                }}>
                  <option value={7}>Last 7 days</option>
                  <option value={14}>Last 14 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={60}>Last 60 days</option>
                  <option value={90}>Last 90 days</option>
                  <option value={180}>Last 6 months</option>
                  <option value={365}>Last 12 months</option>
                  <option value="previous_year">Previous year</option>
                </select>
              ) : (
                <div className="custom-date-range">
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    placeholder="Start date"
                  />
                  <span>to</span>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    placeholder="End date"
                  />
                </div>
              )}
            </div>

          </div>
        )}
        
        {(selectedView === 'correlation' || selectedView === 'timeline') && (
          <div className="date-range">
            <label>Time frame: </label>
            <div className="time-range-toggle">
              <label>
                <input 
                  type="radio" 
                  name="dateRangeMode" 
                  value="predefined" 
                  checked={dateRangeMode === 'predefined'} 
                  onChange={(e) => setDateRangeMode(e.target.value)} 
                />
                Predefined
              </label>
              <label>
                <input 
                  type="radio" 
                  name="dateRangeMode" 
                  value="custom" 
                  checked={dateRangeMode === 'custom'} 
                  onChange={(e) => setDateRangeMode(e.target.value)} 
                />
                Custom
              </label>
            </div>
            {dateRangeMode === 'predefined' ? (
              <select value={timeRangeType === 'previous_year' ? 'previous_year' : dateRange} onChange={(e) => {
                const value = e.target.value;
                if (value === 'previous_year') {
                  setTimeRangeType('previous_year');
                  setDateRange(365);
                } else {
                  setTimeRangeType('recent');
                  setDateRange(Number(value));
                }
              }}>
                <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
                <option value={60}>Last 60 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last 12 months</option>
                <option value="previous_year">Previous year</option>
              </select>
            ) : (
              <div className="custom-date-range">
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  placeholder="Start date"
                />
                <span>to</span>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  placeholder="End date"
                />
              </div>
            )}
          </div>
        )}

        {selectedView === 'annual-heatmap' && (
          <div className="annual-heatmap-controls">

            <div className="year-selector">
              <label>Year: </label>
              <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
                {getAvailableYears().map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div className="aggregation-type">
              <label>Aggregation: </label>
              <select value={annualHeatmapAggregation} onChange={(e) => setAnnualHeatmapAggregation(e.target.value)}>
                <option value="average">Daily Average</option>
                <option value="max">Daily Maximum</option>
              </select>
            </div>
          </div>
        )}
        
        <div className="timezone-controls">
          <div className="timezone-row">
            <div className="timezone-selector">
              <label>Source:</label>
              <select 
                value={sourceTimezone} 
                onChange={(e) => setSourceTimezone(Number(e.target.value))}
              >
                {timezoneOptions.map(tz => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="timezone-selector">
              <label>Display:</label>
              <select 
                value={selectedTimezone} 
                onChange={(e) => setSelectedTimezone(Number(e.target.value))}
              >
                {timezoneOptions.map(tz => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="chart-container">
        {selectedView === 'heatmap' && data.length > 0 && (
          <div>
            <h2>Indoor & Outdoor AQI Levels by Hour - {getTimeRangeDescription()}</h2>
            
            {/* Manual color legend */}
            <div className="color-legend">
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#f0f0f0'}}></div>
                <span>No Data</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#00E400'}}></div>
                <span>Good (0-50)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FFDC00'}}></div>
                <span>Moderate (51-100)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF7E00'}}></div>
                <span>Sensitive (101-150)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
                <span>Unhealthy (151-200)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#8F3F97'}}></div>
                <span>Very Unhealthy (201-300)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#7E0023'}}></div>
                <span>Hazardous (301-500)</span>
              </div>
            </div>
            
            <Plot
              data={getHeatmapData()}
              layout={{
                xaxis: { 
                  title: 'Hour of Day', 
                  tickmode: window.innerWidth <= 768 ? 'array' : 'linear',
                  tickvals: window.innerWidth <= 768 ? [0, 6, 12, 18] : undefined,
                  ticktext: window.innerWidth <= 768 ? ['0:00', '6:00', '12:00', '18:00'] : undefined,
                  domain: [0, 1]
                },
                yaxis: { 
                  title: 'Indoor AQI', 
                  tickmode: 'auto', 
                  nticks: 10,
                  domain: [0.55, 1]
                },
                yaxis2: { 
                  title: 'Outdoor AQI', 
                  tickmode: 'auto', 
                  nticks: 10,
                  domain: [0, 0.45]
                },
                margin: { l: 100, r: 50, t: 50, b: 50 },
                annotations: [
                  {
                    text: 'Indoor AQI',
                    x: -0.1,
                    y: 0.775,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    textangle: -90,
                    font: { size: 14 },
                    showarrow: false
                  },
                  {
                    text: 'Outdoor AQI',
                    x: -0.1,
                    y: 0.225,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    textangle: -90,
                    font: { size: 14 },
                    showarrow: false
                  }
                ]
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '800px' }}
            />
          </div>
        )}

        {selectedView === 'hourly' && (
          <div>
            <h2>Indoor & Outdoor AQI Hourly Pattern Analysis - {getTimeRangeDescription()}</h2>
            <Plot
              data={getHourlyStats()}
              layout={{
                xaxis: { title: 'Hour of Day' },
                yaxis: { title: 'Average AQI' },
                showlegend: true,
                barmode: 'group'
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '500px' }}
            />
          </div>
        )}

        {selectedView === 'timeline' && (
          <div>
            <h2>Timeline - {getTimeRangeDescription()}</h2>
            <Plot
              data={getTimeSeriesData()}
              layout={{
                xaxis: { 
                  title: 'Time',
                  rangeslider: { visible: true }
                },
                yaxis: { title: 'AQI' },
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
            <h2>Indoor vs Outdoor Correlation - {getTimeRangeDescription()}</h2>
            <Plot
              data={[getCorrelationData()]}
              layout={{
                xaxis: { title: 'Outdoor AQI' },
                yaxis: { title: 'Indoor AQI' },
                showlegend: false
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '600px' }}
            />
          </div>
        )}

        {selectedView === 'annual-heatmap' && (
          <div>
            <h2>Indoor & Outdoor AQI Annual Calendar {selectedYear} - Daily {annualHeatmapAggregation === 'average' ? 'Average' : 'Maximum'}</h2>
            
            {/* Manual color legend */}
            <div className="color-legend">
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#f0f0f0'}}></div>
                <span>No Data</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#00E400'}}></div>
                <span>Good (0-50)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FFDC00'}}></div>
                <span>Moderate (51-100)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF7E00'}}></div>
                <span>Sensitive (101-150)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
                <span>Unhealthy (151-200)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#8F3F97'}}></div>
                <span>Very Unhealthy (201-300)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#7E0023'}}></div>
                <span>Hazardous (301-500)</span>
              </div>
            </div>
            
            <Plot
              data={getAnnualHeatmapData(annualHeatmapAggregation)}
              layout={{
                xaxis: { 
                  title: '',
                  showticklabels: true,
                  tickangle: 0,
                  tickmode: 'array',
                  tickvals: [0, 4, 13, 22, 30, 39, 48], // Approximate month starts
                  ticktext: ['Jan', 'Feb', 'Apr', 'Jun', 'Aug', 'Oct', 'Dec'],
                  showgrid: false,
                  zeroline: false,
                  side: 'top',
                  range: [-0.5, 51.5],
                  domain: [0, 1]
                },
                yaxis: { 
                  title: '',
                  tickmode: 'array',
                  tickvals: [0, 1, 2, 3, 4, 5, 6],
                  ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                  showgrid: false,
                  zeroline: false,
                  autorange: 'reversed',
                  side: 'left',
                  domain: [0.55, 1]
                },
                yaxis2: { 
                  title: '',
                  tickmode: 'array',
                  tickvals: [0, 1, 2, 3, 4, 5, 6],
                  ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                  showgrid: false,
                  zeroline: false,
                  autorange: 'reversed',
                  side: 'left',
                  domain: [0, 0.45]
                },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                margin: { l: 50, r: 20, t: 50, b: 20 },
                height: 400,
                annotations: [
                  {
                    text: 'Indoor AQI',
                    x: -0.1,
                    y: 0.775,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    textangle: -90,
                    font: { size: 14 },
                    showarrow: false
                  },
                  {
                    text: 'Outdoor AQI',
                    x: -0.1,
                    y: 0.225,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    textangle: -90,
                    font: { size: 14 },
                    showarrow: false
                  }
                ]
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