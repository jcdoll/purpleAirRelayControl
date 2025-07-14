import React from 'react';
import Plot from 'react-plotly.js';

const AnnualHeatmapChart = ({ data, selectedYear, aggregation }) => {
  return (
    <div>
      <h2>Indoor & Outdoor AQI Annual Calendar {selectedYear} - Daily {aggregation === 'average' ? 'Average' : 'Maximum'}</h2>
      
      {/* Manual color legend */}
      <div className="color-legend">
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#f0f0f0'}}></div>
          <span>No Data</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#00E400'}}></div>
          <span>Good (0-50)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FFDC00'}}></div>
          <span>Moderate (51-100)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FF7E00'}}></div>
          <span>Sensitive (101-150)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
          <span>Unhealthy (151-200)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#8F3F97'}}></div>
          <span>Very Unhealthy (201-300)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{backgroundColor: '#7E0023'}}></div>
          <span>Hazardous (301-500)</span>
        </div>
      </div>
      
      <Plot
        data={data}
        layout={{
          xaxis: { 
            title: '',
            showticklabels: true,
            tickangle: 0,
            tickmode: 'array',
            tickvals: [0, 4, 13, 22, 30, 39, 48], // Approximate month starts
            ticktext: ['Jan', 'Feb', 'Apr', 'Jun', 'Aug', 'Oct', 'Dec'],
            showgrid: false,
            zeroline: false,
            side: 'top',
            range: [-0.5, 51.5],
            domain: [0, 1]
          },
          yaxis: { 
            title: '',
            tickmode: 'array',
            tickvals: [0, 1, 2, 3, 4, 5, 6],
            ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            showgrid: false,
            zeroline: false,
            autorange: 'reversed',
            side: 'left',
            domain: [0.55, 1]
          },
          yaxis2: { 
            title: '',
            tickmode: 'array',
            tickvals: [0, 1, 2, 3, 4, 5, 6],
            ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            showgrid: false,
            zeroline: false,
            autorange: 'reversed',
            side: 'left',
            domain: [0, 0.45]
          },
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          margin: { l: 50, r: 20, t: 50, b: 20 },
          height: 400,
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
        style={{ width: '100%', height: '500px' }}
      />
    </div>
  );
};

export default AnnualHeatmapChart; 