import { 
  getAQIColor, 
  getAQIClass, 
  getAQICategory, 
  isAQIGood, 
  isAQIUnhealthy 
} from '../../utils/aqiUtils';

describe('aqiUtils', () => {
  describe('getAQIColor', () => {
    it('should return correct colors for continuous mode', () => {
      expect(getAQIColor(0)).toBe('#FFFFFF');   // White at AQI 0
      expect(getAQIColor(50)).toBe('#00E400');  // Green at AQI 50
      expect(getAQIColor(100)).toBe('#FFDC00'); // Yellow at AQI 100
      expect(getAQIColor(150)).toBe('#FF7E00'); // Orange at AQI 150
      expect(getAQIColor(200)).toBe('#FF0000'); // Red at AQI 200
      expect(getAQIColor(300)).toBe('#8F3F97'); // Purple at AQI 300
      expect(getAQIColor(500)).toBe('#7E0023'); // Maroon at AQI 500
    });
    
    it('should handle edge cases', () => {
      expect(getAQIColor(0)).toBe('#FFFFFF');   // Exactly 0 should be white
      expect(getAQIColor(25)).toMatch(/^#[0-9A-Fa-f]{6}$/); // Should return valid hex color
      expect(getAQIColor(600)).toBe('#7E0023'); // Values above 500 should be maroon
    });

    it('should interpolate colors between breakpoints', () => {
      const color25 = getAQIColor(25);  // Between 0 and 50
      const color75 = getAQIColor(75);  // Between 50 and 100
      
      // Colors should be valid hex values
      expect(color25).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(color75).toMatch(/^#[0-9A-Fa-f]{6}$/);
      
      // Color at 25 should be different from both white and green
      expect(color25).not.toBe('#FFFFFF');
      expect(color25).not.toBe('#00E400');
      
      // Color at 75 should be different from both green and yellow  
      expect(color75).not.toBe('#00E400');
      expect(color75).not.toBe('#FFDC00');
    });
  });

  describe('getAQIClass', () => {
    it('should return correct CSS classes', () => {
      expect(getAQIClass(25)).toBe('aqi-good');
      expect(getAQIClass(75)).toBe('aqi-moderate');
      expect(getAQIClass(125)).toBe('aqi-unhealthy-sensitive');
      expect(getAQIClass(175)).toBe('aqi-unhealthy');
      expect(getAQIClass(250)).toBe('aqi-very-unhealthy');
      expect(getAQIClass(400)).toBe('aqi-hazardous');
    });
  });

  describe('getAQICategory', () => {
    it('should return correct category names', () => {
      expect(getAQICategory(25)).toBe('Good');
      expect(getAQICategory(75)).toBe('Moderate');
      expect(getAQICategory(125)).toBe('Unhealthy for Sensitive Groups');
      expect(getAQICategory(175)).toBe('Unhealthy');
      expect(getAQICategory(250)).toBe('Very Unhealthy');
      expect(getAQICategory(400)).toBe('Hazardous');
    });
  });

  describe('isAQIGood', () => {
    it('should correctly identify good AQI values', () => {
      expect(isAQIGood(0)).toBe(true);
      expect(isAQIGood(25)).toBe(true);
      expect(isAQIGood(50)).toBe(true);
      expect(isAQIGood(51)).toBe(false);
      expect(isAQIGood(100)).toBe(false);
    });
  });

  describe('isAQIUnhealthy', () => {
    it('should correctly identify unhealthy AQI values', () => {
      expect(isAQIUnhealthy(50)).toBe(false);
      expect(isAQIUnhealthy(100)).toBe(false);
      expect(isAQIUnhealthy(101)).toBe(true);
      expect(isAQIUnhealthy(200)).toBe(true);
      expect(isAQIUnhealthy(500)).toBe(true);
    });
  });
}); 