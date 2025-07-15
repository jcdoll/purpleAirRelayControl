import React from 'react';
import Chart from 'react-apexcharts';
import { getAnnualHeatmapOptions, createAnnualHeatmapTooltip } from '../../utils/chartConfigUtils';
import { createAnnualHeatmapSeries } from '../../utils/seriesCreators';
import ColorLegend from '../UI/ColorLegend';
import chartStyles from './Chart.module.css';
import styles from './AnnualHeatmapChart.module.css';

const AnnualHeatmapChart = ({ data, selectedYear, aggregation, isVisible }) => {
  const { indoor, outdoor } = createAnnualHeatmapSeries(data);
  
  // Single source of truth for month positions and labels
  const monthTickMap = {
    0: 'Jan',
    4: 'Feb', 
    8: 'Mar',
    13: 'Apr',
    17: 'May',
    21: 'Jun',
    26: 'Jul',
    30: 'Aug',
    35: 'Sep',
    39: 'Oct',
    43: 'Nov',
    47: 'Dec'
  };
  
  // Generic chart options creator
  const createAnnualHeatmapOptions = (type) => {
    const baseOptions = getAnnualHeatmapOptions({
      tooltip: createAnnualHeatmapTooltip(type, selectedYear)
    });
    
    return {
      ...baseOptions,
      xaxis: {
        ...baseOptions.xaxis,
        labels: {
          ...baseOptions.xaxis.labels,
          formatter: function(value) {
            const weekNum = Math.round(value);
            if (monthTickMap[weekNum]) {
              return monthTickMap[weekNum];
            }
            return '';
          }
        }
      }
    };
  };
  
  // Generic chart section renderer
  const renderChartSection = (dataType, series) => {
    const options = createAnnualHeatmapOptions(dataType);
    
    return (
      <div className={chartStyles.chartSection}>
        <h3 className={chartStyles.chartSectionTitle}>{dataType} AQI</h3>
        <div className={styles.annualHeatmap}>
          <Chart options={options} series={series} type="heatmap" height={250} />
        </div>
      </div>
    );
  };

  return (
    <div className={`${chartStyles.chartContainer} ${!isVisible ? chartStyles.hidden : ''}`}>
      <h2 className={chartStyles.chartTitle}>Indoor & Outdoor AQI Annual Calendar {selectedYear} - Daily {aggregation === 'average' ? 'Average' : 'Maximum'}</h2>
      <ColorLegend />
      {renderChartSection('Indoor', indoor)}
      {renderChartSection('Outdoor', outdoor)}
    </div>
  );
};

export default AnnualHeatmapChart; 