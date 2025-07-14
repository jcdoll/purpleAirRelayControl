import React from 'react';

// Function to get AQI CSS class based on AQI value
const getAQIClass = (aqiValue) => {
  if (aqiValue <= 50) return 'aqi-good';
  if (aqiValue <= 100) return 'aqi-moderate';
  if (aqiValue <= 150) return 'aqi-unhealthy-sensitive';
  if (aqiValue <= 200) return 'aqi-unhealthy';
  if (aqiValue <= 300) return 'aqi-very-unhealthy';
  return 'aqi-hazardous';
};

const SummaryCards = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="summary-cards">
      <div className="card">
        <h3>Peak Hour</h3>
        <div className="value">{summary.peakHour.hour}</div>
        <div className="label">{summary.peakHour.aqi} AQI avg</div>
      </div>
      <div className="card">
        <h3>Indoor Average</h3>
        <div className={`value ${getAQIClass(parseFloat(summary.indoorAvg || 0))}`}>
          {summary.indoorAvg}
        </div>
        <div className="label">AQI</div>
      </div>
      <div className="card">
        <h3>Outdoor Average</h3>
        <div className={`value ${getAQIClass(parseFloat(summary.outdoorAvg || 0))}`}>
          {summary.outdoorAvg}
        </div>
        <div className="label">AQI</div>
      </div>
    </div>
  );
};

export default SummaryCards; 