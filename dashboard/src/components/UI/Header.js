import React from 'react';

const Header = ({ dataPointsCount, timeRangeDescription, lastUpdate, onRefresh }) => {
  return (
    <header>
      <div className="header-content">
        <div className="header-text">
          <h1>🏠 Air Quality Pattern Explorer</h1>
          <p>
            Analyzing {dataPointsCount?.toLocaleString()} measurements from PurpleAir sensor ({timeRangeDescription})
          </p>
          <p className="last-update">Last updated: {lastUpdate.toLocaleString()}</p>
        </div>
        <button onClick={onRefresh} className="refresh-btn refresh-btn-header">
          🔄 Refresh
        </button>
      </div>
    </header>
  );
};

export default Header; 