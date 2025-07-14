// Chart data processing functions - refactored to eliminate indoor/outdoor duplication
import { getAQIColor } from './aqiUtils';

// Generic utilities for data processing
const isValidValue = (value) => value !== null && value !== undefined;

const calculateAverage = (values) => {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b) / values.length;
};

const getFieldName = (dataType) => {
  return dataType === 'indoor' ? 'IndoorAirQuality' : 'OutdoorAirQuality';
};

// Generic single-dataset processors
const processSingleHeatmapDataset = (filteredData, dataType) => {
  const fieldName = getFieldName(dataType);
  const pivotData = {};
  
  filteredData.forEach(row => {
    if (!pivotData[row.date]) {
      pivotData[row.date] = {};
    }
    if (!pivotData[row.date][row.hour]) {
      pivotData[row.date][row.hour] = [];
    }
    const value = row[fieldName];
    if (isValidValue(value)) {
      pivotData[row.date][row.hour].push(value);
    }
  });
  
  return pivotData;
};

const processSingleHourlyDataset = (filteredData, dataType) => {
  const fieldName = getFieldName(dataType);
  const hourlyData = {};
  
  filteredData.forEach(row => {
    if (!hourlyData[row.hour]) {
      hourlyData[row.hour] = [];
    }
    const value = row[fieldName];
    if (isValidValue(value)) {
      hourlyData[row.hour].push(value);
    }
  });
  
  return hourlyData;
};

const processSingleDailyDataset = (data, selectedYear, dataType) => {
  const fieldName = getFieldName(dataType);
  const yearData = data.filter(d => d.timestamp.getFullYear() === selectedYear);
  
  const dailyData = {};
  yearData.forEach(row => {
    const date = row.date;
    if (!dailyData[date]) {
      dailyData[date] = [];
    }
    const value = row[fieldName];
    if (isValidValue(value)) {
      dailyData[date].push(value);
    }
  });
  
  return dailyData;
};

const createHoverText = (values, labels, dataType, hours) => {
  return values.map((row, dateIndex) => 
    row.map((val, hourIndex) => {
      const date = labels[dateIndex];
      const hour = hours[hourIndex];
      const displayType = dataType === 'indoor' ? 'Indoor' : 'Outdoor';
      if (val === null) {
        return `${displayType}<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: No data`;
      }
      return `${displayType}<br>Date: ${date}<br>Hour: ${hour}:00<br>AQI: ${val.toFixed(1)}`;
    })
  );
};

