// Application Constants and Configuration

// Data Source
export const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRN0PHzfkvu7IMHEf2PG6_Ne4Vr-Pstsg0Sa8-WNBSy9a_-10Vvpr_jYGZxLszyMw8CybUq_7tDGkBq/pub?gid=394013654&single=true&output=csv';

// Application Info
export const GITHUB_URL = 'https://github.com/jcdoll/purpleAirRelayControl';

// Refresh Interval
export const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
export const REFRESH_MESSAGE = 'Data source: Google Sheets (auto-refreshes every 5 minutes)';

// AQI Colors
export const AQI_COLORS = {
  CLEAR: '#FFFFFF',                  // White (AQI 0)
  GOOD: '#00E400',                    // Green (0-50)
  MODERATE: '#FFDC00',               // Yellow (51-100)
  UNHEALTHY_SENSITIVE: '#FF7E00',    // Orange (101-150)
  UNHEALTHY: '#FF0000',              // Red (151-200)
  VERY_UNHEALTHY: '#8F3F97',         // Purple (201-300)
  HAZARDOUS: '#7E0023',              // Maroon (301-500)
  NO_DATA: '#f0f0f0'                 // Light gray for no data
};

// AQI Thresholds
export const AQI_THRESHOLDS = {
  GOOD: 50,
  MODERATE: 100,
  UNHEALTHY_SENSITIVE: 150,
  UNHEALTHY: 200,
  VERY_UNHEALTHY: 300
};

// AQI CSS Classes
export const AQI_CLASSES = {
  GOOD: 'aqi-good',
  MODERATE: 'aqi-moderate',
  UNHEALTHY_SENSITIVE: 'aqi-unhealthy-sensitive',
  UNHEALTHY: 'aqi-unhealthy',
  VERY_UNHEALTHY: 'aqi-very-unhealthy',
  HAZARDOUS: 'aqi-hazardous'
};

// Chart Heights
export const CHART_HEIGHTS = {
  HEATMAP: '800px',
  HOURLY: '400px',
  TIMELINE: '400px',
  CORRELATION: '400px',
  ANNUAL_HEATMAP: '300px'
};

// Chart Margins
export const CHART_MARGINS = {
  DEFAULT: { t: 50, r: 50, b: 50, l: 50 },
  HEATMAP: { t: 50, r: 50, b: 100, l: 100 },
  ANNUAL_HEATMAP: { t: 50, r: 20, b: 80, l: 50 }
};

// Data Processing
export const MAX_DATA_POINTS = 1000; // Limit for performance

// Date Range Options
export const DATE_RANGE_OPTIONS = [
  { value: 1, label: 'Last 24 hours' },
  { value: 3, label: 'Last 3 days' },
  { value: 7, label: 'Last 7 days' },
  { value: 14, label: 'Last 14 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
  { value: 180, label: 'Last 180 days' },
  { value: 365, label: 'Last 365 days' }
];

// View Types
export const VIEW_TYPES = {
  HEATMAP: 'heatmap',
  HOURLY: 'hourly',
  TIMELINE: 'timeline',
  CORRELATION: 'correlation',
  ANNUAL_HEATMAP: 'annual-heatmap'
};

// View Options
export const VIEW_OPTIONS = [
  { value: VIEW_TYPES.HEATMAP, label: 'Recent' },
  { value: VIEW_TYPES.HOURLY, label: 'Hourly Analysis' },
  { value: VIEW_TYPES.TIMELINE, label: 'Timeline' },
  { value: VIEW_TYPES.CORRELATION, label: 'Correlation' },
  { value: VIEW_TYPES.ANNUAL_HEATMAP, label: 'Annual' }
];

// Aggregation Options
export const AGGREGATION_OPTIONS = [
  { value: '95th', label: '95%' },
  { value: 'max', label: 'Maximum' },
  { value: 'average', label: 'Average' },
  { value: 'median', label: 'Median' }
];

// Summary Card Configuration
export const SUMMARY_CARD_CONFIG = {
  PEAK_HOUR: {
    title: 'PEAK HOUR',
    icon: '⏰',
    color: '#007bff'
  },
  INDOOR_AVG: {
    title: 'INDOOR AVERAGE',
    icon: '🏠',
    color: '#28a745'
  },
  OUTDOOR_AVG: {
    title: 'OUTDOOR AVERAGE',
    icon: '🌤️',
    color: '#ffc107'
  }
};

// Error Messages
export const ERROR_MESSAGES = {
  FETCH_ERROR: 'Failed to fetch data. Please check your internet connection.',
  PARSE_ERROR: 'Failed to parse data. Please check the data format.',
  NO_DATA: 'No data available for the selected time range.',
  INVALID_DATE: 'Invalid date range selected.'
};

// Loading Messages
export const LOADING_MESSAGES = {
  INITIAL: 'Loading air quality data...',
  REFRESH: 'Refreshing data...',
  PROCESSING: 'Processing data...'
};

// AQI Legend Items
export const AQI_LEGEND_ITEMS = [
  { color: '#f0f0f0', label: 'No Data' },
  { color: '#FFFFFF', label: 'Clear (=0)', border: '1px solid #ccc' },
  { color: '#00E400', label: 'Good (<50)' },
  { color: '#FFDC00', label: 'Moderate (<100)' },
  { color: '#FF7E00', label: 'Sensitive (<150)' },
  { color: '#FF0000', label: 'Unhealthy (<200)' },
  { color: '#8F3F97', label: 'Very Unhealthy (<300)' },
  { color: '#7E0023', label: 'Hazardous (>300)' }
];

// Chart Constants
export const CHART_CONSTANTS = {
  MAX_AQI: 300,
  MIN_AQI: 0,
  COLOR_STEPS: 60,
  WEEKS_PER_YEAR: 52,
  HOURS_PER_DAY: 24,
  DAYS_PER_WEEK: 7,
  HEATMAP_HEIGHT: 350,
  ANNUAL_HEATMAP_HEIGHT: 250,
  DEFAULT_CHART_HEIGHT: 400,
  TIMELINE_CHART_HEIGHT: 500
};

// Time Constants
export const TIME_CONSTANTS = {
  MS_PER_SECOND: 1000,
  MS_PER_MINUTE: 60 * 1000,
  MS_PER_HOUR: 60 * 60 * 1000,
  MS_PER_DAY: 24 * 60 * 60 * 1000
}; 