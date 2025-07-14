import React from 'react';
import styles from './SummaryCards.module.css';

// Function to get AQI CSS class based on AQI value
const getAQIClass = (aqiValue) => {
  if (aqiValue <= 50) return styles.aqiGood;
  if (aqiValue <= 100) return styles.aqiModerate;
  if (aqiValue <= 150) return styles.aqiUnhealthySensitive;
  if (aqiValue <= 200) return styles.aqiUnhealthy;
  if (aqiValue <= 300) return styles.aqiVeryUnhealthy;
  return styles.aqiHazardous;
};

const SummaryCards = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className={styles.summaryCards}>
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Peak Hour</h3>
        <div className={styles.cardValue}>{summary.peakHour.hour}</div>
        <div className={styles.cardLabel}>{summary.peakHour.aqi} AQI avg</div>
      </div>
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Indoor Average</h3>
        <div className={`${styles.cardValue} ${getAQIClass(parseFloat(summary.indoorAvg || 0))}`}>
          {summary.indoorAvg}
        </div>
        <div className={styles.cardLabel}>AQI</div>
      </div>
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Outdoor Average</h3>
        <div className={`${styles.cardValue} ${getAQIClass(parseFloat(summary.outdoorAvg || 0))}`}>
          {summary.outdoorAvg}
        </div>
        <div className={styles.cardLabel}>AQI</div>
      </div>
    </div>
  );
};

export default SummaryCards; 