import React from 'react';
import styles from './DateRangeControls.module.css';

const DateRangeControls = ({
  selectedView,
  dateRangeMode,
  setDateRangeMode,
  timeRangeType,
  dateRange,
  setTimeRangeType,
  setDateRange,
  customStartDate,
  setCustomStartDate,
  customEndDate,
  setCustomEndDate,
  getAvailableYears,
  selectedYear,
  setSelectedYear,
  annualHeatmapAggregation,
  setAnnualHeatmapAggregation
}) => {
  const handleDateRangeChange = (e) => {
    const value = e.target.value;
    if (value === 'previous_year') {
      setTimeRangeType('previous_year');
      setDateRange(365);
    } else {
      setTimeRangeType('recent');
      setDateRange(Number(value));
    }
  };

  // Common date range controls for heatmap, hourly, timeline, and correlation views
  const renderCommonDateControls = () => (
    <div className={styles.dateRange}>
      <label>Time frame: </label>
      <div className={styles.timeRangeToggle}>
        <label>
          <input 
            type="radio" 
            name="dateRangeMode" 
            value="predefined" 
            checked={dateRangeMode === 'predefined'} 
            onChange={(e) => setDateRangeMode(e.target.value)} 
          />
          Predefined
        </label>
        <label>
          <input 
            type="radio" 
            name="dateRangeMode" 
            value="custom" 
            checked={dateRangeMode === 'custom'} 
            onChange={(e) => setDateRangeMode(e.target.value)} 
          />
          Custom
        </label>
      </div>
      {dateRangeMode === 'predefined' ? (
        <select 
          value={timeRangeType === 'previous_year' ? 'previous_year' : dateRange} 
          onChange={handleDateRangeChange}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 6 months</option>
          <option value={365}>Last 12 months</option>
          <option value="previous_year">Previous year</option>
        </select>
      ) : (
        <div className={styles.customDateRange}>
          <input
            type="date"
            value={customStartDate}
            onChange={(e) => setCustomStartDate(e.target.value)}
            placeholder="Start date"
          />
          <span>to</span>
          <input
            type="date"
            value={customEndDate}
            onChange={(e) => setCustomEndDate(e.target.value)}
            placeholder="End date"
          />
        </div>
      )}
    </div>
  );

  if (selectedView === 'heatmap') {
    return (
      <div className={styles.heatmapControls}>
        {renderCommonDateControls()}
      </div>
    );
  }

  if (selectedView === 'hourly') {
    return (
      <div className={styles.hourlyControls}>
        {renderCommonDateControls()}
      </div>
    );
  }

  if (selectedView === 'correlation' || selectedView === 'timeline') {
    return renderCommonDateControls();
  }

  if (selectedView === 'annual-heatmap') {
    return (
      <div className={styles.annualHeatmapControls}>
        <div className={styles.yearSelector}>
          <label>Year: </label>
          <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
            {getAvailableYears.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
        <div className={styles.aggregationType}>
          <label>Aggregation: </label>
          <select value={annualHeatmapAggregation} onChange={(e) => setAnnualHeatmapAggregation(e.target.value)}>
            <option value="average">Daily Average</option>
            <option value="max">Daily Maximum</option>
          </select>
        </div>
      </div>
    );
  }

  return null;
};

export default DateRangeControls; 