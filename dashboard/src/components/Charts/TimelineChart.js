import React from 'react';
import Plot from 'react-plotly.js';

const TimelineChart = ({ data, timeRangeDescription }) => {
  return (
    <div>
      <h2>Timeline - {timeRangeDescription}</h2>
      <Plot
        data={data}
        layout={{
          xaxis: { 
            title: 'Time',
            rangeslider: { visible: true }
          },
          yaxis: { title: 'AQI' },
          showlegend: true,
          legend: { x: 0.1, y: 0.9 }
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '500px' }}
      />
    </div>
  );
};

export default TimelineChart; 