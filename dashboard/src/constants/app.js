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

// Animation Duration
export const ANIMATION_DURATION = 500;

// Data Processing
export const MAX_DATA_POINTS = 10000; // Limit for performance

// Timezone Options
export const TIMEZONE_OPTIONS = [
  { value: -11, label: 'UTC-11 (Hawaii)' },
  { value: -10, label: 'UTC-10 (Alaska)' },
  { value: -9, label: 'UTC-9 (Alaska)' },
  { value: -8, label: 'UTC-8 (Pacific)' },
  { value: -7, label: 'UTC-7 (Mountain/PDT)' },
  { value: -6, label: 'UTC-6 (Central/MDT)' },
  { value: -5, label: 'UTC-5 (Eastern/CDT)' },
  { value: -4, label: 'UTC-4 (Atlantic/EDT)' },
  { value: -3, label: 'UTC-3 (Argentina)' },
  { value: -2, label: 'UTC-2 (Mid-Atlantic)' },
  { value: -1, label: 'UTC-1 (Azores)' },
  { value: 0, label: 'UTC+0 (London)' },
  { value: 1, label: 'UTC+1 (Paris)' },
  { value: 2, label: 'UTC+2 (Cairo)' },
  { value: 3, label: 'UTC+3 (Moscow)' },
  { value: 4, label: 'UTC+4 (Dubai)' },
  { value: 5, label: 'UTC+5 (Karachi)' },
  { value: 5.5, label: 'UTC+5:30 (Mumbai)' },
  { value: 6, label: 'UTC+6 (Dhaka)' },
  { value: 7, label: 'UTC+7 (Bangkok)' },
  { value: 8, label: 'UTC+8 (Beijing)' },
  { value: 9, label: 'UTC+9 (Tokyo)' },
  { value: 10, label: 'UTC+10 (Sydney)' },
  { value: 11, label: 'UTC+11 (New Caledonia)' },
  { value: 12, label: 'UTC+12 (Auckland)' }
];

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

// View Options
export const VIEW_OPTIONS = [
  { value: 'heatmap', label: 'Recent' },
  { value: 'hourly', label: 'Hourly Analysis' },
  { value: 'timeline', label: 'Timeline' },
  { value: 'correlation', label: 'Correlation' },
  { value: 'annual-heatmap', label: 'Annual' }
];

// Aggregation Options
export const AGGREGATION_OPTIONS = [
  { value: 'average', label: 'Average' },
  { value: 'maximum', label: 'Maximum' }
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