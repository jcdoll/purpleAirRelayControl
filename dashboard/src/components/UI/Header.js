import React from 'react';

const Header = ({ lastUpdate, onRefresh }) => {
  return (
    <header>
      <div className="header-content">
        <div className="header-text">
          <h1>🏠 Air Quality Dashboard</h1>
          <p className="last-update">Last updated: {lastUpdate.toLocaleString()}</p>
        </div>
        <div className="header-controls">
          <button onClick={onRefresh} className="refresh-btn refresh-btn-header">
            🔄 Refresh
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header; 