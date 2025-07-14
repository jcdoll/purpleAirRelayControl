import React from 'react';
import Plot from 'react-plotly.js';

// TODO: Switch from Plotly to a different charting library that supports proper cell borders
// Plotly heatmaps don't have native border/stroke properties for individual cells

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
            title: '', 
            showticklabels: true,
            tickmode: 'array',
            tickvals: [0, 4, 8, 13, 17, 21, 26, 30, 35, 39, 43, 47],
            ticktext: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            fixedrange: true,
            range: [-0.5, 51.5],
            showgrid: false,
            zeroline: false,
            scaleanchor: 'y',
            scaleratio: 1
          },
          xaxis2: { 
            title: '', 
            showticklabels: true,
            tickmode: 'array',
            tickvals: [0, 4, 8, 13, 17, 21, 26, 30, 35, 39, 43, 47],
            ticktext: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            fixedrange: true,
            range: [-0.5, 51.5],
            showgrid: false,
            zeroline: false,
            scaleanchor: 'y2',
            scaleratio: 1,
            anchor: 'y2',
            side: 'bottom'
          },
          yaxis: { 
            title: '',
            tickmode: 'array',
            tickvals: [0, 1, 2, 3, 4, 5, 6],
            ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            fixedrange: true,
            autorange: 'reversed',
            showgrid: false,
            zeroline: false,
            domain: [0.52, 1.0]
          },
          yaxis2: { 
            title: '',
            tickmode: 'array',
            tickvals: [0, 1, 2, 3, 4, 5, 6],
            ticktext: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            fixedrange: true,
            autorange: 'reversed',
            domain: [0, 0.48],
            showgrid: false,
            zeroline: false,
            scaleanchor: 'y',
            scaleratio: 1
          },
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          margin: { l: 120, r: 20, t: 80, b: 80 },
          annotations: [
            {
              text: 'Indoor AQI',
              x: 0,
              y: 1.03,
              xref: 'paper',
              yref: 'paper',
              xanchor: 'left',
              yanchor: 'bottom',
              font: { size: 16, weight: 'bold' },
              showarrow: false
            },
            {
              text: 'Outdoor AQI',
              x: 0,
              y: 0.50,
              xref: 'paper',
              yref: 'paper',
              xanchor: 'left',
              yanchor: 'bottom',
              font: { size: 16, weight: 'bold' },
              showarrow: false
            }
          ]
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '600px' }}
      />
    </div>
  );
};

export default AnnualHeatmapChart; 