import React from 'react';
import Chart from 'react-apexcharts';
import { getAnnualHeatmapOptions } from '../../utils/chartConfigUtils';
import { CHART_CONSTANTS, FILTER_EFFICIENCY_COLORS } from '../../constants/app';
import ColorLegend from '../UI/ColorLegend';
import chartStyles from './Chart.module.css';
import styles from './AnnualHeatmapChart.module.css';

const FilterAnnualHeatmapChart = ({ data, selectedYear, aggregation, isVisible }) => {
  // Single source of truth for month positions and labels (same as AQI annual heatmap)
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
  
  // Custom tooltip for filter efficiency (adapted from AQI version)
  const createFilterEfficiencyTooltip = (selectedYear) => {
    return {
      custom: function({ series, seriesIndex, dataPointIndex, w }) {
        try {
          const dataPoint = w.globals.initialSeries[seriesIndex].data[dataPointIndex];
          const text = dataPoint?.text;
          
          if (!text || text.includes('No data')) {
            return '<div class="apexcharts-tooltip-custom">No data</div>';
          }
          
          return `<div class="apexcharts-tooltip-custom">${text}</div>`;
        } catch (e) {
          return '<div class="apexcharts-tooltip-custom">No data</div>';
        }
      }
    };
  };

  // Chart options using the same structure as AQI annual heatmap
  const options = {
    ...getAnnualHeatmapOptions({
      tooltip: createFilterEfficiencyTooltip(selectedYear)
    }),
    xaxis: {
      ...getAnnualHeatmapOptions().xaxis,
      labels: {
        ...getAnnualHeatmapOptions().xaxis.labels,
        formatter: function(value) {
          const weekNum = Math.round(value);
          if (monthTickMap[weekNum]) {
            return monthTickMap[weekNum];
          }
          return '';
        }
      }
    },
    yaxis: {
      reversed: true,
      labels: {
        formatter: function(value) {
          const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
          return days[value] || '';
        },
        style: {
          fontSize: '11px',
          colors: '#666'
        }
      }
    },
    plotOptions: {
      heatmap: {
        ...getAnnualHeatmapOptions().plotOptions.heatmap,
        colorScale: {
          ranges: [
            { from: -1, to: -1, color: FILTER_EFFICIENCY_COLORS.NO_DATA, name: 'No Data' },
            { from: 0, to: 30, color: FILTER_EFFICIENCY_COLORS.POOR, name: 'Poor (0-30%)' },
            { from: 30, to: 50, color: FILTER_EFFICIENCY_COLORS.DECLINING, name: 'Declining (30-50%)' },
            { from: 50, to: 70, color: FILTER_EFFICIENCY_COLORS.MODERATE, name: 'Moderate (50-70%)' },
            { from: 70, to: 85, color: FILTER_EFFICIENCY_COLORS.GOOD, name: 'Good (70-85%)' },
            { from: 85, to: 100, color: FILTER_EFFICIENCY_COLORS.EXCELLENT, name: 'Excellent (85-100%)' }
          ]
        }
      }
    }
  };

  // Filter efficiency legend items
  const filterEfficiencyLegendItems = [
    { color: FILTER_EFFICIENCY_COLORS.NO_DATA, label: 'No Data' },
    { color: FILTER_EFFICIENCY_COLORS.POOR, label: 'Poor (0-30%)' },
    { color: FILTER_EFFICIENCY_COLORS.DECLINING, label: 'Declining (30-50%)' },
    { color: FILTER_EFFICIENCY_COLORS.MODERATE, label: 'Moderate (50-70%)' },
    { color: FILTER_EFFICIENCY_COLORS.GOOD, label: 'Good (70-85%)' },
    { color: FILTER_EFFICIENCY_COLORS.EXCELLENT, label: 'Excellent (85-100%)' }
  ];

  return (
    <div className={`${chartStyles.chartContainer} ${!isVisible ? chartStyles.hidden : ''}`}>
      <h2 className={chartStyles.chartTitle}>
        Filter Efficiency Calendar - {selectedYear} ({aggregation === 'average' ? 'Average' : aggregation === 'median' ? 'Median' : aggregation === 'max' ? 'Maximum' : '95%'})
      </h2>
      
      <ColorLegend items={filterEfficiencyLegendItems} />
      
      <div className={styles.chartWrapper}>
        <Chart 
          options={options} 
          series={data} 
          type="heatmap" 
          height={CHART_CONSTANTS.ANNUAL_HEATMAP_HEIGHT} 
        />
      </div>
    </div>
  );
};

export default FilterAnnualHeatmapChart; 