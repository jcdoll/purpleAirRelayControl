import React from 'react';
import Chart from 'react-apexcharts';
import { getLineChartOptions, getXAxisConfig, getYAxisConfig, TOOLTIP_FORMATTERS, ANIMATION_DISABLED, TOOLBAR_DISABLED } from '../../utils/chartConfigUtils';
import { createIndoorOutdoorSeries } from '../../utils/seriesCreators';
import { CHART_CONSTANTS } from '../../constants/app';
import styles from './Chart.module.css';

const TimelineChart = ({ data, timeRangeDescription, isVisible }) => {
  const series = createIndoorOutdoorSeries(data);
  
  const options = getLineChartOptions({
    chart: { 
      height: CHART_CONSTANTS.TIMELINE_CHART_HEIGHT,
      animations: ANIMATION_DISABLED,
      toolbar: TOOLBAR_DISABLED
    },
    xaxis: {
      ...getXAxisConfig('Time', 'datetime'),
      labels: { datetimeUTC: false }
    },
    yaxis: getYAxisConfig('AQI'),
    tooltip: {
      shared: true,
      intersect: false,
      x: { format: TOOLTIP_FORMATTERS.datetime },
      y: { formatter: TOOLTIP_FORMATTERS.aqi }
    }
  });

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Timeline - {timeRangeDescription}</h2>
      <Chart options={options} series={series} type="line" height={CHART_CONSTANTS.TIMELINE_CHART_HEIGHT} />
    </div>
  );
};

export default TimelineChart; 