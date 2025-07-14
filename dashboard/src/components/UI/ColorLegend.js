import React from 'react';
import { AQI_LEGEND_ITEMS } from '../../constants/app';

const ColorLegend = ({ includeNoData = false }) => {
  const legendItems = includeNoData 
    ? AQI_LEGEND_ITEMS 
    : AQI_LEGEND_ITEMS.slice(1); // Skip "No Data" item

  return (
    <div className="color-legend">
      {legendItems.map((item, index) => (
        <div key={index} className="legend-item">
          <div 
            className="legend-color" 
            style={{ backgroundColor: item.color }}
          ></div>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
};

export default ColorLegend; 