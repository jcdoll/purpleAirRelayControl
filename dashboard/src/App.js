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
  processFilterEfficiencyTimelineData,
  processFilterEfficiencyAnnualData
} from './utils/chartDataProcessors';
import { formatDateToYMD } from './utils/common';

// Import chart components
import {
  RecentHeatmapChart,
  TimelineChart,
  HourlyChart,
  CorrelationChart,
  AnnualHeatmapChart,
  FilterTimelineChart,
  FilterAnnualHeatmapChart
} from './components/Charts';

// Import UI components
import Header from './components/UI/Header';
import SummaryCards from './components/UI/SummaryCards';
import LoadingError from './components/UI/LoadingError';
import ViewSelector from './components/Controls/ViewSelector';
import DateRangeControls from './components/Controls/DateRangeControls';
import { CSV_URL, FILTER_EFFICIENCY_CSV_URL, REFRESH_INTERVAL, VIEW_TYPES, TIME_CONSTANTS } from './constants/app';

function App() {
  // Consolidated state management
  const [state, setState] = useState({
    selectedView: VIEW_TYPES.TIMELINE,
    dateRange: 7,
    selectedYear: new Date().getFullYear(),
    aggregation: '95th',
    dateRangeMode: 'predefined',
    customStartDate: '',
    customEndDate: ''
  });

  // Data state
  const [data, setData] = useState([]);
  const [filterData, setFilterData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Air quality data fetching function
  const fetchAirQualityData = useCallback(async () => {
    const response = await fetch(CSV_URL);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const csvText = await response.text();
    
    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        complete: (results) => {
          if (results.errors.length > 0) {
            reject(new Error('CSV parsing error: ' + results.errors[0].message));
            return;
          }
          
          const processedData = results.data
            .filter(row => row.Timestamp && row.OutdoorAirQuality && row.IndoorAirQuality)
            .map(row => {
              const timestamp = new Date(row.Timestamp);
              return {
                timestamp,
                Timestamp: row.Timestamp,
                IndoorAirQuality: parseFloat(row.IndoorAirQuality),
                OutdoorAirQuality: parseFloat(row.OutdoorAirQuality),
                hour: timestamp.getHours(),
                date: formatDateToYMD(timestamp),
                dayOfWeek: timestamp.toLocaleDateString('en-US', { weekday: 'long' }),
                switch_state: row.SwitchState,
                sensor_type: row.VentilationState,
                log_reason: row.Reason || ''
              };
            })
            .filter(row => !isNaN(row.timestamp.getTime()) && !isNaN(row.IndoorAirQuality) && !isNaN(row.OutdoorAirQuality))
            .sort((a, b) => a.timestamp - b.timestamp);
          
          resolve(processedData);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  }, []);

  // Filter efficiency data fetching function
  const fetchFilterEfficiencyData = useCallback(async () => {
    const response = await fetch(FILTER_EFFICIENCY_CSV_URL);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const csvText = await response.text();
    
    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        complete: (results) => {
          if (results.errors.length > 0) {
            reject(new Error('Filter efficiency CSV parsing error: ' + results.errors[0].message));
            return;
          }
          
          const processedData = results.data
            .filter(row => row.Timestamp && row['Estimated Filter Efficiency (%)'] !== undefined && row['Estimated Filter Efficiency (%)'] !== '')
            .map(row => {
              const timestamp = new Date(row.Timestamp);
              return {
                timestamp,
                Timestamp: row.Timestamp,
                filterEfficiency: parseFloat(row['Estimated Filter Efficiency (%)']),
                efficiencyUncertainty: parseFloat(row['Efficiency Uncertainty (%)']) || 0,
                indoorPM25: parseFloat(row['Indoor PM2.5']) || 0,
                outdoorPM25: parseFloat(row['Outdoor PM2.5']) || 0,
                hour: timestamp.getHours(),
                date: formatDateToYMD(timestamp)
              };
            })
            .filter(row => !isNaN(row.timestamp.getTime()) && !isNaN(row.filterEfficiency))
            .sort((a, b) => a.timestamp - b.timestamp);
          
          resolve(processedData);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  }, []);

  // Combined data fetching function
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch both datasets in parallel
      const [airQualityData, filterEfficiencyData] = await Promise.all([
        fetchAirQualityData(),
        fetchFilterEfficiencyData().catch(() => []) // Gracefully handle filter data errors
      ]);
      
      setData(airQualityData);
      setFilterData(filterEfficiencyData);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (error) {
      setError(error.message);
      setLoading(false);
    }
  }, [fetchAirQualityData, fetchFilterEfficiencyData]);

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
    const combinedData = [...data, ...filterData];
    if (combinedData.length === 0) return [new Date().getFullYear()];
    const years = combinedData.map(item => item.timestamp.getFullYear());
    const uniqueYears = [...new Set(years)].sort((a, b) => b - a);
    return uniqueYears.length > 0 ? uniqueYears : [new Date().getFullYear()];
  }, [data, filterData]);

  // Filter data based on date range
  const filteredData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const now = new Date();
    let startDate;
    
    if (state.dateRangeMode === 'custom') {
      startDate = state.customStartDate ? new Date(state.customStartDate) : new Date(now.getTime() - (state.dateRange * TIME_CONSTANTS.MS_PER_DAY));
    } else {
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

  // Process filter efficiency data (use all data for timeline, not filtered by date range)
  const filterTimelineData = useMemo(() => 
    processFilterEfficiencyTimelineData(filterData),
    [filterData]
  );
  
  // Use appropriate aggregation defaults for each view type
  const effectiveAggregation = useMemo(() => {
    // Use 'average' as default for filter efficiency, '95th' for AQI views
    return state.selectedView === VIEW_TYPES.FILTER_EFFICIENCY && state.aggregation === '95th' ? 'average' : state.aggregation;
  }, [state.selectedView, state.aggregation]);

  const filterAnnualData = useMemo(() => 
    processFilterEfficiencyAnnualData(filterData, state.selectedYear, effectiveAggregation),
    [filterData, state.selectedYear, effectiveAggregation]
  );

  // Calculate latest sensor values summary
  const summary = useMemo(() => {
    if (data.length === 0) {
      return { indoorLatest: 'N/A', outdoorLatest: 'N/A' };
    }
    const latest = data[data.length - 1];
    const indoor = (!isNaN(latest.IndoorAirQuality) && latest.IndoorAirQuality !== null)
      ? latest.IndoorAirQuality.toFixed(1)
      : 'N/A';
    const outdoor = (!isNaN(latest.OutdoorAirQuality) && latest.OutdoorAirQuality !== null)
      ? latest.OutdoorAirQuality.toFixed(1)
      : 'N/A';
    return { indoorLatest: indoor, outdoorLatest: outdoor };
  }, [data]);

  // Handle loading and error states
  if (loading || error) {
    return <LoadingError loading={loading} error={error} onRetry={fetchData} />;
  }

  // Determine which chart to show based on selected view
  const isFilterEfficiencyView = state.selectedView === VIEW_TYPES.FILTER_EFFICIENCY;

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
        {/* Air Quality Charts */}
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
        
        {/* Filter Efficiency Charts */}
        {isFilterEfficiencyView && (
          <>
            <FilterTimelineChart 
              data={filterTimelineData} 
              timeRangeDescription={timeRangeDescription} 
              isVisible={true}
            />
            <FilterAnnualHeatmapChart 
              data={filterAnnualData} 
              selectedYear={state.selectedYear} 
              aggregation={effectiveAggregation}
              isVisible={true}
            />
          </>
        )}
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