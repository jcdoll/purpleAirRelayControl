import { 
  getAQIColor, 
  getAQIClass, 
  getAQICategory, 
  isAQIGood, 
  isAQIUnhealthy 
} from '../../utils/aqiUtils';
import { AQI_COLORS, AQI_CLASSES } from '../../constants/app';

describe('aqiUtils', () => {
  describe('getAQIColor', () => {
    test('returns correct color for good air quality (0-50)', () => {
      expect(getAQIColor(0)).toBe(AQI_COLORS.GOOD);
      expect(getAQIColor(25)).toBe(AQI_COLORS.GOOD);
      expect(getAQIColor(50)).toBe(AQI_COLORS.GOOD);
    });

    test('returns correct color for moderate air quality (51-100)', () => {
      expect(getAQIColor(51)).toBe(AQI_COLORS.MODERATE);
      expect(getAQIColor(75)).toBe(AQI_COLORS.MODERATE);
      expect(getAQIColor(100)).toBe(AQI_COLORS.MODERATE);
    });

    test('returns correct color for unhealthy for sensitive air quality (101-150)', () => {
      expect(getAQIColor(101)).toBe(AQI_COLORS.UNHEALTHY_SENSITIVE);
      expect(getAQIColor(125)).toBe(AQI_COLORS.UNHEALTHY_SENSITIVE);
      expect(getAQIColor(150)).toBe(AQI_COLORS.UNHEALTHY_SENSITIVE);
    });

    test('returns correct color for unhealthy air quality (151-200)', () => {
      expect(getAQIColor(151)).toBe(AQI_COLORS.UNHEALTHY);
      expect(getAQIColor(175)).toBe(AQI_COLORS.UNHEALTHY);
      expect(getAQIColor(200)).toBe(AQI_COLORS.UNHEALTHY);
    });

    test('returns correct color for very unhealthy air quality (201-300)', () => {
      expect(getAQIColor(201)).toBe(AQI_COLORS.VERY_UNHEALTHY);
      expect(getAQIColor(250)).toBe(AQI_COLORS.VERY_UNHEALTHY);
      expect(getAQIColor(300)).toBe(AQI_COLORS.VERY_UNHEALTHY);
    });

    test('returns correct color for hazardous air quality (301+)', () => {
      expect(getAQIColor(301)).toBe(AQI_COLORS.HAZARDOUS);
      expect(getAQIColor(400)).toBe(AQI_COLORS.HAZARDOUS);
      expect(getAQIColor(500)).toBe(AQI_COLORS.HAZARDOUS);
    });
  });

  describe('getAQIClass', () => {
    test('returns correct CSS class for good air quality', () => {
      expect(getAQIClass(25)).toBe(AQI_CLASSES.GOOD);
    });

    test('returns correct CSS class for moderate air quality', () => {
      expect(getAQIClass(75)).toBe(AQI_CLASSES.MODERATE);
    });

    test('returns correct CSS class for unhealthy air quality', () => {
      expect(getAQIClass(180)).toBe(AQI_CLASSES.UNHEALTHY);
    });

    test('returns correct CSS class for hazardous air quality', () => {
      expect(getAQIClass(400)).toBe(AQI_CLASSES.HAZARDOUS);
    });
  });

  describe('getAQICategory', () => {
    test('returns correct category names', () => {
      expect(getAQICategory(25)).toBe('Good');
      expect(getAQICategory(75)).toBe('Moderate');
      expect(getAQICategory(125)).toBe('Unhealthy for Sensitive Groups');
      expect(getAQICategory(175)).toBe('Unhealthy');
      expect(getAQICategory(250)).toBe('Very Unhealthy');
      expect(getAQICategory(400)).toBe('Hazardous');
    });
  });

  describe('isAQIGood', () => {
    test('returns true for good AQI values', () => {
      expect(isAQIGood(0)).toBe(true);
      expect(isAQIGood(25)).toBe(true);
      expect(isAQIGood(50)).toBe(true);
    });

    test('returns false for non-good AQI values', () => {
      expect(isAQIGood(51)).toBe(false);
      expect(isAQIGood(100)).toBe(false);
      expect(isAQIGood(200)).toBe(false);
    });
  });

  describe('isAQIUnhealthy', () => {
    test('returns false for good and moderate AQI values', () => {
      expect(isAQIUnhealthy(25)).toBe(false);
      expect(isAQIUnhealthy(50)).toBe(false);
      expect(isAQIUnhealthy(100)).toBe(false);
    });

    test('returns true for unhealthy AQI values', () => {
      expect(isAQIUnhealthy(101)).toBe(true);
      expect(isAQIUnhealthy(150)).toBe(true);
      expect(isAQIUnhealthy(300)).toBe(true);
    });
  });
}); 