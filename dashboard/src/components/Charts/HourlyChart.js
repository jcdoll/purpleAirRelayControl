import React from 'react';
import Plot from 'react-plotly.js';

const HourlyChart = ({ data, timeRangeDescription }) => {
  return (
    <div>
      <h2>Indoor & Outdoor AQI Hourly Pattern Analysis - {timeRangeDescription}</h2>
      <Plot
        data={data}
        layout={{
          xaxis: { title: 'Hour of Day' },
          yaxis: { title: 'Average AQI' },
          showlegend: true,
          barmode: 'group'
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '500px' }}
      />
    </div>
  );
};

export default HourlyChart; 