import React from 'react';
import Plot from 'react-plotly.js';

const CorrelationChart = ({ data, timeRangeDescription }) => {
  return (
    <div>
      <h2>Indoor vs Outdoor Correlation - {timeRangeDescription}</h2>
      <Plot
        data={[data]}
        layout={{
          xaxis: { title: 'Outdoor AQI' },
          yaxis: { title: 'Indoor AQI' },
          showlegend: false
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '600px' }}
      />
    </div>
  );
};

export default CorrelationChart; 