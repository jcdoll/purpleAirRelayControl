// Chart data processing functions extracted from App.js

// Helper function to get AQI color based on AQI value
export const getAQIColor = (aqiValue) => {
  if (aqiValue <= 50) return '#00E400';       // Green (Good)
  if (aqiValue <= 100) return '#FFDC00';     // Yellow (Moderate)
  if (aqiValue <= 150) return '#FF7E00';     // Orange (Unhealthy for Sensitive)
  if (aqiValue <= 200) return '#FF0000';     // Red (Unhealthy)
  if (aqiValue <= 300) return '#8F3F97';     // Purple (Very Unhealthy)
  return '#7E0023';                           // Maroon (Hazardous)
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

export const processHourlyStats = (filteredData) => {
  const indoorHourlyData = {};
  const outdoorHourlyData = {};
  
  filteredData.forEach(row => {
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

export const processTimeSeriesData = (filteredData) => {
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

export const calculatePatternSummary = (data, filteredData) => {
  if (data.length === 0) return null;
  
  // Get indoor stats from the new processHourlyStats format
  const hourlyStats = processHourlyStats(filteredData);
  const indoorStats = hourlyStats[0]; // Indoor AQI is first in the array
  
  // Find peak hour from indoor data
  const peakHour = indoorStats.x.reduce((peakIdx, hour, idx) => 
    indoorStats.y[idx] > indoorStats.y[peakIdx] ? idx : peakIdx
  , 0);
  
  const avgIndoor = filteredData.reduce((sum, d) => sum + d.IndoorAirQuality, 0) / filteredData.length;
  const avgOutdoor = filteredData.reduce((sum, d) => sum + d.OutdoorAirQuality, 0) / filteredData.length;
  
  return {
    peakHour: indoorStats.x[peakHour],
    peakValue: indoorStats.y[peakHour].toFixed(1),
    avgIndoor: avgIndoor.toFixed(1),
    avgOutdoor: avgOutdoor.toFixed(1),
    dataPoints: filteredData.length
  };
}; 