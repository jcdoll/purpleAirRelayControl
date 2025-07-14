import React from 'react';
import Chart from 'react-apexcharts';
import ColorLegend from '../UI/ColorLegend';
import styles from './Chart.module.css';

const BaseChart = ({ 
  title, 
  isVisible, 
  children, 
  showColorLegend = false,
  className = '',
  ...chartProps 
}) => {
  return (
    <div className={`${styles.chartContainer} ${!isVisible ? styles.hidden : ''} ${className}`}>
      <h2 className={styles.chartTitle}>{title}</h2>
      {showColorLegend && <ColorLegend />}
      {children}
      <Chart {...chartProps} />
    </div>
  );
};

export default BaseChart; 