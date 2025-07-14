// Common ApexCharts configuration utilities
import { getAQIColor } from './aqiUtils';

export const CHART_COLORS = {
  indoor: '#007bff',
  outdoor: '#ff6b6b',
  primary: '#007bff',
  secondary: '#6c757d'
};

// Generate linearly interpolated color ranges for ApexCharts heatmaps
// This creates many small discrete color ranges that approximate continuous interpolation
// Example: generateLinearColorRanges(0, 300, 60) creates 60 color steps from AQI 0 to 300
// Each step uses the getAQIColor function to get the interpolated color for that AQI value
export const generateLinearColorRanges = (min = 0, max = 300, steps = 60) => {
  const ranges = [];
  
  for (let i = 0; i < steps; i++) {
    const from = min + (i * (max - min) / steps);
    const to = min + ((i + 1) * (max - min) / steps);
    const midpoint = (from + to) / 2;
    const color = getAQIColor(midpoint);
    
    ranges.push({
      from: from,
      to: to,
      color: color,
      name: `${Math.round(from)}-${Math.round(to)}`
    });
  }
  
  // Add special handling for no data and clear values
  ranges.unshift({ from: -1, to: -0.5, color: '#f0f0f0', name: 'No Data' });
  
  return ranges;
};

// AQI Color Scale for heatmaps (legacy discrete ranges - now replaced by linear interpolation)
export const AQI_COLOR_SCALE = {
  ranges: [
    { from: -1, to: -0.5, color: '#f0f0f0', name: 'No Data' },
    { from: 0, to: 0.1, color: '#FFFFFF', name: 'Clear' },
    { from: 0.1, to: 50, color: '#00E400', name: 'Good' },
    { from: 50, to: 100, color: '#FFDC00', name: 'Moderate' },
    { from: 100, to: 150, color: '#FF7E00', name: 'Sensitive' },
    { from: 150, to: 200, color: '#FF0000', name: 'Unhealthy' },
    { from: 200, to: 300, color: '#8F3F97', name: 'Very Unhealthy' },
    { from: 300, to: 500, color: '#7E0023', name: 'Hazardous' }
  ]
};

// Common chart options optimized for performance
export const getCommonChartOptions = (overrides = {}) => ({
  chart: {
    toolbar: { 
      show: false,
      tools: {
        download: false,
        selection: false,
        zoom: false,
        zoomin: false,
        zoomout: false,
        pan: false,
        reset: false
      }
    },
    animations: {
      enabled: false,  // Disable all animations for immediate display
      easing: 'linear',
      speed: 0,
      animateGradually: { 
        enabled: false,
        delay: 0 
      },
      dynamicAnimation: { 
        enabled: false,
        speed: 0 
      }
    },
    redrawOnParentResize: false,  // Disable automatic redraw for performance
    redrawOnWindowResize: false,  // Disable automatic redraw for performance
    // Performance optimizations
    sparkline: { enabled: false },
    group: undefined,
    offsetX: 0,
    offsetY: 0,
    fontFamily: 'inherit',
    foreColor: '#373d3f',
    ...overrides.chart
  },
  dataLabels: { enabled: false },
  grid: { 
    show: true, 
    strokeDashArray: 3, 
    borderColor: '#e0e0e0',
    ...overrides.grid
  },
  transitions: {
    enabled: false,
    speed: 0
  },
  // Additional performance settings
  noData: {
    text: 'Loading...',
    align: 'center',
    verticalAlign: 'middle',
    style: {
      fontSize: '14px'
    }
  },
  ...overrides
});

// Common line chart options optimized for performance
export const getLineChartOptions = (overrides = {}) => {
  // Default toolbar configuration for line charts - allows zoom but no download
  const defaultToolbar = {
    show: true,
    tools: {
      download: false,
      selection: true,
      zoom: true,
      zoomin: true,
      zoomout: true,
      pan: true,
      reset: true
    }
  };

  return {
    ...getCommonChartOptions(overrides),
    chart: {
      type: 'line',
      zoom: { enabled: true, type: 'x', autoScaleYaxis: true },
      animations: {
        enabled: false,
        speed: 0,
        animateGradually: { enabled: false },
        dynamicAnimation: { enabled: false }
      },
      // Line chart performance optimizations
      selection: { enabled: false },
      toolbar: defaultToolbar,
      ...overrides.chart
    },
  colors: [CHART_COLORS.indoor, CHART_COLORS.outdoor],
  stroke: { 
    curve: 'smooth', 
    width: 2,
    // Performance optimizations for stroke
    lineCap: 'round',
    dashArray: 0
  },
  legend: { 
    show: true, 
    position: 'top', 
    horizontalAlign: 'left', 
    offsetX: 40 
  },
  // Optimize markers for performance
  markers: {
    size: 0,  // Disable markers by default for better performance
    strokeWidth: 0,
    hover: {
      size: 4,
      sizeOffset: 2
    }
  },
  states: {
    hover: {
      filter: {
        type: 'none'  // Disable hover effects that cause layout changes
      }
    },
    active: {
      filter: {
        type: 'none'  // Disable active state effects
      }
    }
  },
  ...overrides
  };
};

