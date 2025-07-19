import React from 'react';
import Chart from 'react-apexcharts';
import { getLineChartOptions, getXAxisConfig, getYAxisConfig, TOOLTIP_FORMATTERS, ANIMATION_DISABLED, TOOLBAR_DISABLED } from '../../utils/chartConfigUtils';
import { CHART_CONSTANTS } from '../../constants/app';
import styles from './Chart.module.css';

const FilterTimelineChart = ({ data, timeRangeDescription, isVisible }) => {
  const options = {
    chart: { 
      type: 'line',
      height: CHART_CONSTANTS.TIMELINE_CHART_HEIGHT,
      animations: { enabled: false },
      toolbar: { show: false }
    },
    xaxis: {
      type: 'datetime',
      title: { text: 'Time' },
      labels: { datetimeUTC: false }
    },
    yaxis: {
      title: { text: 'Filter Efficiency (%)' },
      min: 0,
      max: 100,
      labels: {
        formatter: function (value) {
          return value?.toFixed(1) + '%';
        }
      }
    },
    tooltip: {
      shared: true,
      intersect: false,
      x: { format: 'dd MMM yyyy HH:mm' },
      y: { 
        formatter: function(value) {
          return value?.toFixed(1) + '%';
        }
      }
    },
    colors: ['#00E400'],
    stroke: {
      width: 2,
      curve: 'smooth'
    },
    markers: {
      size: 0
    },
    grid: {
      show: true
    }
  };

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Filter Efficiency Timeline - All Available Data</h2>
      <Chart options={options} series={data} type="line" height={CHART_CONSTANTS.TIMELINE_CHART_HEIGHT} />
    </div>
  );
};

export default FilterTimelineChart; 