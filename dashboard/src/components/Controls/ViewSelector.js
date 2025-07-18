import React from 'react';
import styles from './ViewSelector.module.css';

const ViewSelector = ({ selectedView, onViewChange }) => {
  return (
    <div className={styles.viewSelector}>
      <button 
        className={selectedView === 'timeline' ? styles.active : ''}
        onClick={() => onViewChange('timeline')}
      >
        Timeline
      </button>
      <button 
        className={selectedView === 'heatmap' ? styles.active : ''}
        onClick={() => onViewChange('heatmap')}
      >
        Recent
      </button>
      <button 
        className={selectedView === 'annual-heatmap' ? styles.active : ''}
        onClick={() => onViewChange('annual-heatmap')}
      >
        Annual
      </button>
      <button 
        className={selectedView === 'hourly' ? styles.active : ''}
        onClick={() => onViewChange('hourly')}
      >
        Hourly Patterns
      </button>
      <button 
        className={selectedView === 'correlation' ? styles.active : ''}
        onClick={() => onViewChange('correlation')}
      >
        Correlation
      </button>
    </div>
  );
};

export default ViewSelector; 