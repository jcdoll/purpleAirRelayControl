import React from 'react';
import Chart from 'react-apexcharts';
import { getScatterOptions, getYAxisConfig, ANIMATION_DISABLED } from '../../utils/chartConfigUtils';
import { createScatterSeries } from '../../utils/seriesCreators';
import styles from './Chart.module.css';

const CorrelationChart = ({ data, timeRangeDescription, isVisible }) => {
  const series = [createScatterSeries(data, 'Indoor vs Outdoor AQI')];
  
  const options = getScatterOptions({
    chart: { 
      height: 400,
      animations: ANIMATION_DISABLED
    },
    xaxis: getYAxisConfig('Outdoor AQI'),
    yaxis: getYAxisConfig('Indoor AQI')
  });

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Indoor vs Outdoor AQI Correlation - {timeRangeDescription}</h2>
      <Chart options={options} series={series} type="scatter" height={400} />
    </div>
  );
};

export default CorrelationChart; 