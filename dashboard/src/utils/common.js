/**
 * Common utility functions shared across the dashboard
 */

/**
 * Validates if a value is not null, undefined, or NaN
 * @param {*} value - The value to validate
 * @returns {boolean} True if the value is valid
 */
export const isValidValue = (value) => {
  return value !== null && value !== undefined && !isNaN(value);
};

/**
 * Calculates the average of an array of numbers
 * @param {number[]} values - Array of numbers
 * @returns {number|null} The average value, or null if array is empty
 */
export const calculateAverage = (values) => {
  if (!values || values.length === 0) return null;
  const validValues = values.filter(isValidValue);
  if (validValues.length === 0) return null;
  return validValues.reduce((sum, val) => sum + val, 0) / validValues.length;
};

/**
 * Filters out invalid data points from an array
 * @param {Object[]} data - Array of data objects with x,y properties
 * @returns {Object[]} Filtered array with only valid data points
 */
export const filterValidData = (data) => {
  return data.filter(item => 
    isValidValue(item.y) && 
    isValidValue(item.x)
  );
};

/**
 * Formats an hour number (0-23) to display format
 * @param {number} hour - Hour number (0-23)
 * @returns {string} Formatted hour string (e.g., "14:00")
 */
export const formatHour = (hour) => {
  return `${hour}:00`;
};

/**
 * Formats a date to a consistent string format
 * @param {Date} date - Date object to format
 * @param {string} format - Format type ('date', 'datetime', 'time')
 * @returns {string} Formatted date string
 */
export const formatDate = (date, format = 'date') => {
  if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
    return 'Invalid Date';
  }
  
  switch (format) {
    case 'datetime':
      return date.toLocaleString();
    case 'time':
      return date.toLocaleTimeString();
    case 'date':
    default:
      return date.toLocaleDateString();
  }
};

/**
 * Groups an array of objects by a key function
 * @param {Object[]} data - Array of objects to group
 * @param {Function} keyFunc - Function that returns the grouping key for each item
 * @returns {Object} Object with keys as group identifiers and values as arrays of items
 */
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

/**
 * Formats a tooltip value for AQI display
 * @param {number|null|undefined} value - The AQI value to format
 * @returns {string} Formatted value or 'No data' for invalid values
 */
export const formatTooltipValue = (value) => {
  return value === -1 || value === null || value === undefined ? 'No data' : value.toFixed(1);
};

/**
 * Calculates averages for grouped data
 * @param {Object} groupedData - Object with arrays of values as properties
 * @param {Function} valueFunc - Optional function to extract numeric value from items
 * @returns {Object} Object with same keys and average values
 */
export const calculateGroupAverages = (groupedData, valueFunc = (x) => x) => {
  const result = {};
  Object.keys(groupedData).forEach(key => {
    const values = groupedData[key].map(valueFunc);
    result[key] = calculateAverage(values);
  });
  return result;
};

/**
 * Formats a date to YYYY-MM-DD format
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
export const formatDateToYMD = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};