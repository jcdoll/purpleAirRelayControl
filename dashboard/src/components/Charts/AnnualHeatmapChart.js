import React from 'react';
import Chart from 'react-apexcharts';
import { getHeatmapOptions, createAnnualHeatmapTooltip } from '../../utils/chartConfigUtils';
import { createAnnualHeatmapSeries } from '../../utils/seriesCreators';
import ColorLegend from '../UI/ColorLegend';
import chartStyles from './Chart.module.css';
import styles from './AnnualHeatmapChart.module.css';

const AnnualHeatmapChart = ({ data, selectedYear, aggregation, isVisible }) => {
  const { indoor, outdoor } = createAnnualHeatmapSeries(data);
  
  // Helper function to create chart options (eliminates duplication)
  const createAnnualHeatmapOptions = (type) => {
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
    
    return getHeatmapOptions({
      chart: { 
        height: 250,
        animations: { enabled: false, speed: 0 },
        toolbar: { show: false }
      },
      plotOptions: {
        heatmap: {
          radius: 1,
          useFillColorAsStroke: false,
          distributed: true,
          enableShades: false,
          shadeIntensity: 0,
          colorScale: getHeatmapOptions({}).plotOptions.heatmap.colorScale
        }
      },
      dataLabels: {
        enabled: false
      },
      grid: {
        show: false,
        padding: {
          top: 0,
          right: 0,
          bottom: 0,
          left: 20
        }
      },
      stroke: {
        show: true,
        width: 1,
        color: '#ffffff'
      },
      xaxis: {
        type: 'numeric',
        position: 'bottom',
        min: 0,
        max: 51,
        tickAmount: 'dataPoints',
        labels: {
          formatter: function(value) {
            const weekNum = Math.round(value);
            // Only show labels for weeks that are in our monthTickMap
            if (monthTickMap[weekNum]) {
              return monthTickMap[weekNum];
            }
            return '';
          },
          show: true,
          rotate: 0,
          offsetY: 0,
          hideOverlappingLabels: false,
          showDuplicates: false
        }
      },
      yaxis: {
        reversed: true,
        labels: { 
          formatter: function(value) { 
            return value; 
          } 
        }
      },
      tooltip: createAnnualHeatmapTooltip(type, selectedYear)
    });
  };
  
  const indoorOptions = createAnnualHeatmapOptions('Indoor');
  const outdoorOptions = createAnnualHeatmapOptions('Outdoor');

  return (
    <div className={`${chartStyles.chartContainer} ${!isVisible ? chartStyles.hidden : ''}`}>
      <h2 className={chartStyles.chartTitle}>Indoor & Outdoor AQI Annual Calendar {selectedYear} - Daily {aggregation === 'average' ? 'Average' : 'Maximum'}</h2>
      <ColorLegend />
      <div className={chartStyles.chartSection}>
        <h3 className={chartStyles.chartSectionTitle}>Indoor AQI</h3>
        <div className={styles.annualHeatmap}>
          <Chart options={indoorOptions} series={indoor} type="heatmap" height={250} />
        </div>
      </div>
      <div className={chartStyles.chartSection}>
        <h3 className={chartStyles.chartSectionTitle}>Outdoor AQI</h3>
        <div className={styles.annualHeatmap}>
          <Chart options={outdoorOptions} series={outdoor} type="heatmap" height={250} />
        </div>
      </div>
    </div>
  );
};

export default AnnualHeatmapChart; 