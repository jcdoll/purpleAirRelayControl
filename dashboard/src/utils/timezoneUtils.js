/**
 * Convert timestamp between timezones
 * @param {Date} sourceDate - The source date
 * @param {number} sourceTimezoneOffset - Source timezone offset in hours
 * @param {number} targetTimezoneOffset - Target timezone offset in hours
 * @returns {Date} - Converted date
 */
export const convertToTimezone = (sourceDate, sourceTimezoneOffset, targetTimezoneOffset) => {
  // If source and target are the same, no conversion needed
  if (sourceTimezoneOffset === targetTimezoneOffset) {
    return sourceDate;
  }
  
  // Convert to UTC first, then to target timezone
  const sourceTime = sourceDate.getTime();
  const utcTime = sourceTime - (sourceTimezoneOffset * 60 * 60 * 1000);
  const localTime = utcTime + (targetTimezoneOffset * 60 * 60 * 1000);
  
  return new Date(localTime);
};

/**
 * Get the current browser timezone offset in hours
 * @returns {number} - Timezone offset in hours
 */
export const getBrowserTimezoneOffset = () => {
  const now = new Date();
  return -now.getTimezoneOffset() / 60; // Convert to hours, flip sign
};

/**
 * Get current time in a specific timezone
 * @param {number} timezoneOffset - Timezone offset in hours
 * @returns {Date} - Current time in the specified timezone
 */
export const getCurrentTimeInTimezone = (timezoneOffset) => {
  const now = new Date();
  const browserOffset = getBrowserTimezoneOffset();
  
  if (browserOffset === timezoneOffset) {
    return now;
  }
  
  // Convert current time to specified timezone
  const offsetDiff = timezoneOffset - browserOffset;
  return new Date(now.getTime() + (offsetDiff * 60 * 60 * 1000));
};

/**
 * Format date to YYYY-MM-DD string in a specific timezone
 * @param {Date} date - The date to format
 * @param {number} timezoneOffset - Timezone offset in hours
 * @returns {string} - Formatted date string
 */
export const formatDateInTimezone = (date, timezoneOffset) => {
  const convertedDate = convertToTimezone(date, getBrowserTimezoneOffset(), timezoneOffset);
  const year = convertedDate.getFullYear();
  const month = String(convertedDate.getMonth() + 1).padStart(2, '0');
  const day = String(convertedDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Get timezone description from offset
 * @param {number} offset - Timezone offset in hours
 * @returns {string} - Human readable timezone description
 */
export const getTimezoneDescription = (offset) => {
  if (offset === 0) return 'UTC (GMT)';
  if (offset > 0) return `UTC+${offset}`;
  return `UTC${offset}`; // Negative sign is already included
}; 