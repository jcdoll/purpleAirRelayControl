// Series creation utilities for ApexCharts - refactored to eliminate indoor/outdoor duplication
import { CHART_COLORS } from './chartConfigUtils';

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
  
  for (let day = 0; day < 7; day++) {
    const dayData = [];
    for (let week = 0; week < 52; week++) {
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
  
  console.log('Annual heatmap series values range:', {
    min: Math.min(...allValues),
    max: Math.max(...allValues),
    count: allValues.length,
    sample: allValues.slice(0, 10)
  });
  
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
export const createLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((timestamp, index) => ({
    x: new Date(timestamp).getTime(),
    y: data.y[index]
  })),
  color: color || CHART_COLORS.primary
});

export const createHourlyLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((hour, index) => ({ 
    x: hour, 
    y: data.y[index] 
  })),
  color: color || CHART_COLORS.primary
});

export const createScatterSeries = (data, name) => ({
  name,
  data: data.x.map((outdoor, index) => ({ 
    x: outdoor, 
    y: data.y[index] 
  }))
});

export const createHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  
  return {
    indoor: createSingleHeatmapSeries(indoorData, 'Indoor'),
    outdoor: createSingleHeatmapSeries(outdoorData, 'Outdoor')
  };
};

export const createAnnualHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  
  console.log('createAnnualHeatmapSeries called with:', { indoorData, outdoorData });
  
  return {
    indoor: createSingleAnnualHeatmapSeries(indoorData),
    outdoor: createSingleAnnualHeatmapSeries(outdoorData)
  };
};

export const createIndoorOutdoorSeries = (data) => {
  return data.map(trace => createSingleComparisonSeries(trace, (trace) => 
    trace.x.map((timestamp, dataIndex) => ({
      x: new Date(timestamp).getTime(),
      y: trace.y[dataIndex]
    }))
  ));
};

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

export const filterValidData = (data) => {
  return data.filter(item => 
    item.y !== null && 
    item.y !== undefined && 
    !isNaN(item.y)
  );
};

export const groupDataBy = (data, keyFunc) => {
  return data.reduce((groups, item) => {
    const key = keyFunc(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {});
};

export const calculateAverages = (groupedData) => {
  const result = {};
  Object.keys(groupedData).forEach(key => {
    const values = groupedData[key];
    if (values.length > 0) {
      const sum = values.reduce((acc, val) => acc + val, 0);
      result[key] = sum / values.length;
    }
  });
  return result;
}; 