// Common heatmap options optimized for performance
export const getHeatmapOptions = (overrides = {}) => {
  const linearRanges = generateLinearColorRanges(0, 300, 60);
  const dateRange = overrides.dateRange || 7; // Default to 7 days
  
  console.log('getHeatmapOptions called with overrides:', overrides);
  console.log('Generated linear ranges count:', linearRanges.length);
  
  return {
    ...getCommonChartOptions(overrides),
    chart: {
      type: 'heatmap',
      height: 350,
      toolbar: { 
        show: false,
        tools: {
          download: false,
          selection: false,
          zoom: false,
          zoomin: false,
          zoomout: false,
          pan: false,
          reset: false
        }
      },
      animations: {
        enabled: false,
        speed: 0,
        animateGradually: { enabled: false },
        dynamicAnimation: { enabled: false }
      },
      // Heatmap-specific performance optimizations
      selection: { enabled: false },
      zoom: { enabled: false },
      pan: { enabled: false },
      redrawOnWindowResize: false,
      redrawOnParentResize: false,
      dropShadow: {
        enabled: false  // Disable drop shadow to prevent hover shifts
      },
      ...overrides.chart
    },
    plotOptions: {
      heatmap: {
        shadeIntensity: 0,
        radius: 0,
        useFillColorAsStroke: false,
        enableShades: false,  // Disable shading since we're providing explicit color ranges
        hover: {
          sizeOffset: 0  // Prevent size changes on hover
        },
        ...overrides.plotOptions?.heatmap,
        // CRITICAL: Always preserve linear interpolation - must be AFTER overrides
        colorScale: {
          ranges: linearRanges
        }
      }
    },
    states: {
      hover: {
        filter: {
          type: 'none'  // Disable hover effects that cause layout changes
        }
      },
      active: {
        filter: {
          type: 'none'  // Disable active state effects
        }
      }
    },
    legend: {
      show: false  // Hide the generated legend, use custom ColorLegend component instead
    },
    xaxis: {
      type: 'category',
      title: { text: 'Hour of Day' },
      labels: {
        formatter: function(value) {
          if (window.innerWidth <= 768) {
            return ['0:00', '6:00', '12:00', '18:00'].includes(value) ? value : '';
          }
          return value;
        },
        trim: false,
        hideOverlappingLabels: false,
        showDuplicates: false
      },
      crosshairs: {
        show: false  // Disable crosshairs that cause gray x-axis highlight
      },
      ...overrides.xaxis
    },
    yaxis: { 
      title: { text: 'Date' },
      labels: {
        formatter: function(value, index) {
          // Dynamic date labeling based on date range
          const interval = Math.ceil(dateRange / 7);
          
          if (index % interval === 0) {
            return value;
          }
          return '';
        }
      },
      ...overrides.yaxis
    },
    ...overrides
  };
};

// Common scatter plot options
export const getScatterOptions = (overrides = {}) => ({
  ...getCommonChartOptions(overrides),
  chart: {
    type: 'scatter',
    zoom: { enabled: true, type: 'xy' },
    animations: {
      enabled: false,
      speed: 0,
      animateGradually: { enabled: false },
      dynamicAnimation: { enabled: false }
    },
    ...overrides.chart
  },
  colors: [CHART_COLORS.primary],
  markers: { 
    size: 4, 
    strokeWidth: 1, 
    strokeColors: ['rgba(0,0,0,0.3)'], 
    hover: { sizeOffset: 2 } 
  },
  ...overrides
});

// Common tooltip formatters
export const TOOLTIP_FORMATTERS = {
  aqi: (value) => value ? `${value.toFixed(1)} AQI` : 'No data',
  date: (value) => new Date(value).toLocaleDateString(),
  hour: (value) => `${value}:00`,
  datetime: 'dd MMM yyyy HH:mm'
};

// Custom tooltip generator for heatmap
export const createHeatmapTooltip = (type = 'Indoor') => ({
  custom: function({ series, seriesIndex, dataPointIndex, w }) {
    // For recent heatmap: seriesIndex = date, dataPointIndex = hour
    const formattedDate = w.globals.seriesNames[seriesIndex] || 'Unknown Date';
    const hour = w.globals.labels[dataPointIndex] || 'Unknown Hour';
    const value = series[seriesIndex][dataPointIndex];
    
    return `<div class="custom-tooltip">
      <strong>${formattedDate}</strong><br>
      Hour: ${hour}<br>
      ${type} AQI: ${value === -1 || value === null || value === undefined ? 'No data' : value.toFixed(1)}
    </div>`;
  }
});

// Custom tooltip generator for annual calendar heatmap
export const createAnnualHeatmapTooltip = (type = 'Indoor', selectedYear) => {
  // Helper to convert week number and day to actual date (reuses logic from processAnnualHeatmapData)
  const weekDayToDate = (week, day) => {
    const yearStart = new Date(selectedYear, 0, 1);
    const firstSunday = new Date(yearStart);
    firstSunday.setDate(firstSunday.getDate() - firstSunday.getDay());
    
    const date = new Date(firstSunday);
    date.setDate(date.getDate() + (week * 7 + day));
    return date;
  };

  return {
    custom: function({ series, seriesIndex, dataPointIndex, w }) {
      const dayIndex = seriesIndex; // 0-6 for Sun-Sat
      const weekNumber = dataPointIndex; // 0-51
      const value = series[seriesIndex][dataPointIndex];
      
      const actualDate = weekDayToDate(weekNumber, dayIndex);
      const formattedDate = actualDate.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
      
      return `<div class="custom-tooltip">
        <strong>${formattedDate}</strong><br>
        Week: ${weekNumber}<br>
        ${type} AQI: ${value === -1 || value === null || value === undefined ? 'No data' : value.toFixed(1)}
      </div>`;
    }
  };
};

// Common Y-axis configurations
export const getYAxisConfig = (title, overrides = {}) => ({
  title: { text: title },
  min: 0,
  labels: { 
    formatter: function(value) { 
      return value ? value.toFixed(0) : '0'; 
    } 
  },
  ...overrides
});

// Common X-axis configurations
export const getXAxisConfig = (title, type = 'category', overrides = {}) => ({
  type,
  title: { text: title },
  ...overrides
}); 