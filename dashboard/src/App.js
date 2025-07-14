import React, { useState, useEffect, useMemo } from 'react';
import './App.css';

// Import our new hooks and components
import { useAirQualityData } from './hooks/useAirQualityData';
import { useDataFiltering } from './hooks/useDataFiltering';
import {
  processHeatmapData,
  processHourlyStats,
  processTimeSeriesData,
  processCorrelationData,
  processAnnualHeatmapData,
  calculatePatternSummary
} from './utils/chartDataProcessors';
import Header from './components/UI/Header';
import SummaryCards from './components/UI/SummaryCards';
import ViewSelector from './components/Controls/ViewSelector';
import DateRangeControls from './components/Controls/DateRangeControls';
import TimezoneControls from './components/Controls/TimezoneControls';
import HeatmapChart from './components/Charts/HeatmapChart';
import TimelineChart from './components/Charts/TimelineChart';
import HourlyChart from './components/Charts/HourlyChart';
import CorrelationChart from './components/Charts/CorrelationChart';
import AnnualHeatmapChart from './components/Charts/AnnualHeatmapChart';
import { GITHUB_URL, REFRESH_MESSAGE } from './constants/app';

function App() {
  // State for view and controls
  const [selectedView, setSelectedView] = useState('heatmap');
  const [dateRange, setDateRange] = useState(30);
  const [annualHeatmapAggregation, setAnnualHeatmapAggregation] = useState('average');
  const [selectedYear, setSelectedYear] = useState(() => new Date().getFullYear());
  const [timeRangeType, setTimeRangeType] = useState('recent'); // 'recent' or 'previous_year'
  const [dateRangeMode, setDateRangeMode] = useState('predefined'); // 'predefined' or 'custom'
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  
  // Timezone state
  const [selectedTimezone, setSelectedTimezone] = useState(() => {
    // Auto-detect local timezone offset
    const now = new Date();
    const offset = -now.getTimezoneOffset() / 60; // Convert to hours, flip sign
    return offset;
  });
  
  const [sourceTimezone, setSourceTimezone] = useState(() => {
    // Default to assuming source data is in local timezone
    const now = new Date();
    const offset = -now.getTimezoneOffset() / 60; // Convert to hours, flip sign
    return offset;
  });

  // Use our new hooks
  const { data, loading, error, lastUpdate, fetchData } = useAirQualityData(sourceTimezone, selectedTimezone);
  const { filteredData, getAvailableYears, getTimeRangeDescription } = useDataFiltering(
    data,
    dateRange,
    selectedTimezone,
    dateRangeMode,
    customStartDate,
    customEndDate,
    timeRangeType
  );

  // Update selectedYear when data changes
  useEffect(() => {
    if (data.length > 0) {
       // getAvailableYears is a memoized array, use it directly
      if (!getAvailableYears.includes(selectedYear)) {
        setSelectedYear(getAvailableYears[0]);
      }
    }
  }, [data, selectedYear, getAvailableYears]);

  // Memoized chart data processing
  const heatmapData = useMemo(() => processHeatmapData(filteredData, dateRange), [filteredData, dateRange]);
  const hourlyData = useMemo(() => processHourlyStats(filteredData), [filteredData]);
  const timeSeriesData = useMemo(() => processTimeSeriesData(filteredData), [filteredData]);
  const correlationData = useMemo(() => processCorrelationData(filteredData), [filteredData]);
  const annualHeatmapData = useMemo(() => 
    processAnnualHeatmapData(data, selectedYear, selectedTimezone, annualHeatmapAggregation),
    [data, selectedYear, selectedTimezone, annualHeatmapAggregation]
  );

  // Calculate pattern summary
  const summary = useMemo(() => calculatePatternSummary(data, filteredData), [data, filteredData]);

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading air quality data...</h2>
        <div className="spinner"></div>
        <p>Fetching data from Google Sheets...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h2>Error loading data</h2>
        <p>{error}</p>
        <p>Make sure your Google Sheet is published to web as CSV</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="App">
      <Header
        lastUpdate={lastUpdate}
        onRefresh={fetchData}
      />

      <SummaryCards summary={summary} />

      <div className="controls">
        <ViewSelector 
          selectedView={selectedView} 
          onViewChange={setSelectedView} 
        />
        
        <DateRangeControls
          selectedView={selectedView}
          dateRangeMode={dateRangeMode}
          setDateRangeMode={setDateRangeMode}
          timeRangeType={timeRangeType}
          dateRange={dateRange}
          setTimeRangeType={setTimeRangeType}
          setDateRange={setDateRange}
          customStartDate={customStartDate}
          setCustomStartDate={setCustomStartDate}
          customEndDate={customEndDate}
          setCustomEndDate={setCustomEndDate}
          getAvailableYears={getAvailableYears}
          selectedYear={selectedYear}
          setSelectedYear={setSelectedYear}
          annualHeatmapAggregation={annualHeatmapAggregation}
          setAnnualHeatmapAggregation={setAnnualHeatmapAggregation}
        />
        
        <TimezoneControls
          sourceTimezone={sourceTimezone}
          setSourceTimezone={setSourceTimezone}
          selectedTimezone={selectedTimezone}
          setSelectedTimezone={setSelectedTimezone}
        />
      </div>

      <div className="chart-container">
        {selectedView === 'heatmap' && data.length > 0 && (
          <HeatmapChart 
            data={heatmapData} 
            timeRangeDescription={getTimeRangeDescription} 
          />
        )}

        {selectedView === 'hourly' && (
          <HourlyChart 
            data={hourlyData} 
            timeRangeDescription={getTimeRangeDescription} 
          />
        )}

        {selectedView === 'timeline' && (
          <TimelineChart 
            data={timeSeriesData} 
            timeRangeDescription={getTimeRangeDescription} 
          />
        )}

        {selectedView === 'correlation' && (
          <CorrelationChart 
            data={correlationData} 
            timeRangeDescription={getTimeRangeDescription} 
          />
        )}

        {selectedView === 'annual-heatmap' && (
          <AnnualHeatmapChart 
            data={annualHeatmapData} 
            selectedYear={selectedYear} 
            aggregation={annualHeatmapAggregation} 
          />
        )}
      </div>

      <footer>
        <p>{REFRESH_MESSAGE}</p>
        <p>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
            View on GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App; 