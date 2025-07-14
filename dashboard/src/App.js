import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './styles/globals.css';
import styles from './App.module.css';
import controlsStyles from './components/UI/Controls.module.css';
import loadingStyles from './components/UI/LoadingError.module.css';
import Papa from 'papaparse';

import {
  processHeatmapData,
  processHourlyStats,
  processTimeSeriesData,
  processCorrelationData,
  processAnnualHeatmapData,
  calculatePatternSummary
} from './utils/chartDataProcessors';

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
import ViewSelector from './components/Controls/ViewSelector';
import DateRangeControls from './components/Controls/DateRangeControls';
import { CSV_URL, REFRESH_INTERVAL } from './constants/app';

function App() {
  // Consolidated state management
  const [state, setState] = useState({
    selectedView: 'heatmap',
    dateRange: 7,
    selectedYear: new Date().getFullYear(),
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
                  date: timestamp.getFullYear() + '-' + String(timestamp.getMonth() + 1).padStart(2, '0') + '-' + String(timestamp.getDate()).padStart(2, '0'), // no timezone, use sensor date directly
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
      startDate = state.customStartDate ? new Date(state.customStartDate) : new Date(now.getTime() - (state.dateRange * 24 * 60 * 60 * 1000));
    } else {
      // Calculate start date and set to beginning of day (midnight)
      startDate = new Date(now.getTime() - (state.dateRange * 24 * 60 * 60 * 1000));
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
    processAnnualHeatmapData(data, state.selectedYear, 'average'),
    [data, state.selectedYear]
  );

  // Calculate pattern summary
  const summary = useMemo(() => calculatePatternSummary(data, filteredData), [data, filteredData]);

  if (loading) {
    return (
      <div className={loadingStyles.loading}>
        <h2>Loading air quality data...</h2>
        <div className={loadingStyles.spinner}></div>
        <p>Fetching data from Google Sheets...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={loadingStyles.error}>
        <h2>Error loading data</h2>
        <p>{error}</p>
        <p>Make sure your Google Sheet is published to web as CSV</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
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
          timeRangeType="recent"
          dateRange={state.dateRange}
          setTimeRangeType={() => {}}
          setDateRange={(range) => updateState({ dateRange: range })}
          customStartDate={state.customStartDate}
          setCustomStartDate={(date) => updateState({ customStartDate: date })}
          customEndDate={state.customEndDate}
          setCustomEndDate={(date) => updateState({ customEndDate: date })}
          getAvailableYears={availableYears}
          selectedYear={state.selectedYear}
          setSelectedYear={(year) => updateState({ selectedYear: year })}
          annualHeatmapAggregation="average"
          setAnnualHeatmapAggregation={() => {}}
        />
      </div>

      <div className={styles.chartContainer}>
        {/* Pre-render all charts for instant tab switching */}
        <RecentHeatmapChart 
          data={heatmapData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === 'heatmap'}
          dateRange={state.dateRange}
        />
        <HourlyChart 
          data={hourlyData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === 'hourly'}
        />
        <TimelineChart 
          data={timeSeriesData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === 'timeline'}
        />
        <CorrelationChart 
          data={correlationData} 
          timeRangeDescription={timeRangeDescription} 
          isVisible={state.selectedView === 'correlation'}
        />
        <AnnualHeatmapChart 
          data={annualHeatmapData} 
          selectedYear={state.selectedYear} 
          aggregation="average"
          isVisible={state.selectedView === 'annual-heatmap'}
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