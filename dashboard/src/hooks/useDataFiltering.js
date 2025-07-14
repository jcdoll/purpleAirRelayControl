import { useMemo } from 'react';

export const useDataFiltering = (
  data,
  dateRange,
  selectedTimezone,
  dateRangeMode,
  customStartDate,
  customEndDate,
  timeRangeType
) => {
  
  const getFilteredData = useMemo(() => {
    // Get current time - since we're comparing with data that's already in display timezone,
    // we need current time in the same timezone
    const now = new Date();
    
    // If user browser is in same timezone as display, no conversion needed
    const browserTZOffset = -now.getTimezoneOffset() / 60;
    let displayNow;
    
    if (browserTZOffset === selectedTimezone) {
      displayNow = now;
    } else {
      // Convert current time to display timezone
      const offsetDiff = selectedTimezone - browserTZOffset;
      displayNow = new Date(now.getTime() + (offsetDiff * 60 * 60 * 1000));
    }
    
    let filteredData;
    
    if (dateRangeMode === 'custom') {
      if (!customStartDate || !customEndDate) return data;
      
      // Helper function to convert timezone (duplicated from useAirQualityData for now)
      const convertToTimezone = (sourceDate, sourceTimezoneOffset, targetTimezoneOffset) => {
        if (sourceTimezoneOffset === targetTimezoneOffset) {
          return sourceDate;
        }
        const sourceTime = sourceDate.getTime();
        const utcTime = sourceTime - (sourceTimezoneOffset * 60 * 60 * 1000);
        const localTime = utcTime + (targetTimezoneOffset * 60 * 60 * 1000);
        return new Date(localTime);
      };
      
      // Convert custom dates to display timezone
      const start = convertToTimezone(new Date(customStartDate), 0, selectedTimezone);
      const end = convertToTimezone(new Date(customEndDate), 0, selectedTimezone);
      end.setHours(23, 59, 59, 999); // Include the full end date
      filteredData = data.filter(d => d.timestamp >= start && d.timestamp <= end && d.timestamp <= displayNow);
    }
    else if (timeRangeType === 'previous_year') {
      const oneYearAgo = new Date(displayNow.getFullYear() - 1, displayNow.getMonth(), displayNow.getDate());
      const twoYearsAgo = new Date(displayNow.getFullYear() - 2, displayNow.getMonth(), displayNow.getDate());
      filteredData = data.filter(d => d.timestamp >= twoYearsAgo && d.timestamp <= oneYearAgo);
    }
    else {
      // Recent data (predefined ranges)
      const cutoffDate = new Date(displayNow);
      cutoffDate.setDate(cutoffDate.getDate() - dateRange);
      
      filteredData = data.filter(d => d.timestamp > cutoffDate && d.timestamp <= displayNow);
    }
    
    return filteredData;
  }, [data, dateRange, selectedTimezone, dateRangeMode, customStartDate, customEndDate, timeRangeType]);

  // Helper function to get available years from data
  const getAvailableYears = useMemo(() => {
    if (data.length === 0) return [new Date().getFullYear()];
    
    const years = [...new Set(data.map(row => row.timestamp.getFullYear()))];
    return years.sort((a, b) => b - a); // Sort in descending order (newest first)
  }, [data]);

  // Helper function to get a description of the current time range
  const getTimeRangeDescription = useMemo(() => {
    if (dateRangeMode === 'custom') {
      if (!customStartDate || !customEndDate) return 'custom dates';
      const start = new Date(customStartDate).toLocaleDateString();
      const end = new Date(customEndDate).toLocaleDateString();
      return `${start} to ${end}`;
    }
    
    if (timeRangeType === 'previous_year') {
      return 'previous year';
    }
    
    if (dateRange === 180) return 'last 6 months';
    if (dateRange === 365) return 'last 12 months';
    return `last ${dateRange} days`;
  }, [dateRangeMode, customStartDate, customEndDate, timeRangeType, dateRange]);

  return {
    filteredData: getFilteredData,
    getAvailableYears,
    getTimeRangeDescription
  };
}; 