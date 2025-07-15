import React from 'react';
import Chart from 'react-apexcharts';
import { getScatterOptions, getYAxisConfig, ANIMATION_DISABLED } from '../../utils/chartConfigUtils';
import { createScatterSeries } from '../../utils/seriesCreators';
import { CHART_CONSTANTS } from '../../constants/app';
import styles from './Chart.module.css';

const CorrelationChart = ({ data, timeRangeDescription, isVisible }) => {
  const series = [createScatterSeries(data, 'Indoor vs Outdoor AQI')];
  
  const options = getScatterOptions({
    chart: { 
      height: CHART_CONSTANTS.DEFAULT_CHART_HEIGHT,
      animations: ANIMATION_DISABLED
    },
    xaxis: getYAxisConfig('Outdoor AQI'),
    yaxis: getYAxisConfig('Indoor AQI')
  });

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Indoor vs Outdoor AQI Correlation - {timeRangeDescription}</h2>
      <Chart options={options} series={series} type="scatter" height={CHART_CONSTANTS.DEFAULT_CHART_HEIGHT} />
    </div>
  );
};

export default CorrelationChart; 