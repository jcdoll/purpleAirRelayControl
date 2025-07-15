// Chart data processing functions - refactored to eliminate indoor/outdoor duplication
import { getAQIColor } from './aqiUtils';
import { isValidValue, calculateAverage, calculateMedian, calculate95thPercentile, formatHour, groupDataBy, formatTooltipValue } from './common';
import { CHART_CONSTANTS } from '../constants/app';

// Generic utilities for data processing

const getFieldName = (dataType) => {
  return dataType === 'indoor' ? 'IndoorAirQuality' : 'OutdoorAirQuality';
};

// Generic single-dataset processors
const processSingleHourlyDataset = (filteredData, dataType) => {
  const fieldName = getFieldName(dataType);
  
  const validData = filteredData.filter(row => isValidValue(row[fieldName]));
  const grouped = groupDataBy(validData, row => row.hour);
  
  // Transform grouped data to extract just the values
  const hourlyData = {};
  Object.entries(grouped).forEach(([hour, rows]) => {
    hourlyData[hour] = rows.map(row => row[fieldName]);
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
      return `${displayType}<br>Date: ${date}<br>Hour: ${formatHour(parseInt(hour))}<br>AQI: ${formatTooltipValue(val)}`;
    })
  );
};

// Main processing functions using the generic utilities
/**
 * Processes raw data into heatmap format for indoor/outdoor AQI visualization
 * @param {Object[]} filteredData - Array of data objects with timestamp, IndoorAirQuality, OutdoorAirQuality, hour, date fields
 * @param {number} dateRange - Number of days to display (used for label formatting)
 * @returns {Array} Array of two objects with x (hours), y (dates), z (AQI values) and text (tooltips) arrays
 */
export const processHeatmapData = (filteredData, dateRange) => {
  // Process both datasets in a single pass
  const pivotDatasets = {
    indoor: {},
    outdoor: {}
  };
  
  const dateSet = new Set();
  
  // Single pass through data to build both indoor and outdoor pivot structures
  filteredData.forEach(row => {
    // Process indoor data
    const indoorValue = row.IndoorAirQuality;
    if (isValidValue(indoorValue)) {
      if (!pivotDatasets.indoor[row.date]) {
        pivotDatasets.indoor[row.date] = {};
      }
      if (!pivotDatasets.indoor[row.date][row.hour]) {
        pivotDatasets.indoor[row.date][row.hour] = [];
      }
      pivotDatasets.indoor[row.date][row.hour].push(indoorValue);
      dateSet.add(row.date);
    }
    
    // Process outdoor data
    const outdoorValue = row.OutdoorAirQuality;
    if (isValidValue(outdoorValue)) {
      if (!pivotDatasets.outdoor[row.date]) {
        pivotDatasets.outdoor[row.date] = {};
      }
      if (!pivotDatasets.outdoor[row.date][row.hour]) {
        pivotDatasets.outdoor[row.date][row.hour] = [];
      }
      pivotDatasets.outdoor[row.date][row.hour].push(outdoorValue);
      dateSet.add(row.date);
    }
  });
  
  const validDates = Array.from(dateSet).sort();
  
  const hours = Array.from({length: CHART_CONSTANTS.HOURS_PER_DAY}, (_, i) => i);
  const datasets = {};
  
  // Process each dataset to create Z values
  const dataTypes = ['indoor', 'outdoor'];
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

/**
 * Processes data to calculate hourly statistics for comparison charts
 * @param {Object[]} filteredData - Array of data objects with timestamp, IndoorAirQuality, OutdoorAirQuality, hour fields
 * @returns {Array} Array of two objects with name, x (hours), y (average AQI values) arrays
 */
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

/**
 * Processes data for time series line charts
 * @param {Object[]} filteredData - Array of data objects with Timestamp, IndoorAirQuality, OutdoorAirQuality fields
 * @returns {Array} Array of two objects with name, x (timestamps), y (AQI values) arrays
 */
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

/**
 * Processes data for correlation scatter plot between indoor and outdoor AQI
 * @param {Object[]} filteredData - Array of data objects with IndoorAirQuality, OutdoorAirQuality fields
 * @returns {Object} Object with x (outdoor values) and y (indoor values) arrays
 */
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

/**
 * Processes data for annual heatmap visualization (GitHub-style calendar)
 * @param {Object[]} data - Array of all data objects with timestamp, IndoorAirQuality, OutdoorAirQuality fields
 * @param {number} selectedYear - Year to display data for
 * @param {string} aggregation - Aggregation method ('average', 'max', 'median', or '95th')
 * @returns {Array} Array of two objects with x (week numbers), y (day names), z (aggregated AQI values) arrays
 */
export const processAnnualHeatmapData = (data, selectedYear, aggregation = '95th') => {
  const dataTypes = ['indoor', 'outdoor'];
  const dailyDatasets = {};
  
  // Process both datasets
  dataTypes.forEach(dataType => {
    const dailyData = processSingleDailyDataset(data, selectedYear, dataType);
    const dailyValues = {};
    
    Object.keys(dailyData).forEach(date => {
      const values = dailyData[date];
      if (values.length > 0) {
        switch (aggregation) {
          case 'average':
            dailyValues[date] = calculateAverage(values);
            break;
          case 'median':
            dailyValues[date] = calculateMedian(values);
            break;
          case 'max':
            dailyValues[date] = Math.max(...values);
            break;
          case '95th':
          default:
            dailyValues[date] = calculate95thPercentile(values);
            break;
        }
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

/**
 * Calculates summary statistics and patterns from the data
 * @param {Object[]} data - Full dataset
 * @param {Object[]} filteredData - Filtered dataset for current view
 * @returns {Object} Summary object with peakHour, indoorAvg, outdoorAvg, and trend information
 */
export const calculatePatternSummary = (data, filteredData) => {
  if (data.length === 0 || filteredData.length === 0) {
    return {
      peakHour: { hour: 'N/A', aqi: 'N/A' },
      indoorAvg: 'N/A',
      outdoorAvg: 'N/A'
    };
  }

  // Calculate peak hour based on filtered data
  const hourlyData = groupDataBy(filteredData, row => row.hour);
  
  // Collect all AQI values (both indoor and outdoor) for each hour
  const hourlyAverages = {};
  Object.entries(hourlyData).forEach(([hour, rows]) => {
    const allValues = [];
    rows.forEach(row => {
      if (isValidValue(row.IndoorAirQuality)) allValues.push(row.IndoorAirQuality);
      if (isValidValue(row.OutdoorAirQuality)) allValues.push(row.OutdoorAirQuality);
    });
    if (allValues.length > 0) {
      hourlyAverages[hour] = calculateAverage(allValues);
    }
  });

  let peakHour = { hour: 'N/A', aqi: 'N/A' };
  let maxAqi = -1;
  
  Object.entries(hourlyAverages).forEach(([hour, avgAqi]) => {
    if (avgAqi > maxAqi) {
      maxAqi = avgAqi;
      peakHour = { hour: formatHour(parseInt(hour)), aqi: avgAqi.toFixed(1) };
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