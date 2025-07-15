// Series creation utilities for ApexCharts - refactored to eliminate indoor/outdoor duplication
import { CHART_COLORS } from './chartConfigUtils';
import { CHART_CONSTANTS } from '../constants/app';

// Generic utilities
const isIndoorDataset = (datasetName) => {
  return datasetName.toLowerCase().includes('indoor');
};

const getDatasetColor = (datasetName) => {
  return isIndoorDataset(datasetName) ? CHART_COLORS.indoor : CHART_COLORS.outdoor;
};

// Generic series transformers
const createSingleHeatmapSeries = (sourceData, datasetName) => {
  return sourceData.y.map((date, dateIndex) => ({
    name: date,
    data: sourceData.x.map((hour, hourIndex) => ({
      x: hour,
      y: sourceData.z[dateIndex][hourIndex]
    }))
  }));
};

const createSingleAnnualHeatmapSeries = (sourceData) => {
  const weekLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const series = [];
  const allValues = [];
  
  for (let day = 0; day < CHART_CONSTANTS.DAYS_PER_WEEK; day++) {
    const dayData = [];
    for (let week = 0; week < CHART_CONSTANTS.WEEKS_PER_YEAR; week++) {
      const index = week * 7 + day;
      if (index < sourceData.z.length) {
        const value = sourceData.z[index];
        dayData.push({ 
          x: week, 
          y: value 
        });
        if (value !== null && value !== -1) allValues.push(value);
      }
    }
    series.push({ name: weekLabels[day], data: dayData });
  }
  
  
  return series;
};

const createSingleComparisonSeries = (trace, transformDataFn) => {
  const color = getDatasetColor(trace.name);
  
  return {
    name: trace.name,
    data: transformDataFn(trace),
    color
  };
};

// Main series creation functions using generic transformers
/**
 * Creates a line series for ApexCharts
 * @param {Object} data - Data object with x (timestamps) and y (values) arrays
 * @param {string} name - Series name for legend
 * @param {string} color - Optional color for the series
 * @returns {Object} ApexCharts series object
 */
export const createLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((timestamp, index) => ({
    x: new Date(timestamp).getTime(),
    y: data.y[index]
  })),
  color: color || CHART_COLORS.primary
});

/**
 * Creates an hourly line series for ApexCharts
 * @param {Object} data - Data object with x (hours) and y (values) arrays
 * @param {string} name - Series name for legend
 * @param {string} color - Optional color for the series
 * @returns {Object} ApexCharts series object
 */
export const createHourlyLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((hour, index) => ({ 
    x: hour, 
    y: data.y[index] 
  })),
  color: color || CHART_COLORS.primary
});

/**
 * Creates a scatter series for ApexCharts
 * @param {Object} data - Data object with x and y value arrays
 * @param {string} name - Series name for legend
 * @returns {Object} ApexCharts series object
 */
export const createScatterSeries = (data, name) => ({
  name,
  data: data.x.map((outdoor, index) => ({ 
    x: outdoor, 
    y: data.y[index] 
  }))
});

/**
 * Creates heatmap series for both indoor and outdoor data
 * @param {Array} data - Array of two data objects (indoor, outdoor) with x, y, z arrays
 * @returns {Object} Object with indoor and outdoor heatmap series
 */
export const createHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  
  return {
    indoor: createSingleHeatmapSeries(indoorData, 'Indoor'),
    outdoor: createSingleHeatmapSeries(outdoorData, 'Outdoor')
  };
};

/**
 * Creates annual heatmap series for both indoor and outdoor data
 * @param {Array} data - Array of two data objects (indoor, outdoor) with z arrays
 * @returns {Object} Object with indoor and outdoor annual heatmap series
 */
export const createAnnualHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  
  return {
    indoor: createSingleAnnualHeatmapSeries(indoorData),
    outdoor: createSingleAnnualHeatmapSeries(outdoorData)
  };
};

/**
 * Creates indoor/outdoor comparison series for time series charts
 * @param {Array} data - Array of data objects with name, x (timestamps), y (values) arrays
 * @returns {Array} Array of ApexCharts series objects with appropriate colors
 */
export const createIndoorOutdoorSeries = (data) => {
  return data.map(trace => createSingleComparisonSeries(trace, (trace) => 
    trace.x.map((timestamp, dataIndex) => ({
      x: new Date(timestamp).getTime(),
      y: trace.y[dataIndex]
    }))
  ));
};

/**
 * Creates hourly comparison series for indoor/outdoor data
 * @param {Array} data - Array of data objects with name, x (hours), y (values) arrays
 * @returns {Array} Array of ApexCharts series objects with appropriate colors
 */
export const createHourlyComparisonSeries = (data) => {
  return data.map(trace => createSingleComparisonSeries(trace, (trace) => 
    trace.x.map((hour, dataIndex) => ({ 
      x: hour, 
      y: trace.y[dataIndex] 
    }))
  ));
};

// Generic data transformation utilities
export const transformToApexFormat = (data, xMapper, yMapper) => {
  return data.map(item => ({
    x: xMapper(item),
    y: yMapper(item)
  }));
}; 