// Application Constants and Configuration

// Data Source
export const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRN0PHzfkvu7IMHEf2PG6_Ne4Vr-Pstsg0Sa8-WNBSy9a_-10Vvpr_jYGZxLszyMw8CybUq_7tDGkBq/pub?gid=394013654&single=true&output=csv';

// Refresh Interval
export const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

// AQI Colors
export const AQI_COLORS = {
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
  TIMELINE: '500px',
  HOURLY: '500px',
  CORRELATION: '600px',
  ANNUAL: '500px'
};

// Chart Color Scale for Plotly
export const CHART_COLOR_SCALE = [
  [0, AQI_COLORS.GOOD],               // Green (Good: 0-50)
  [0.1, AQI_COLORS.GOOD],             // Green (50/500)
  [0.1, AQI_COLORS.MODERATE],         // Yellow (Moderate: 51-100)
  [0.2, AQI_COLORS.MODERATE],         // Yellow (100/500)
  [0.2, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (Unhealthy for Sensitive: 101-150)
  [0.3, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (150/500)
  [0.3, AQI_COLORS.UNHEALTHY],        // Red (Unhealthy: 151-200)
  [0.4, AQI_COLORS.UNHEALTHY],        // Red (200/500)
  [0.4, AQI_COLORS.VERY_UNHEALTHY],   // Purple (Very Unhealthy: 201-300)
  [0.6, AQI_COLORS.VERY_UNHEALTHY],   // Purple (300/500)
  [0.6, AQI_COLORS.HAZARDOUS],        // Maroon (Hazardous: 301-500)
  [1.0, AQI_COLORS.HAZARDOUS]         // Maroon (500/500)
];

// Annual Chart Color Scale (includes no data)
export const ANNUAL_CHART_COLOR_SCALE = [
  [0, AQI_COLORS.NO_DATA],            // Light gray for no data
  [0.001, AQI_COLORS.GOOD],           // Green (Good: 0-50)
  [0.1, AQI_COLORS.GOOD],             // Green (50/500)
  [0.1, AQI_COLORS.MODERATE],         // Yellow (Moderate: 51-100)
  [0.2, AQI_COLORS.MODERATE],         // Yellow (100/500)
  [0.2, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (Unhealthy for Sensitive: 101-150)
  [0.3, AQI_COLORS.UNHEALTHY_SENSITIVE], // Orange (150/500)
  [0.3, AQI_COLORS.UNHEALTHY],        // Red (Unhealthy: 151-200)
  [0.4, AQI_COLORS.UNHEALTHY],        // Red (200/500)
  [0.4, AQI_COLORS.VERY_UNHEALTHY],   // Purple (Very Unhealthy: 201-300)
  [0.6, AQI_COLORS.VERY_UNHEALTHY],   // Purple (300/500)
  [0.6, AQI_COLORS.HAZARDOUS],        // Maroon (Hazardous: 301-500)
  [1.0, AQI_COLORS.HAZARDOUS]         // Maroon (500/500)
];

// Timezone Options
export const TIMEZONE_OPTIONS = [
  { value: -12, label: 'UTC-12 (Baker Island)' },
  { value: -11, label: 'UTC-11 (Samoa)' },
  { value: -10, label: 'UTC-10 (Hawaii)' },
  { value: -9, label: 'UTC-9 (Alaska)' },
  { value: -8, label: 'UTC-8 (Pacific Standard)' },
  { value: -7, label: 'UTC-7 (Mountain/Pacific Daylight)' },
  { value: -6, label: 'UTC-6 (Central)' },
  { value: -5, label: 'UTC-5 (Eastern)' },
  { value: -4, label: 'UTC-4 (Atlantic)' },
  { value: -3, label: 'UTC-3 (Argentina)' },
  { value: -2, label: 'UTC-2 (Mid-Atlantic)' },
  { value: -1, label: 'UTC-1 (Azores)' },
  { value: 0, label: 'UTC (GMT)' },
  { value: 1, label: 'UTC+1 (Central European)' },
  { value: 2, label: 'UTC+2 (Eastern European)' },
  { value: 3, label: 'UTC+3 (Moscow)' },
  { value: 4, label: 'UTC+4 (Gulf)' },
  { value: 5, label: 'UTC+5 (Pakistan)' },
  { value: 6, label: 'UTC+6 (Bangladesh)' },
  { value: 7, label: 'UTC+7 (Indochina)' },
  { value: 8, label: 'UTC+8 (China)' },
  { value: 9, label: 'UTC+9 (Japan)' },
  { value: 10, label: 'UTC+10 (Australia East)' },
  { value: 11, label: 'UTC+11 (Solomon Islands)' },
  { value: 12, label: 'UTC+12 (Fiji)' }
];

// Date Range Options
export const DATE_RANGE_OPTIONS = [
  { value: 7, label: 'Last 7 days' },
  { value: 14, label: 'Last 14 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 60, label: 'Last 60 days' },
  { value: 90, label: 'Last 90 days' },
  { value: 180, label: 'Last 6 months' },
  { value: 365, label: 'Last 12 months' },
  { value: 'previous_year', label: 'Previous year' }
];

// AQI Legend Items
export const AQI_LEGEND_ITEMS = [
  { color: AQI_COLORS.NO_DATA, label: 'No Data' },
  { color: AQI_COLORS.GOOD, label: 'Good (0-50)' },
  { color: AQI_COLORS.MODERATE, label: 'Moderate (51-100)' },
  { color: AQI_COLORS.UNHEALTHY_SENSITIVE, label: 'Sensitive (101-150)' },
  { color: AQI_COLORS.UNHEALTHY, label: 'Unhealthy (151-200)' },
  { color: AQI_COLORS.VERY_UNHEALTHY, label: 'Very Unhealthy (201-300)' },
  { color: AQI_COLORS.HAZARDOUS, label: 'Hazardous (301-500)' }
];

// Chart Configuration
export const CHART_CONFIG = {
  RESPONSIVE: { responsive: true },
  Z_MIN: 0,
  Z_MAX: 500,
  TIME_SERIES_MAX_POINTS: 2000,
  MOBILE_BREAKPOINT: 768
};

// Annual Heatmap Configuration
export const ANNUAL_HEATMAP_CONFIG = {
  WEEKS_PER_YEAR: 52,
  DAYS_PER_WEEK: 7,
  MONTH_TICK_POSITIONS: [0, 4, 13, 22, 30, 39, 48], // Approximate month starts
  MONTH_LABELS: ['Jan', 'Feb', 'Apr', 'Jun', 'Aug', 'Oct', 'Dec'],
  DAY_LABELS: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
  GAP_SIZE: 3
}; 