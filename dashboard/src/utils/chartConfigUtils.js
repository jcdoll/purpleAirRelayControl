// Common ApexCharts configuration utilities - refactored to eliminate duplication
import { getAQIColor } from './aqiUtils';

export const CHART_COLORS = {
  indoor: '#007bff',
  outdoor: '#ff6b6b',
  primary: '#007bff',
  secondary: '#6c757d'
};

// Shared configuration constants
export const ANIMATION_DISABLED = {
  enabled: false,
  speed: 0,
  animateGradually: { enabled: false, delay: 0 },
  dynamicAnimation: { enabled: false, speed: 0 }
};

export const TOOLBAR_DISABLED = {
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
};

export const PERFORMANCE_OPTIMIZED_STATES = {
  hover: {
    filter: { type: 'none' }
  },
  active: {
    filter: { type: 'none' }
  }
};

export const PERFORMANCE_OPTIMIZED_CHART = {
  redrawOnParentResize: false,
  redrawOnWindowResize: false,
  sparkline: { enabled: false },
  group: undefined,
  offsetX: 0,
  offsetY: 0,
  fontFamily: 'inherit',
  foreColor: '#373d3f'
};

// Generate linearly interpolated color ranges for ApexCharts heatmaps
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
  
  ranges.unshift({ from: -1, to: -0.5, color: '#f0f0f0', name: 'No Data' });
  return ranges;
};

// Common chart options optimized for performance
export const getCommonChartOptions = (overrides = {}) => ({
  chart: {
    toolbar: TOOLBAR_DISABLED,
    animations: ANIMATION_DISABLED,
    ...PERFORMANCE_OPTIMIZED_CHART,
    ...overrides.chart
  },
  dataLabels: { enabled: false },
  grid: { 
    show: true, 
    strokeDashArray: 3, 
    borderColor: '#e0e0e0',
    ...overrides.grid
  },
  transitions: { enabled: false, speed: 0 },
  noData: {
    text: 'Loading...',
    align: 'center',
    verticalAlign: 'middle',
    style: { fontSize: '14px' }
  },
  ...overrides
});

// Common line chart options optimized for performance
export const getLineChartOptions = (overrides = {}) => {
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
      animations: ANIMATION_DISABLED,
      selection: { enabled: false },
      toolbar: defaultToolbar,
      ...overrides.chart
    },
    colors: [CHART_COLORS.indoor, CHART_COLORS.outdoor],
    stroke: { 
      curve: 'smooth', 
      width: 2,
      lineCap: 'round',
      dashArray: 0
    },
    legend: { 
      show: true, 
      position: 'top', 
      horizontalAlign: 'left', 
      offsetX: 40 
    },
    markers: {
      size: 0,
      strokeWidth: 0,
      hover: { size: 4, sizeOffset: 2 }
    },
    states: PERFORMANCE_OPTIMIZED_STATES,
    ...overrides
  };
};

// Recent heatmap options optimized for hour-based daily heatmaps
export const getRecentHeatmapOptions = (overrides = {}) => {
  const linearRanges = generateLinearColorRanges(0, 300, 60);
  const dateRange = overrides.dateRange || 7;
  
  return {
    ...getCommonChartOptions(overrides),
    chart: {
      type: 'heatmap',
      height: 350,
      toolbar: TOOLBAR_DISABLED,
      animations: ANIMATION_DISABLED,
      selection: { enabled: false },
      zoom: { enabled: false },
      pan: { enabled: false },
      dropShadow: { enabled: false },
      ...overrides.chart
    },
    plotOptions: {
      heatmap: {
        shadeIntensity: 0,
        radius: 0,
        useFillColorAsStroke: false,
        enableShades: false,
        hover: { sizeOffset: 0 },
        ...overrides.plotOptions?.heatmap,
        colorScale: { ranges: linearRanges }
      }
    },
    states: PERFORMANCE_OPTIMIZED_STATES,
    legend: { show: false },
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
      crosshairs: { show: false },
      ...overrides.xaxis
    },
    yaxis: { 
      title: { text: 'Date' },
      labels: {
        formatter: function(value, index) {
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

// Annual heatmap options optimized for week-based yearly heatmaps  
export const getAnnualHeatmapOptions = (overrides = {}) => {
  const linearRanges = generateLinearColorRanges(0, 300, 60);
  
  return {
    ...getCommonChartOptions(overrides),
    chart: {
      type: 'heatmap',
      height: 250,
      toolbar: TOOLBAR_DISABLED,
      animations: ANIMATION_DISABLED,
      zoom: { enabled: false },
      pan: { enabled: false },
      selection: { enabled: false },
      dropShadow: { enabled: false },
      ...overrides.chart
    },
    plotOptions: {
      heatmap: {
        radius: 1,
        useFillColorAsStroke: false,
        distributed: true,
        enableShades: false,
        shadeIntensity: 0,
        hover: { sizeOffset: 0 },
        ...overrides.plotOptions?.heatmap,
        colorScale: { ranges: linearRanges }
      }
    },
    states: PERFORMANCE_OPTIMIZED_STATES,
    legend: { show: false },
    dataLabels: { enabled: false },
    grid: {
      show: false,
      padding: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 20
      },
      ...overrides.grid
    },
    stroke: {
      show: true,
      width: 1,
      color: '#ffffff',
      ...overrides.stroke
    },
    xaxis: {
      type: 'numeric',
      position: 'bottom',
      min: 0,
      max: 51,
      tickAmount: 'dataPoints',
      labels: {
        show: true,
        rotate: 0,
        offsetY: 0,
        hideOverlappingLabels: false,
        showDuplicates: false
      },
      ...overrides.xaxis
    },
    yaxis: {
      reversed: true,
      labels: { 
        formatter: function(value) { 
          return value; 
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
    animations: ANIMATION_DISABLED,
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
      const dayIndex = seriesIndex;
      const weekNumber = dataPointIndex;
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