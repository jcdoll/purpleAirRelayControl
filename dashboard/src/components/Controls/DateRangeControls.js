import React from 'react';
import styles from './DateRangeControls.module.css';
import { VIEW_TYPES, AGGREGATION_OPTIONS } from '../../constants/app';

const DateRangeControls = ({
  selectedView,
  dateRangeMode,
  setDateRangeMode,
  dateRange,
  setDateRange,
  customStartDate,
  setCustomStartDate,
  customEndDate,
  setCustomEndDate,
  getAvailableYears,
  selectedYear,
  setSelectedYear,
  aggregation,
  setAggregation
}) => {
  const handleDateRangeChange = (e) => {
    const value = e.target.value;
    setDateRange(Number(value));
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
          value={dateRange} 
          onChange={handleDateRangeChange}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 6 months</option>
          <option value={365}>Last 12 months</option>
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

  if (selectedView === VIEW_TYPES.HEATMAP) {
    return (
      <div className={styles.heatmapControls}>
        {renderCommonDateControls()}
      </div>
    );
  }

  if (selectedView === VIEW_TYPES.HOURLY) {
    return (
      <div className={styles.hourlyControls}>
        {renderCommonDateControls()}
      </div>
    );
  }

  if (selectedView === VIEW_TYPES.CORRELATION || selectedView === VIEW_TYPES.TIMELINE) {
    return renderCommonDateControls();
  }

  if (selectedView === VIEW_TYPES.ANNUAL_HEATMAP) {
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
          <select value={aggregation} onChange={(e) => setAggregation(e.target.value)}>
            {AGGREGATION_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </div>
    );
  }

  return null;
};

export default DateRangeControls; 