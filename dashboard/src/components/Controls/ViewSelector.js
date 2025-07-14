import React from 'react';

const ViewSelector = ({ selectedView, onViewChange }) => {
  return (
    <div className="view-selector">
      <button 
        className={selectedView === 'heatmap' ? 'active' : ''}
        onClick={() => onViewChange('heatmap')}
      >
        Recent
      </button>
      <button 
        className={selectedView === 'hourly' ? 'active' : ''}
        onClick={() => onViewChange('hourly')}
      >
        Hourly Analysis
      </button>
      <button 
        className={selectedView === 'timeline' ? 'active' : ''}
        onClick={() => onViewChange('timeline')}
      >
        Timeline
      </button>
      <button 
        className={selectedView === 'correlation' ? 'active' : ''}
        onClick={() => onViewChange('correlation')}
      >
        Correlation
      </button>
      <button 
        className={selectedView === 'annual-heatmap' ? 'active' : ''}
        onClick={() => onViewChange('annual-heatmap')}
      >
        Annual
      </button>
    </div>
  );
};

export default ViewSelector; 