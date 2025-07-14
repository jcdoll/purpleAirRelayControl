import React from 'react';
import styles from './ColorLegend.module.css';
import { AQI_LEGEND_ITEMS } from '../../constants/app';

const ColorLegend = ({ includeNoData = true }) => {
  const legendItems = includeNoData 
    ? AQI_LEGEND_ITEMS 
    : AQI_LEGEND_ITEMS.slice(1); // Skip "No Data" item

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