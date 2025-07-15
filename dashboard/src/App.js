import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './styles/globals.css';
import styles from './App.module.css';
import controlsStyles from './components/UI/Controls.module.css';
import Papa from 'papaparse';

import {
  processHeatmapData,
  processHourlyStats,
  processTimeSeriesData,
  processCorrelationData,
  processAnnualHeatmapData,
  calculatePatternSummary
} from './utils/chartDataProcessors';
import { formatDateToYMD } from './utils/common';

// Import chart components
import {
  RecentHeatmapChart,
  TimelineChart,
  HourlyChart,
  CorrelationChart,
  AnnualHeatmapChart
} from './components/Charts';

// Import UI components
import Header from './components/UI/Header';
import SummaryCards from './components/UI/SummaryCards';
import LoadingError from './components/UI/LoadingError';
import ViewSelector from './components/Controls/ViewSelector';
import DateRangeControls from './components/Controls/DateRangeControls';
import { CSV_URL, REFRESH_INTERVAL, VIEW_TYPES, TIME_CONSTANTS } from './constants/app';

function App() {
  // Consolidated state management
  const [state, setState] = useState({
    selectedView: VIEW_TYPES.HEATMAP,
    dateRange: 7,
    selectedYear: new Date().getFullYear(),
    aggregation: 'max',
    dateRangeMode: 'predefined',
    customStartDate: '',
    customEndDate: ''
  });

  // Data state
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Simplified data fetching - no timezone complexity
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(CSV_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const csvText = await response.text();
      
      return new Promise((resolve, reject) => {
        Papa.parse(csvText, {
          header: true, // CSV has headers
          complete: (results) => {
            if (results.errors.length > 0) {
              reject(new Error('CSV parsing error: ' + results.errors[0].message));
              return;
            }
            
            // Process CSV data using header names
            const processedData = results.data
              .filter(row => row.Timestamp && row.OutdoorAirQuality && row.IndoorAirQuality) // Filter out empty rows
              .map(row => {
                const timestamp = new Date(row.Timestamp);
                return {
                  timestamp,
                  Timestamp: row.Timestamp, // Keep original string for compatibility
                  IndoorAirQuality: parseFloat(row.IndoorAirQuality),
                  OutdoorAirQuality: parseFloat(row.OutdoorAirQuality),
                  hour: timestamp.getHours(),
                  date: formatDateToYMD(timestamp), // no timezone, use sensor date directly
                  dayOfWeek: timestamp.toLocaleDateString('en-US', { weekday: 'long' }),
                  switch_state: row.SwitchState,
                  sensor_type: row.VentilationState,
                  log_reason: row.Reason || ''
                };
              })
              .filter(row => !isNaN(row.timestamp.getTime()) && !isNaN(row.IndoorAirQuality) && !isNaN(row.OutdoorAirQuality))
              .sort((a, b) => a.timestamp - b.timestamp);
            
            setData(processedData);
            setLastUpdate(new Date());
            setLoading(false);
            resolve();
          },
          error: (error) => {
            reject(error);
          }
        });
      });
    } catch (error) {
      setError(error.message);
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchData();
    }, REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchData]);

  // Helper to update state
  const updateState = (updates) => {
    setState(prevState => ({ ...prevState, ...updates }));
  };

  // Get available years for annual heatmap
  const availableYears = useMemo(() => {
    if (data.length === 0) return [new Date().getFullYear()];
    const years = data.map(item => item.timestamp.getFullYear());
    const uniqueYears = [...new Set(years)].sort((a, b) => b - a);
    return uniqueYears.length > 0 ? uniqueYears : [new Date().getFullYear()];
  }, [data]);

  // Filter data based on date range
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const now = new Date();
    let startDate;
    
    if (state.dateRangeMode === 'custom') {
      startDate = state.customStartDate ? new Date(state.customStartDate) : new Date(now.getTime() - (state.dateRange * TIME_CONSTANTS.MS_PER_DAY));
    } else {
      // Calculate start date and set to beginning of day (midnight)
      startDate = new Date(now.getTime() - (state.dateRange * TIME_CONSTANTS.MS_PER_DAY));
      startDate.setHours(0, 0, 0, 0);
    }
    
    const endDate = state.dateRangeMode === 'custom' && state.customEndDate ? 
      new Date(state.customEndDate) : now;
    
    return data.filter(item => {
      const itemDate = item.timestamp;
      return itemDate >= startDate && itemDate <= endDate;
    });
  }, [data, state.dateRange, state.dateRangeMode, state.customStartDate, state.customEndDate]);

  // Generate time range description
  const timeRangeDescription = useMemo(() => {
    if (state.dateRangeMode === 'custom') {
      const start = state.customStartDate ? new Date(state.customStartDate).toLocaleDateString() : 'N/A';
      const end = state.customEndDate ? new Date(state.customEndDate).toLocaleDateString() : 'N/A';
      return `${start} to ${end}`;
    } else {
      return `Last ${state.dateRange} days`;
    }
  }, [state.dateRange, state.dateRangeMode, state.customStartDate, state.customEndDate]);

  // Process data for different chart types
  const heatmapData = useMemo(() => 
    processHeatmapData(filteredData, state.dateRange),
    [filteredData, state.dateRange]
  );
  
  const hourlyData = useMemo(() => 
    processHourlyStats(filteredData),
    [filteredData]
  );
  
  const timeSeriesData = useMemo(() => 
    processTimeSeriesData(filteredData),
    [filteredData]
  );
  
  const correlationData = useMemo(() => 
    processCorrelationData(filteredData),
    [filteredData]
  );
  
  const annualHeatmapData = useMemo(() => 
    processAnnualHeatmapData(data, state.selectedYear, state.aggregation),
    [data, state.selectedYear, state.aggregation]
  );

  // Calculate pattern summary
  const summary = useMemo(() => calculatePatternSummary(data, filteredData), [data, filteredData]);

  // Handle loading and error states
  if (loading || error) {
    return <LoadingError loading={loading} error={error} onRetry={fetchData} />;
  }

  return (
    <div className={styles.app}>
      <Header lastUpdate={lastUpdate} onRefresh={fetchData} />
      <SummaryCards summary={summary} />

      <div className={controlsStyles.controls}>
        <ViewSelector 
          selectedView={state.selectedView} 
          onViewChange={(view) => updateState({ selectedView: view })} 
        />
        
        <DateRangeControls
          selectedView={state.selectedView}
          dateRangeMode={state.dateRangeMode}
          setDateRangeMode={(mode) => updateState({ dateRangeMode: mode })}
          dateRange={state.dateRange}
          setDateRange={(range) => updateState({ dateRange: range })}
          customStartDate={state.customStartDate}
          setCustomStartDate={(date) => updateState({ customStartDate: date })}
          customEndDate={state.customEndDate}
          setCustomEndDate={(date) => updateState({ customEndDate: date })}
          getAvailableYears={availableYears}
          selectedYear={state.selectedYear}
          setSelectedYear={(year) => updateState({ selectedYear: year })}
          aggregation={state.aggregation}
          setAggregation={(agg) => updateState({ aggregation: agg })}
        />
      </div>

      <div className={styles.chartContainer}>
        {/* Pre-render all charts for instant tab switching */}
        <RecentHeatmapChart 
          data={heatmapData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === VIEW_TYPES.HEATMAP}
          dateRange={state.dateRange}
        />
        <HourlyChart 
          data={hourlyData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === VIEW_TYPES.HOURLY}
        />
        <TimelineChart 
          data={timeSeriesData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === VIEW_TYPES.TIMELINE}
        />
        <CorrelationChart 
          data={correlationData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === VIEW_TYPES.CORRELATION}
        />
        <AnnualHeatmapChart 
          data={annualHeatmapData} 
          selectedYear={state.selectedYear} 
          aggregation={state.aggregation}
          isVisible={state.selectedView === VIEW_TYPES.ANNUAL_HEATMAP}
        />
      </div>

      <footer className={styles.footer}>
        <p>Data source: Google Sheets (auto-refreshes every 5 minutes)</p>
        <p>
          <a href="https://github.com/jcdoll/purpleAirRelayControl" target="_blank" rel="noopener noreferrer">
            View on GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App; 