import React from 'react';
import Chart from 'react-apexcharts';
import { getHeatmapOptions, createHeatmapTooltip } from '../../utils/chartConfigUtils';
import { createHeatmapSeries } from '../../utils/seriesCreators';
import ColorLegend from '../UI/ColorLegend';
import styles from './Chart.module.css';

const RecentHeatmapChart = ({ data, timeRangeDescription, isVisible, dateRange }) => {
  const { indoor, outdoor } = createHeatmapSeries(data);
  
  const indoorOptions = getHeatmapOptions({
    tooltip: createHeatmapTooltip('Indoor'),
    dateRange: dateRange
  });
  
  const outdoorOptions = getHeatmapOptions({
    tooltip: createHeatmapTooltip('Outdoor'),
    dateRange: dateRange
  });

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Indoor & Outdoor AQI Levels by Hour - {timeRangeDescription}</h2>
      <ColorLegend />
      <div className={styles.chartSection}>
        <h3 className={styles.chartSectionTitle}>Indoor AQI</h3>
        <Chart options={indoorOptions} series={indoor} type="heatmap" height={350} />
      </div>
      <div className={styles.chartSection}>
        <h3 className={styles.chartSectionTitle}>Outdoor AQI</h3>
        <Chart options={outdoorOptions} series={outdoor} type="heatmap" height={350} />
      </div>
    </div>
  );
};

export default RecentHeatmapChart; 