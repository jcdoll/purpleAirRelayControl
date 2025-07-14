import React from 'react';
import styles from './SummaryCards.module.css';
import { getAQIClass } from '../../utils/aqiUtils';

// Create CSS class mapper that uses the centralized AQI classification
const getAQICSSClass = (aqiValue) => {
  const baseClass = getAQIClass(aqiValue);
  
  // Map AQI utility classes to CSS module classes
  const classMap = {
    'aqi-good': styles.aqiGood,
    'aqi-moderate': styles.aqiModerate,
    'aqi-unhealthy-sensitive': styles.aqiUnhealthySensitive,
    'aqi-unhealthy': styles.aqiUnhealthy,
    'aqi-very-unhealthy': styles.aqiVeryUnhealthy,
    'aqi-hazardous': styles.aqiHazardous
  };
  
  return classMap[baseClass] || '';
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
        <div className={`${styles.cardValue} ${getAQICSSClass(parseFloat(summary.indoorAvg || 0))}`}>
          {summary.indoorAvg}
        </div>
        <div className={styles.cardLabel}>AQI</div>
      </div>
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Outdoor Average</h3>
        <div className={`${styles.cardValue} ${getAQICSSClass(parseFloat(summary.outdoorAvg || 0))}`}>
          {summary.outdoorAvg}
        </div>
        <div className={styles.cardLabel}>AQI</div>
      </div>
    </div>
  );
};

export default SummaryCards; 