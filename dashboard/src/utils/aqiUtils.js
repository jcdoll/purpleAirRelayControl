import { AQI_COLORS, AQI_THRESHOLDS, AQI_CLASSES } from '../constants/app';

/**
 * Convert hex color to RGB
 * @param {string} hex - Hex color code
 * @returns {object} - RGB object {r, g, b}
 */
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
};

/**
 * Convert RGB to hex color
 * @param {number} r - Red component (0-255)
 * @param {number} g - Green component (0-255)
 * @param {number} b - Blue component (0-255)
 * @returns {string} - Hex color code
 */
const rgbToHex = (r, g, b) => {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
};

/**
 * Linear interpolation between two RGB colors
 * @param {object} color1 - First RGB color {r, g, b}
 * @param {object} color2 - Second RGB color {r, g, b}
 * @param {number} factor - Interpolation factor (0-1)
 * @returns {object} - Interpolated RGB color {r, g, b}
 */
const interpolateColor = (color1, color2, factor) => {
  return {
    r: Math.round(color1.r + (color2.r - color1.r) * factor),
    g: Math.round(color1.g + (color2.g - color1.g) * factor),
    b: Math.round(color1.b + (color2.b - color1.b) * factor)
  };
};

/**
 * Get continuous AQI color using linear interpolation
 * @param {number} aqiValue - The AQI value to get color for
 * @returns {string} - Hex color code
 */
export const getAQIColor = (aqiValue) => {
  // Define color stops for continuous interpolation
  const colorStops = [
    { aqi: 0, color: AQI_COLORS.CLEAR },        // Clear/White
    { aqi: 50, color: AQI_COLORS.GOOD },
    { aqi: 100, color: AQI_COLORS.MODERATE },
    { aqi: 150, color: AQI_COLORS.UNHEALTHY_SENSITIVE },
    { aqi: 200, color: AQI_COLORS.UNHEALTHY },
    { aqi: 300, color: AQI_COLORS.VERY_UNHEALTHY },
    { aqi: 500, color: AQI_COLORS.HAZARDOUS }
  ];

  // Handle edge cases
  if (aqiValue <= 0) return colorStops[0].color;
  if (aqiValue >= 500) return colorStops[colorStops.length - 1].color;

  // Find the two color stops to interpolate between
  let lowerStop = colorStops[0];
  let upperStop = colorStops[colorStops.length - 1];

  for (let i = 0; i < colorStops.length - 1; i++) {
    if (aqiValue >= colorStops[i].aqi && aqiValue <= colorStops[i + 1].aqi) {
      lowerStop = colorStops[i];
      upperStop = colorStops[i + 1];
      break;
    }
  }

  // Calculate interpolation factor
  const factor = (aqiValue - lowerStop.aqi) / (upperStop.aqi - lowerStop.aqi);

  // Convert colors to RGB and interpolate
  const lowerRgb = hexToRgb(lowerStop.color);
  const upperRgb = hexToRgb(upperStop.color);
  const interpolatedRgb = interpolateColor(lowerRgb, upperRgb, factor);

  // Convert back to hex
  return rgbToHex(interpolatedRgb.r, interpolatedRgb.g, interpolatedRgb.b);
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