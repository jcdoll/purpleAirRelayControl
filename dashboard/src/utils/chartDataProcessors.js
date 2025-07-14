// Chart data processing functions extracted from App.js
import { getAQIColor } from './aqiUtils';
import { AQI_COLORS } from '../constants/app';

// Continuous colorscale from white through EPA colors
const generateColorscale = () => {
  return [
    [0, AQI_COLORS.CLEAR],   // Clear/White (AQI 0)
    [0.1, AQI_COLORS.GOOD],      // Green (AQI 50)
    [0.2, AQI_COLORS.MODERATE],  // Yellow (AQI 100)
    [0.3, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (AQI 150)
    [0.4, AQI_COLORS.UNHEALTHY], // Red (AQI 200)
    [0.6, AQI_COLORS.VERY_UNHEALTHY], // Purple (AQI 300)
    [1.0, AQI_COLORS.HAZARDOUS]  // Maroon (AQI 500+)
  ];
};

export const processHeatmapData = (filteredData, dateRange) => {
  // Helper function to create pivot table for a data source
  const createPivotData = (dataSource) => {
    const pivotData = {};
    filteredData.forEach(row => {
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
      [0, '#f0f0f0'],  // Gray for missing data (-1)
      [0.002, AQI_COLORS.CLEAR],   // Clear/White (AQI 0)
      [0.102, AQI_COLORS.GOOD],      // Green (AQI 50)
      [0.201, AQI_COLORS.MODERATE],  // Yellow (AQI 100)
      [0.301, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (AQI 150)
      [0.401, AQI_COLORS.UNHEALTHY], // Red (AQI 200)
      [0.601, AQI_COLORS.VERY_UNHEALTHY], // Purple (AQI 300)
      [1.0, AQI_COLORS.HAZARDOUS]  // Maroon (AQI 500+)
    ],
    zmin: -1,
    zmax: 500,
    showscale: false,
    hoverongaps: false
  };
  
  // Create custom hover text for missing data
  const indoorHoverText = indoorZValues.map((row, dateIndex) => 
    row.map((val, hourIndex) => {
      const date = yLabels[dateIndex];
      const hour = hours[hourIndex];
      if (val === null) {
        return `Indoor<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: No data`;
      }
      return `Indoor<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: ${val.toFixed(1)}`;
    })
  );

  const outdoorHoverText = outdoorZValues.map((row, dateIndex) => 
    row.map((val, hourIndex) => {
      const date = yLabels[dateIndex];
      const hour = hours[hourIndex];
      if (val === null) {
        return `Outdoor<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: No data`;
      }
      return `Outdoor<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: ${val.toFixed(1)}`;
    })
  );

  const indoorConfig = {
    ...commonConfig,
    z: indoorZValues.map(row => row.map(val => val === null ? -1 : val)),
    text: indoorHoverText,
    hoverinfo: 'text',
    name: 'Indoor AQI'
  };

  const outdoorConfig = {
    ...commonConfig,
    z: outdoorZValues.map(row => row.map(val => val === null ? -1 : val)),
    text: outdoorHoverText,
    hoverinfo: 'text',
    name: 'Outdoor AQI',
    xaxis: 'x2',
    yaxis: 'y2'
  };

  return [indoorConfig, outdoorConfig];
};

export const processHourlyStats = (filteredData) => {
  const indoorHourlyData = {};
  const outdoorHourlyData = {};
  
  filteredData.forEach(row => {
    if (!indoorHourlyData[row.hour]) {
      indoorHourlyData[row.hour] = [];
    }
    if (!outdoorHourlyData[row.hour]) {
      outdoorHourlyData[row.hour] = [];
    }
    
    if (row.IndoorAirQuality !== null && row.IndoorAirQuality !== undefined) {
      indoorHourlyData[row.hour].push(row.IndoorAirQuality);
    }
    if (row.OutdoorAirQuality !== null && row.OutdoorAirQuality !== undefined) {
      outdoorHourlyData[row.hour].push(row.OutdoorAirQuality);
    }
  });

  const indoorStats = [];
  const outdoorStats = [];
  
  for (let hour = 0; hour < 24; hour++) {
    const indoorValues = indoorHourlyData[hour] || [];
    const outdoorValues = outdoorHourlyData[hour] || [];
    
    const indoorAvg = indoorValues.length > 0 ? indoorValues.reduce((a, b) => a + b) / indoorValues.length : null;
    const outdoorAvg = outdoorValues.length > 0 ? outdoorValues.reduce((a, b) => a + b) / outdoorValues.length : null;
    
    indoorStats.push({
      hour: hour,
      average: indoorAvg,
      count: indoorValues.length
    });
    
    outdoorStats.push({
      hour: hour,
      average: outdoorAvg,
      count: outdoorValues.length
    });
  }

  const indoorData = {
    x: indoorStats.map(s => `${s.hour}:00`),
    y: indoorStats.map(s => s.average),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Indoor',
    line: { color: '#007bff' },
    marker: { color: '#007bff' },
    hovertemplate: 'Indoor<br>Hour: %{x}<br>Average AQI: %{y:.1f}<extra></extra>'
  };

  const outdoorData = {
    x: outdoorStats.map(s => `${s.hour}:00`),
    y: outdoorStats.map(s => s.average),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Outdoor',
    line: { color: '#ff6b6b' },
    marker: { color: '#ff6b6b' },
    hovertemplate: 'Outdoor<br>Hour: %{x}<br>Average AQI: %{y:.1f}<extra></extra>'
  };

  return [indoorData, outdoorData];
};

export const processTimeSeriesData = (filteredData) => {
  const timeSeriesData = filteredData.map(row => ({
    timestamp: new Date(row.timestamp),
    indoor: row.IndoorAirQuality,
    outdoor: row.OutdoorAirQuality
  }));

  const indoorData = {
    x: timeSeriesData.map(d => d.timestamp),
    y: timeSeriesData.map(d => d.indoor),
    type: 'scatter',
    mode: 'lines',
    name: 'Indoor',
    line: { color: '#007bff' },
    hovertemplate: 'Indoor<br>Time: %{x}<br>AQI: %{y:.1f}<extra></extra>'
  };

  const outdoorData = {
    x: timeSeriesData.map(d => d.timestamp),
    y: timeSeriesData.map(d => d.outdoor),
    type: 'scatter',
    mode: 'lines',
    name: 'Outdoor',
    line: { color: '#ff6b6b' },
    hovertemplate: 'Outdoor<br>Time: %{x}<br>AQI: %{y:.1f}<extra></extra>'
  };

  return [indoorData, outdoorData];
};

export const processCorrelationData = (filteredData) => {
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

export const processAnnualHeatmapData = (data, selectedYear, selectedTimezone, aggregation = 'average') => {
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
          : `${dateStr}<br>Indoor AQI: No data`);
        outdoorHeatmapText.push(outdoorValue !== undefined 
          ? `${dateStr}<br>Outdoor AQI: ${outdoorValue.toFixed(1)}` 
          : `${dateStr}<br>Outdoor AQI: No data`);
      } else {
        // No data for dates outside target year or future dates
        indoorHeatmapData.push(null);
        outdoorHeatmapData.push(null);
        indoorHeatmapText.push(`${dateStr}<br>Indoor AQI: No data`);
        outdoorHeatmapText.push(`${dateStr}<br>Outdoor AQI: No data`);
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
      [0, '#f0f0f0'],  // Gray for missing data (-1)
      [0.002, AQI_COLORS.CLEAR],   // Clear/White (AQI 0)
      [0.102, AQI_COLORS.GOOD],      // Green (AQI 50)
      [0.201, AQI_COLORS.MODERATE],  // Yellow (AQI 100)
      [0.301, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (AQI 150)
      [0.401, AQI_COLORS.UNHEALTHY], // Red (AQI 200)
      [0.601, AQI_COLORS.VERY_UNHEALTHY], // Purple (AQI 300)
      [1.0, AQI_COLORS.HAZARDOUS]  // Maroon (AQI 500+)
    ],
    zmin: -1,
    zmax: 500,
    showscale: false,
    xgap: 1,
    ygap: 1,
    hoverongaps: false,
    connectgaps: false
  };
  
  return [
    {
      ...commonConfig,
      z: indoorHeatmapData.map(val => val === null ? -1 : val),
      text: indoorHeatmapText,
      name: 'Indoor AQI'
    },
    {
      ...commonConfig,
      z: outdoorHeatmapData.map(val => val === null ? -1 : val),
      text: outdoorHeatmapText,
      name: 'Outdoor AQI',
      yaxis: 'y2',
      xaxis: 'x2'
    }
  ];
};

export const calculatePatternSummary = (data, filteredData) => {
  if (data.length === 0 || filteredData.length === 0) {
    return {
      peakHour: { hour: 'N/A', aqi: 'N/A' },
      indoorAvg: 'N/A',
      outdoorAvg: 'N/A'
    };
  }

  // Calculate peak hour based on filtered data
  const hourlyData = {};
  filteredData.forEach(row => {
    if (!hourlyData[row.hour]) {
      hourlyData[row.hour] = [];
    }
    // Use both indoor and outdoor values for peak calculation
    if (row.IndoorAirQuality !== null && row.IndoorAirQuality !== undefined) {
      hourlyData[row.hour].push(row.IndoorAirQuality);
    }
    if (row.OutdoorAirQuality !== null && row.OutdoorAirQuality !== undefined) {
      hourlyData[row.hour].push(row.OutdoorAirQuality);
    }
  });

  let peakHour = { hour: 'N/A', aqi: 'N/A' };
  let maxAqi = -1;
  
  Object.keys(hourlyData).forEach(hour => {
    const values = hourlyData[hour];
    if (values.length > 0) {
      const avgAqi = values.reduce((a, b) => a + b) / values.length;
      if (avgAqi > maxAqi) {
        maxAqi = avgAqi;
        peakHour = { hour: `${hour}:00`, aqi: avgAqi.toFixed(1) };
      }
    }
  });

  // Calculate indoor and outdoor averages
  const indoorValues = filteredData
    .filter(row => row.IndoorAirQuality !== null && row.IndoorAirQuality !== undefined)
    .map(row => row.IndoorAirQuality);
  
  const outdoorValues = filteredData
    .filter(row => row.OutdoorAirQuality !== null && row.OutdoorAirQuality !== undefined)
    .map(row => row.OutdoorAirQuality);

  const indoorAvg = indoorValues.length > 0 
    ? (indoorValues.reduce((a, b) => a + b) / indoorValues.length).toFixed(1)
    : 'N/A';
  
  const outdoorAvg = outdoorValues.length > 0 
    ? (outdoorValues.reduce((a, b) => a + b) / outdoorValues.length).toFixed(1)
    : 'N/A';

  return {
    peakHour,
    indoorAvg,
    outdoorAvg
  };
}; 