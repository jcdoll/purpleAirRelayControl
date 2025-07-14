import React from 'react';
import styles from './Header.module.css';

const Header = ({ lastUpdate, onRefresh }) => {
  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <div className={styles.headerText}>
          <h1 className={styles.title}>🏠 Air Quality Dashboard</h1>
          <p className={styles.lastUpdate}>Last updated: {lastUpdate.toLocaleString()}</p>
        </div>
        <div className={styles.headerControls}>
          <button onClick={onRefresh} className={`${styles.refreshBtn} ${styles.refreshBtnHeader}`}>
            🔄 Refresh
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header; 