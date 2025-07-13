import React, { useState, useEffect } from 'react';
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
  const [heatmapDataSource, setHeatmapDataSource] = useState('indoor');
  const [annualDataSource, setAnnualDataSource] = useState('indoor');
  const [annualHeatmapDataSource, setAnnualHeatmapDataSource] = useState('indoor');
  const [annualHeatmapAggregation, setAnnualHeatmapAggregation] = useState('average');
  const [timeRangeType, setTimeRangeType] = useState('recent'); // 'recent' or 'previous_year'
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

  // Function to get AQI color based on PM2.5 value
  const getAQIColor = (pm25Value) => {
    if (pm25Value <= 12) return '#00E400';      // Green (Good)
    if (pm25Value <= 35.4) return '#FFDC00';   // Yellow (Moderate) - darker yellow
    if (pm25Value <= 55.4) return '#FF7E00';   // Orange (Unhealthy for Sensitive)
    if (pm25Value <= 150.4) return '#FF0000';  // Red (Unhealthy)
    if (pm25Value <= 250.4) return '#8F3F97';  // Purple (Very Unhealthy)
    return '#7E0023';                           // Maroon (Hazardous)
  };

  // Function to get AQI CSS class based on PM2.5 value
  const getAQIClass = (pm25Value) => {
    if (pm25Value <= 12) return 'aqi-good';
    if (pm25Value <= 35.4) return 'aqi-moderate';
    if (pm25Value <= 55.4) return 'aqi-unhealthy-sensitive';
    if (pm25Value <= 150.4) return 'aqi-unhealthy';
    if (pm25Value <= 250.4) return 'aqi-very-unhealthy';
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

  useEffect(() => {
    fetchData();
    // Refresh data every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Re-process data when timezone changes
  useEffect(() => {
    if (data.length > 0) {
      fetchData();
    }
  }, [selectedTimezone, sourceTimezone]);

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
  };

  const getHeatmapData = (dataSource = 'indoor') => {
    const recentData = getFilteredData();
    

    
    // Create pivot table
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
    
    return {
      z: zValues,
      x: hours.map(h => `${h}:00`),
      y: yLabels,
      type: 'heatmap',
      colorscale: [
        [0, '#00E400'],      // Green (Good: 0-12)
        [0.08, '#00E400'],   // Green
        [0.08, '#FFDC00'],   // Yellow (Moderate: 12.1-35.4)
        [0.24, '#FFDC00'],   // Yellow
        [0.24, '#FF7E00'],   // Orange (Unhealthy for Sensitive: 35.5-55.4)
        [0.37, '#FF7E00'],   // Orange
        [0.37, '#FF0000'],   // Red (Unhealthy: 55.5-150.4)
        [1.0, '#8F3F97']     // Purple (Very Unhealthy: 150.5+)
      ],
      zmin: 0,
      zmax: 150,
      colorbar: {
        title: 'PM2.5<br>(µg/m³)',
        titleside: 'right',
        tickvals: [0, 12, 35.4, 55.4, 150],
        ticktext: ['0<br>Good', '12<br>Moderate', '35.4<br>Sensitive', '55.4<br>Unhealthy', '150<br>Very Unhealthy']
      },
      hoverongaps: false,
      hovertemplate: 'Date: %{y}<br>Hour: %{x}<br>PM2.5: %{z:.1f} µg/m³<extra></extra>'
    };
  };

  const getHourlyStats = (timeFrameDays = 30) => {
    const recentData = getFilteredData();
    const hourlyData = {};
    
    recentData.forEach(row => {
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
    const filteredData = getFilteredData();
    const recentData = filteredData.slice(-2000); // Last 2000 points from filtered data
    
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
    const filteredData = getFilteredData();
    const dayData = {};
    const dayOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    filteredData.forEach(row => {
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
      text: filteredData.map(d => `Hour: ${d.hour}:00<br>Indoor: ${d.IndoorAirQuality.toFixed(1)} µg/m³`),
      hovertemplate: 'Outdoor: %{x:.1f}<br>Indoor: %{y:.1f}<br>%{text}<extra></extra>'
    };
  };

  const getAnnualHeatmapData = (dataSource = 'indoor', aggregation = 'average') => {
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
    
    // Get data for the current year
    const currentYear = displayNow.getFullYear();
    const yearStart = new Date(currentYear, 0, 1);
    const yearEnd = new Date(currentYear, 11, 31);
    
    // Filter data to current year
    const yearData = data.filter(d => {
      const dataYear = d.timestamp.getFullYear();
      return dataYear === currentYear;
    });
    
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
    
    // Create GitHub-style week grid (52 weeks x 7 days)
    // Find the Sunday before or on January 1st
    const firstSunday = new Date(yearStart);
    firstSunday.setDate(firstSunday.getDate() - firstSunday.getDay());
    
    // Create arrays for the full year grid
    const weekNumbers = [];
    const weekdays = [];
    const zValues = [];
    const hoverText = [];
    
    let currentDate = new Date(firstSunday);
    
    // Generate 52 weeks
    for (let week = 0; week < 52; week++) {
      // Generate 7 days for this week
      for (let day = 0; day < 7; day++) {
        const dateStr = currentDate.toISOString().split('T')[0];
        const isCurrentYear = currentDate.getFullYear() === currentYear;
        const isFuture = currentDate > displayNow;
        
        weekNumbers.push(week + 1);
        weekdays.push(day);
        
        if (isCurrentYear && !isFuture) {
          const value = dailyValues[dateStr];
          zValues.push(value !== undefined ? value : null);
          hoverText.push(value !== undefined ? `${dateStr}<br>PM2.5: ${value.toFixed(1)} µg/m³` : `${dateStr}<br>No data`);
        } else {
          // No data for dates outside current year or future dates
          zValues.push(null);
          hoverText.push(`${dateStr}<br>No data`);
        }
        
        currentDate.setDate(currentDate.getDate() + 1);
      }
    }
    
    return {
      x: weekNumbers,
      y: weekdays,
      z: zValues,
      text: hoverText,
      hoverinfo: 'text',
      type: 'heatmap',
      colorscale: [
        [0, '#00E400'],      // Green (Good: 0-12)
        [0.08, '#00E400'],   // Green
        [0.08, '#FFDC00'],   // Yellow (Moderate: 12.1-35.4)
        [0.24, '#FFDC00'],   // Yellow
        [0.24, '#FF7E00'],   // Orange (Unhealthy for Sensitive: 35.5-55.4)
        [0.37, '#FF7E00'],   // Orange
        [0.37, '#FF0000'],   // Red (Unhealthy: 55.5-150.4)
        [1.0, '#8F3F97']     // Purple (Very Unhealthy: 150.5+)
      ],
      zmin: 0,
      zmax: 150,
      showscale: false,
      xgap: 3,  // Gap between columns (weeks)
      ygap: 3,  // Gap between rows (days)
      hoverongaps: false
    };
  };

  const getAnnualComparisonData = (dataSource = 'indoor') => {
    // Group data by year and day of year
    const yearData = {};
    
    data.forEach(row => {
      const year = row.timestamp.getFullYear();
      const dayOfYear = Math.floor((row.timestamp - new Date(year, 0, 0)) / (1000 * 60 * 60 * 24));
      
      if (!yearData[year]) {
        yearData[year] = {};
      }
      if (!yearData[year][dayOfYear]) {
        yearData[year][dayOfYear] = [];
      }
      
      const value = dataSource === 'indoor' ? row.IndoorAirQuality : row.OutdoorAirQuality;
      if (value !== null && value !== undefined) {
        yearData[year][dayOfYear].push(value);
      }
    });
    
    // Create line plots for each year
    const years = Object.keys(yearData).sort().slice(-3); // Last 3 years
    const colors = ['#2196F3', '#FF7E00', '#00E400', '#FF0000', '#8F3F97'];
    
    return years.map((year, index) => {
      const days = Array.from({length: 365}, (_, i) => i + 1);
      const values = days.map(day => {
        const dayValues = yearData[year][day] || [];
        return dayValues.length > 0 ? dayValues.reduce((a, b) => a + b) / dayValues.length : null;
      });
      
      return {
        x: days,
        y: values,
        type: 'scatter',
        mode: 'lines',
        name: year,
        line: { 
          color: colors[index % colors.length], 
          width: 2 
        },
        connectgaps: true
      };
    });
  };

  const calculatePatternSummary = () => {
    if (data.length === 0) return null;
    
    const recentData = getFilteredData();
    
    const hourlyStats = getHourlyStats(dateRange);
    const peakHour = hourlyStats.reduce((prev, current) => 
      prev.mean > current.mean ? prev : current
    );
    
    const totalSpikes = recentData.filter(d => d.IndoorAirQuality > 50).length;
    const avgIndoor = recentData.reduce((sum, d) => sum + d.IndoorAirQuality, 0) / recentData.length;
    const avgOutdoor = recentData.reduce((sum, d) => sum + d.OutdoorAirQuality, 0) / recentData.length;
    
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
      dataPoints: recentData.length,
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
          <div className="label">{summary?.peakValue} µg/m³ avg</div>
        </div>
        <div className="card">
          <h3>Total Spikes</h3>
          <div className="value">{summary?.totalSpikes}</div>
          <div className="label">&gt;50 µg/m³</div>
        </div>
        <div className="card">
          <h3>Indoor Average</h3>
          <div className={`value ${getAQIClass(parseFloat(summary?.avgIndoor || 0))}`}>{summary?.avgIndoor}</div>
          <div className="label">µg/m³</div>
        </div>
        <div className="card">
          <h3>Outdoor Average</h3>
          <div className={`value ${getAQIClass(parseFloat(summary?.avgOutdoor || 0))}`}>{summary?.avgOutdoor}</div>
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
          <button 
            className={selectedView === 'annual' ? 'active' : ''}
            onClick={() => setSelectedView('annual')}
          >
            Annual Patterns
          </button>
          <button 
            className={selectedView === 'annual-heatmap' ? 'active' : ''}
            onClick={() => setSelectedView('annual-heatmap')}
          >
            Annual Heatmap
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
            <div className="data-source">
              <label>Data source: </label>
              <select value={heatmapDataSource} onChange={(e) => setHeatmapDataSource(e.target.value)}>
                <option value="indoor">Indoor PM2.5</option>
                <option value="outdoor">Outdoor PM2.5</option>
              </select>
            </div>
          </div>
        )}
        
        {selectedView === 'hourly' && (
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
        
        {(selectedView === 'correlation' || selectedView === 'timeline' || selectedView === 'dayofweek') && (
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

        {selectedView === 'annual' && (
          <div className="data-source">
            <label>Data source: </label>
            <select value={annualDataSource} onChange={(e) => setAnnualDataSource(e.target.value)}>
              <option value="indoor">Indoor PM2.5</option>
              <option value="outdoor">Outdoor PM2.5</option>
            </select>
          </div>
        )}

        {selectedView === 'annual-heatmap' && (
          <div className="annual-heatmap-controls">
            <div className="data-source">
              <label>Data source: </label>
              <select value={annualHeatmapDataSource} onChange={(e) => setAnnualHeatmapDataSource(e.target.value)}>
                <option value="indoor">Indoor PM2.5</option>
                <option value="outdoor">Outdoor PM2.5</option>
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
            <h2>{heatmapDataSource === 'indoor' ? 'Indoor' : 'Outdoor'} PM2.5 Levels by Hour - {getTimeRangeDescription()}</h2>
            <p className="subtitle">Look for vertical patterns (time-based) or horizontal patterns (day-specific)</p>
            <Plot
              data={[getHeatmapData(heatmapDataSource)]}
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
            <h2>Hourly Pattern Analysis - {getTimeRangeDescription()}</h2>
            <Plot
              data={[
                {
                  x: getHourlyStats(dateRange).map(h => `${h.hour}:00`),
                  y: getHourlyStats(dateRange).map(h => h.mean),
                  type: 'bar',
                  name: 'Average PM2.5',
                  marker: {
                    color: getHourlyStats(dateRange).map(h => getAQIColor(h.mean))
                  },
                  text: getHourlyStats(dateRange).map(h => `${h.mean.toFixed(1)} µg/m³`),
                  textposition: 'auto',
                },
                {
                  x: getHourlyStats(dateRange).map(h => `${h.hour}:00`),
                  y: getHourlyStats(dateRange).map(h => h.spikes),
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
            <h2>Timeline - {getTimeRangeDescription()}</h2>
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
            <h2>Indoor vs Outdoor Correlation - {getTimeRangeDescription()}</h2>
            <p className="subtitle">Colors represent indoor air quality levels - green (good) to red/purple (unhealthy)</p>
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
            <h2>Day of Week Patterns - {getTimeRangeDescription()}</h2>
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

        {selectedView === 'annual' && (
          <div>
            <h2>{annualDataSource === 'indoor' ? 'Indoor' : 'Outdoor'} PM2.5 Annual Comparison</h2>
            <p className="subtitle">Compare yearly patterns - each line represents a different year</p>
            <Plot
              data={getAnnualComparisonData(annualDataSource)}
              layout={{
                xaxis: { 
                  title: 'Day of Year',
                  tickmode: 'linear',
                  tick0: 1,
                  dtick: 30
                },
                yaxis: { title: 'Daily Average PM2.5 (µg/m³)' },
                showlegend: true,
                legend: { x: 0.02, y: 0.98 },
                hovermode: 'x unified'
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '600px' }}
            />
          </div>
        )}

        {selectedView === 'annual-heatmap' && (
          <div>
            <h2>{annualHeatmapDataSource === 'indoor' ? 'Indoor' : 'Outdoor'} PM2.5 Annual Calendar - {annualHeatmapAggregation === 'average' ? 'Daily Average' : 'Daily Maximum'}</h2>
            <p className="subtitle">Each square represents one day - colors follow PM2.5 air quality standards ({new Date().getFullYear()} year to date)</p>
            
            {/* Manual color legend */}
            <div className="color-legend">
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#00E400'}}></div>
                <span>Good (0-12)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FFDC00'}}></div>
                <span>Moderate (12-35)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF7E00'}}></div>
                <span>Sensitive (35-55)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
                <span>Unhealthy (55-150)</span>
              </div>
              <div className="legend-item">
                <div className="legend-color" style={{backgroundColor: '#8F3F97'}}></div>
                <span>Very Unhealthy (150+)</span>
              </div>
            </div>
            
            <Plot
              data={[getAnnualHeatmapData(annualHeatmapDataSource, annualHeatmapAggregation)]}
              layout={{
                xaxis: { 
                  title: '',
                  showticklabels: true,
                  tickangle: 0,
                  tickmode: 'array',
                  tickvals: [2, 6, 11, 15, 19, 24, 28, 33, 37, 41, 45, 50],
                  ticktext: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                  showgrid: false,
                  zeroline: false,
                  side: 'bottom',
                  range: [0.5, 52.5]
                },
                yaxis: { 
                  title: '',
                  tickmode: 'array',
                  tickvals: [0, 1, 2, 3, 4, 5, 6],
                  ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                  showgrid: false,
                  zeroline: false,
                  autorange: 'reversed'
                },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                margin: { l: 60, r: 20, t: 20, b: 60 },
                height: 200
              }}
              config={{ responsive: true }}
              style={{ width: '100%', height: '300px' }}
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