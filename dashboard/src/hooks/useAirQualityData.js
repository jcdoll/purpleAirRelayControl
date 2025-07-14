import { useState, useEffect, useCallback } from 'react';
import Papa from 'papaparse';

// Google Sheets CSV URL
const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRN0PHzfkvu7IMHEf2PG6_Ne4Vr-Pstsg0Sa8-WNBSy9a_-10Vvpr_jYGZxLszyMw8CybUq_7tDGkBq/pub?gid=394013654&single=true&output=csv';

// Function to convert timestamp based on source timezone
const convertToTimezone = (sourceDate, sourceTimezoneOffset, targetTimezoneOffset) => {
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

export const useAirQualityData = (sourceTimezone, selectedTimezone) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = useCallback(async () => {
    try {
      const response = await fetch(CSV_URL);
      const text = await response.text();
      
      Papa.parse(text, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          const processedData = results.data
            .filter(row => row.Timestamp && row.IndoorAirQuality !== null && row.IndoorAirQuality !== '')
            .map(row => {
              const sourceTimestamp = new Date(row.Timestamp);
              const displayTimestamp = convertToTimezone(sourceTimestamp, sourceTimezone, selectedTimezone);
              
              // Fix: Use consistent timezone for both date and hour extraction
              // Don't use toISOString() as it converts back to UTC
              const year = displayTimestamp.getFullYear();
              const month = String(displayTimestamp.getMonth() + 1).padStart(2, '0');
              const day = String(displayTimestamp.getDate()).padStart(2, '0');
              const dateString = `${year}-${month}-${day}`;
              
              return {
                ...row,
                timestamp: displayTimestamp,
                hour: displayTimestamp.getHours(),
                date: dateString,
                dayOfWeek: displayTimestamp.toLocaleDateString('en-US', { weekday: 'long' })
              };
            })
            .filter(row => !isNaN(row.timestamp.getTime())); // Filter out invalid dates
          
          setData(processedData);
          setLoading(false);
          setLastUpdate(new Date());
        },
        error: (error) => {
          setError(error.message);
          setLoading(false);
        }
      });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [selectedTimezone, sourceTimezone]);

  useEffect(() => {
    fetchData();
    // Refresh data every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Re-process data when timezone changes
  useEffect(() => {
    if (data.length > 0) {
      fetchData();
    }
  }, [data.length, fetchData]);

  return {
    data,
    loading,
    error,
    lastUpdate,
    fetchData
  };
}; 