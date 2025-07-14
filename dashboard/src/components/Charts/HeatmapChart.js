import React from 'react';
import Plot from 'react-plotly.js';

const HeatmapChart = ({ data, timeRangeDescription }) => {
  return (
    <div>
      <h2>Indoor & Outdoor AQI Levels by Hour - {timeRangeDescription}</h2>
      
      {/* Manual color legend */}
      <div className="color-legend">
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#f0f0f0'}}></div>
          <span>No Data</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FFFFFF', border: '1px solid #ccc'}}></div>
          <span>Clear (=0)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#00E400'}}></div>
          <span>Good (&lt;50)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FFDC00'}}></div>
          <span>Moderate (&lt;100)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FF7E00'}}></div>
          <span>Sensitive (&lt;150)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
          <span>Unhealthy (&lt;200)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#8F3F97'}}></div>
          <span>Very Unhealthy (&lt;300)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#7E0023'}}></div>
          <span>Hazardous (&gt;300)</span>
        </div>
      </div>
      
      <Plot
        data={data}
        layout={{
          xaxis: { 
            title: 'Hour of Day', 
            tickmode: window.innerWidth <= 768 ? 'array' : 'linear',
            tickvals: window.innerWidth <= 768 ? [0, 6, 12, 18] : undefined,
            ticktext: window.innerWidth <= 768 ? ['0:00', '6:00', '12:00', '18:00'] : undefined,
            domain: [0, 1],
            showgrid: false,
            zeroline: false
          },
          yaxis: { 
            title: 'Indoor AQI', 
            tickmode: 'auto', 
            nticks: 10,
            domain: [0.55, 1],
            showgrid: false,
            zeroline: false
          },
          yaxis2: { 
            title: 'Outdoor AQI', 
            tickmode: 'auto', 
            nticks: 10,
            domain: [0, 0.45],
            showgrid: false,
            zeroline: false
          },
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          margin: { l: 100, r: 50, t: 50, b: 50 },
          annotations: [
            {
              text: 'Indoor AQI',
              x: -0.1,
              y: 0.775,
              xref: 'paper',
              yref: 'paper',
              xanchor: 'center',
              yanchor: 'middle',
              textangle: -90,
              font: { size: 14 },
              showarrow: false
            },
            {
              text: 'Outdoor AQI',
              x: -0.1,
              y: 0.225,
              xref: 'paper',
              yref: 'paper',
              xanchor: 'center',
              yanchor: 'middle',
              textangle: -90,
              font: { size: 14 },
              showarrow: false
            }
          ]
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '800px' }}
      />
    </div>
  );
};

export default HeatmapChart; 