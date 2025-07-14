// Series creation utilities for ApexCharts
import { CHART_COLORS } from './chartConfigUtils';

// Create line series data from time series data
export const createLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((timestamp, index) => ({
    x: new Date(timestamp).getTime(),
    y: data.y[index]
  })),
  color: color || CHART_COLORS.primary
});

// Create line series for hourly data
export const createHourlyLineSeries = (data, name, color) => ({
  name,
  data: data.x.map((hour, index) => ({ 
    x: hour, 
    y: data.y[index] 
  })),
  color: color || CHART_COLORS.primary
});

// Create scatter series data
export const createScatterSeries = (data, name) => ({
  name,
  data: data.x.map((outdoor, index) => ({ 
    x: outdoor, 
    y: data.y[index] 
  }))
});

// Create heatmap series from processed data
export const createHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  
  const createSeries = (sourceData, name) => {
    return sourceData.y.map((date, dateIndex) => ({
      name: date,
      data: sourceData.x.map((hour, hourIndex) => ({
        x: hour,
        y: sourceData.z[dateIndex][hourIndex]
      }))
    }));
  };

  return {
    indoor: createSeries(indoorData, 'Indoor'),
    outdoor: createSeries(outdoorData, 'Outdoor')
  };
};

// Create annual heatmap series
export const createAnnualHeatmapSeries = (data) => {
  const [indoorData, outdoorData] = data;
  const weekLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  
  console.log('createAnnualHeatmapSeries called with:', { indoorData, outdoorData });
  
  const createSeries = (sourceData) => {
    const series = [];
    const allValues = [];
    
    for (let day = 0; day < 7; day++) {
      const dayData = [];
      for (let week = 0; week < 52; week++) {
        const index = week * 7 + day;
        if (index < sourceData.z.length) {
          // Keep -1 values as -1 for proper color scale handling (gray color)
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

  return {
    indoor: createSeries(indoorData),
    outdoor: createSeries(outdoorData)
  };
};

// Create multiple line series for indoor/outdoor comparison
export const createIndoorOutdoorSeries = (data) => {
  return data.map((trace, index) => {
    const isIndoor = trace.name.toLowerCase().includes('indoor');
    const color = isIndoor ? CHART_COLORS.indoor : CHART_COLORS.outdoor;
    
    return {
      name: trace.name,
      data: trace.x.map((timestamp, dataIndex) => ({
        x: new Date(timestamp).getTime(),
        y: trace.y[dataIndex]
      })),
      color
    };
  });
};

// Create hourly comparison series
export const createHourlyComparisonSeries = (data) => {
  return data.map((trace, index) => {
    const isIndoor = trace.name.toLowerCase().includes('indoor');
    const color = isIndoor ? CHART_COLORS.indoor : CHART_COLORS.outdoor;
    
    return {
      name: trace.name,
      data: trace.x.map((hour, dataIndex) => ({ 
        x: hour, 
        y: trace.y[dataIndex] 
      })),
      color
    };
  });
};

// Generic data transformation utilities
export const transformToApexFormat = (data, xMapper, yMapper) => {
  return data.map(item => ({
    x: xMapper(item),
    y: yMapper(item)
  }));
};

// Filter out null/undefined values
export const filterValidData = (data) => {
  return data.filter(item => 
    item.y !== null && 
    item.y !== undefined && 
    !isNaN(item.y)
  );
};

// Group data by a key function
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

// Calculate averages for grouped data
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