// Main processing functions using the generic utilities
export const processHeatmapData = (filteredData, dateRange) => {
  const dataTypes = ['indoor', 'outdoor'];
  const pivotDatasets = {};
  
  // Process both datasets using the generic processor
  dataTypes.forEach(dataType => {
    pivotDatasets[dataType] = processSingleHeatmapDataset(filteredData, dataType);
  });
  
  // Find valid dates that have data for either dataset
  const allDates = new Set([
    ...Object.keys(pivotDatasets.indoor), 
    ...Object.keys(pivotDatasets.outdoor)
  ]);
  
  const validDates = Array.from(allDates).filter(date => {
    const hasIndoorData = Object.values(pivotDatasets.indoor[date] || {}).some(values => values.length > 0);
    const hasOutdoorData = Object.values(pivotDatasets.outdoor[date] || {}).some(values => values.length > 0);
    return hasIndoorData || hasOutdoorData;
  }).sort();
  
  const hours = Array.from({length: 24}, (_, i) => i);
  const datasets = {};
  
  // Process each dataset to create Z values
  dataTypes.forEach(dataType => {
    datasets[dataType] = [];
    validDates.forEach(date => {
      const row = [];
      hours.forEach(hour => {
        const values = pivotDatasets[dataType][date]?.[hour] || [];
        const avg = calculateAverage(values);
        row.push(avg);
      });
      datasets[dataType].push(row);
    });
  });

  // Format y-axis labels
  const yLabels = validDates.map(date => {
    const [year, month, day] = date.split('-').map(Number);
    const dateObj = new Date(year, month - 1, day);
    return dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const commonConfig = {
    x: hours.map(h => `${h}:00`),
    y: yLabels,
    type: 'heatmap',
    zmin: -1,
    zmax: 500,
    showscale: false,
    hoverongaps: false
  };
  
  // Create configurations for both datasets
  const configs = dataTypes.map((dataType, index) => ({
    ...commonConfig,
    z: datasets[dataType].map(row => row.map(val => val === null ? -1 : val)),
    text: createHoverText(datasets[dataType], yLabels, dataType, hours),
    hoverinfo: 'text',
    name: `${dataType === 'indoor' ? 'Indoor' : 'Outdoor'} AQI`,
    ...(index === 1 && { xaxis: 'x2', yaxis: 'y2' })
  }));

  return configs;
};

export const processHourlyStats = (filteredData) => {
  const dataTypes = ['indoor', 'outdoor'];
  const results = [];
  
  dataTypes.forEach(dataType => {
    const hourlyData = processSingleHourlyDataset(filteredData, dataType);
    const stats = [];
    
    for (let hour = 0; hour < 24; hour++) {
      const values = hourlyData[hour] || [];
      const average = calculateAverage(values);
      stats.push({
        hour: hour,
        average: average,
        count: values.length
      });
    }
    
    const displayType = dataType === 'indoor' ? 'Indoor' : 'Outdoor';
    const color = dataType === 'indoor' ? '#007bff' : '#ff6b6b';
    
    results.push({
      x: stats.map(s => `${s.hour}:00`),
      y: stats.map(s => s.average),
      type: 'scatter',
      mode: 'lines+markers',
      name: displayType,
      line: { color },
      marker: { color },
      hovertemplate: `${displayType}<br>Hour: %{x}<br>Average AQI: %{y:.1f}<extra></extra>`
    });
  });

  return results;
};

export const processTimeSeriesData = (filteredData) => {
  const dataTypes = ['indoor', 'outdoor'];
  const results = [];
  
  dataTypes.forEach(dataType => {
    const fieldName = getFieldName(dataType);
    const displayType = dataType === 'indoor' ? 'Indoor' : 'Outdoor';
    const color = dataType === 'indoor' ? '#007bff' : '#ff6b6b';
    
    results.push({
      x: filteredData.map(row => row.timestamp),
      y: filteredData.map(row => row[fieldName]),
      type: 'scatter',
      mode: 'lines',
      name: displayType,
      line: { color },
      hovertemplate: `${displayType}<br>Time: %{x}<br>AQI: %{y:.1f}<extra></extra>`
    });
  });

  return results;
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

export const processAnnualHeatmapData = (data, selectedYear, aggregation = 'average') => {
  const dataTypes = ['indoor', 'outdoor'];
  const dailyDatasets = {};
  
  // Process both datasets
  dataTypes.forEach(dataType => {
    const dailyData = processSingleDailyDataset(data, selectedYear, dataType);
    const dailyValues = {};
    
    Object.keys(dailyData).forEach(date => {
      const values = dailyData[date];
      if (values.length > 0) {
        dailyValues[date] = aggregation === 'average' 
          ? calculateAverage(values)
          : Math.max(...values);
      }
    });
    
    dailyDatasets[dataType] = dailyValues;
  });
  
  // Generate calendar data
  const yearStart = new Date(selectedYear, 0, 1);
  const firstSunday = new Date(yearStart);
  firstSunday.setDate(firstSunday.getDate() - firstSunday.getDay());
  
  let currentDate = new Date(firstSunday);
  const results = dataTypes.map(dataType => ({
    heatmapData: [],
    heatmapText: []
  }));
  
  const heatmapX = [];
  const heatmapY = [];
  
  for (let week = 0; week < 52; week++) {
    for (let day = 0; day < 7; day++) {
      const dateStr = currentDate.toISOString().split('T')[0];
      const isTargetYear = currentDate.getFullYear() === selectedYear;
      const isFuture = selectedYear === new Date().getFullYear() && currentDate > new Date();
      
      heatmapX.push(week);
      heatmapY.push(day);
      
      dataTypes.forEach((dataType, index) => {
        const displayType = dataType === 'indoor' ? 'Indoor' : 'Outdoor';
        
        if (isTargetYear && !isFuture) {
          const value = dailyDatasets[dataType][dateStr];
          results[index].heatmapData.push(value !== undefined ? value : -1);
          results[index].heatmapText.push(value !== undefined 
            ? `${dateStr}<br>${displayType} AQI: ${value.toFixed(1)}` 
            : `${dateStr}<br>${displayType} AQI: No data`);
        } else {
          results[index].heatmapData.push(-1);
          results[index].heatmapText.push(`${dateStr}<br>${displayType} AQI: No data`);
        }
      });
      
      currentDate.setDate(currentDate.getDate() + 1);
    }
  }

  const commonConfig = {
    x: heatmapX,
    y: heatmapY,
    hoverinfo: 'text',
    type: 'heatmap',
    zmin: -1,
    zmax: 500,
    showscale: false,
    xgap: 1,
    ygap: 1,
    hoverongaps: false,
    connectgaps: false
  };
  
  return dataTypes.map((dataType, index) => ({
    ...commonConfig,
    z: results[index].heatmapData,
    text: results[index].heatmapText,
    name: `${dataType === 'indoor' ? 'Indoor' : 'Outdoor'} AQI`,
    ...(index === 1 && { yaxis: 'y2', xaxis: 'x2' })
  }));
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
    if (isValidValue(row.IndoorAirQuality)) {
      hourlyData[row.hour].push(row.IndoorAirQuality);
    }
    if (isValidValue(row.OutdoorAirQuality)) {
      hourlyData[row.hour].push(row.OutdoorAirQuality);
    }
  });

  let peakHour = { hour: 'N/A', aqi: 'N/A' };
  let maxAqi = -1;
  
  Object.keys(hourlyData).forEach(hour => {
    const values = hourlyData[hour];
    if (values.length > 0) {
      const avgAqi = calculateAverage(values);
      if (avgAqi > maxAqi) {
        maxAqi = avgAqi;
        peakHour = { hour: `${hour}:00`, aqi: avgAqi.toFixed(1) };
      }
    }
  });

  // Calculate averages for both datasets using generic approach
  const getAverage = (dataType) => {
    const fieldName = getFieldName(dataType);
    const values = filteredData
      .filter(row => isValidValue(row[fieldName]))
      .map(row => row[fieldName]);
    
    return values.length > 0 ? calculateAverage(values).toFixed(1) : 'N/A';
  };

  return {
    peakHour,
    indoorAvg: getAverage('indoor'),
    outdoorAvg: getAverage('outdoor')
  };
}; 