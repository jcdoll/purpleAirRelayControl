import { AQI_COLORS, AQI_THRESHOLDS, AQI_CLASSES } from '../constants/app';

/**
 * Get AQI color based on AQI value
 * @param {number} aqiValue - The AQI value to get color for
 * @returns {string} - Hex color code
 */
export const getAQIColor = (aqiValue) => {
  if (aqiValue <= AQI_THRESHOLDS.GOOD) return AQI_COLORS.GOOD;
  if (aqiValue <= AQI_THRESHOLDS.MODERATE) return AQI_COLORS.MODERATE;
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY_SENSITIVE) return AQI_COLORS.UNHEALTHY_SENSITIVE;
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY) return AQI_COLORS.UNHEALTHY;
  if (aqiValue <= AQI_THRESHOLDS.VERY_UNHEALTHY) return AQI_COLORS.VERY_UNHEALTHY;
  return AQI_COLORS.HAZARDOUS;
};

/**
 * Get AQI CSS class based on AQI value
 * @param {number} aqiValue - The AQI value to get class for
 * @returns {string} - CSS class name
 */
export const getAQIClass = (aqiValue) => {
  if (aqiValue <= AQI_THRESHOLDS.GOOD) return AQI_CLASSES.GOOD;
  if (aqiValue <= AQI_THRESHOLDS.MODERATE) return AQI_CLASSES.MODERATE;
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY_SENSITIVE) return AQI_CLASSES.UNHEALTHY_SENSITIVE;
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY) return AQI_CLASSES.UNHEALTHY;
  if (aqiValue <= AQI_THRESHOLDS.VERY_UNHEALTHY) return AQI_CLASSES.VERY_UNHEALTHY;
  return AQI_CLASSES.HAZARDOUS;
};

/**
 * Get AQI category name based on AQI value
 * @param {number} aqiValue - The AQI value to get category for
 * @returns {string} - Category name
 */
export const getAQICategory = (aqiValue) => {
  if (aqiValue <= AQI_THRESHOLDS.GOOD) return 'Good';
  if (aqiValue <= AQI_THRESHOLDS.MODERATE) return 'Moderate';
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY_SENSITIVE) return 'Unhealthy for Sensitive Groups';
  if (aqiValue <= AQI_THRESHOLDS.UNHEALTHY) return 'Unhealthy';
  if (aqiValue <= AQI_THRESHOLDS.VERY_UNHEALTHY) return 'Very Unhealthy';
  return 'Hazardous';
};

/**
 * Check if AQI value is considered good (safe for everyone)
 * @param {number} aqiValue - The AQI value to check
 * @returns {boolean} - True if AQI is good
 */
export const isAQIGood = (aqiValue) => {
  return aqiValue <= AQI_THRESHOLDS.GOOD;
};

/**
 * Check if AQI value is considered unhealthy (above moderate)
 * @param {number} aqiValue - The AQI value to check
 * @returns {boolean} - True if AQI is unhealthy
 */
export const isAQIUnhealthy = (aqiValue) => {
  return aqiValue > AQI_THRESHOLDS.MODERATE;
}; 