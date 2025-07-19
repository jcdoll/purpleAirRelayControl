import React from 'react';
import styles from './ColorLegend.module.css';
import { AQI_LEGEND_ITEMS } from '../../constants/app';

const ColorLegend = ({ items, includeNoData = true }) => {
  const legendItems = items 
    ? items 
    : (includeNoData ? AQI_LEGEND_ITEMS : AQI_LEGEND_ITEMS.slice(1)); // Use provided items or fall back to AQI items

  return (
    <div className={styles.colorLegend}>
      {legendItems.map((item, index) => (
        <div key={index} className={styles.legendItem}>
          <div 
            className={styles.legendColor} 
            style={{ 
              backgroundColor: item.color,
              border: item.border || 'none'
            }}
          ></div>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
};

export default ColorLegend; 