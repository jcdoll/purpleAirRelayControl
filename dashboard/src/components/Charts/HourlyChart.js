import React from 'react';
import Chart from 'react-apexcharts';
import { getLineChartOptions, getXAxisConfig, getYAxisConfig, TOOLTIP_FORMATTERS, ANIMATION_DISABLED, TOOLBAR_DISABLED } from '../../utils/chartConfigUtils';
import { createHourlyComparisonSeries } from '../../utils/seriesCreators';
import styles from './Chart.module.css';

const HourlyChart = ({ data, timeRangeDescription, isVisible }) => {
  const series = createHourlyComparisonSeries(data);
  
  const options = getLineChartOptions({
    chart: { 
      height: 400, 
      zoom: { enabled: false },
      animations: ANIMATION_DISABLED,
      toolbar: TOOLBAR_DISABLED
    },
    stroke: { width: 3 },
    xaxis: {
      ...getXAxisConfig('Hour of Day'),
      categories: data[0]?.x || [],
      crosshairs: { show: false },
      title: { text: 'Hour of Day' },
    },
    yaxis: getYAxisConfig('Average AQI'),
    tooltip: {
      shared: true,
      intersect: false,
      y: { formatter: TOOLTIP_FORMATTERS.aqi }
    },
    markers: { size: 5 }
  });

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Hourly Analysis - {timeRangeDescription}</h2>
      <Chart options={options} series={series} type="line" height={400} />
    </div>
  );
};

export default HourlyChart; 