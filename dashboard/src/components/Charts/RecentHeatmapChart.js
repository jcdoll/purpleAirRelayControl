import React from 'react';
import Chart from 'react-apexcharts';
import { getRecentHeatmapOptions, createHeatmapTooltip } from '../../utils/chartConfigUtils';
import { createHeatmapSeries } from '../../utils/seriesCreators';
import { CHART_CONSTANTS } from '../../constants/app';
import ColorLegend from '../UI/ColorLegend';
import styles from './Chart.module.css';

const RecentHeatmapChart = ({ data, timeRangeDescription, isVisible, dateRange }) => {
  const { indoor, outdoor } = createHeatmapSeries(data);
  
  // Generic chart section renderer
  const renderChartSection = (dataType, series) => {
    const options = getRecentHeatmapOptions({
      tooltip: createHeatmapTooltip(dataType),
      dateRange: dateRange
    });
    
    return (
      <div className={styles.chartSection}>
        <h3 className={styles.chartSectionTitle}>{dataType} AQI</h3>
        <Chart options={options} series={series} type="heatmap" height={CHART_CONSTANTS.HEATMAP_HEIGHT} />
      </div>
    );
  };

  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''}`}>
      <h2 className={styles.chartTitle}>Indoor & Outdoor AQI Levels by Hour - {timeRangeDescription}</h2>
      <ColorLegend />
      {renderChartSection('Indoor', indoor)}
      {renderChartSection('Outdoor', outdoor)}
    </div>
  );
};

export default RecentHeatmapChart; 