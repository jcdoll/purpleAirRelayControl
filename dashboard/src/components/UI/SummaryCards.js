import React from 'react';
import styles from './SummaryCards.module.css';
import { getAQIClass } from '../../utils/aqiUtils';

// Create CSS class mapper that uses the centralized AQI classification
const getAQICSSClass = (aqiValue) => {
  if (isNaN(aqiValue)) return '';

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
        <h3 className={styles.cardTitle}>Indoor</h3>
        <div className={`${styles.cardValue} ${getAQICSSClass(parseFloat(summary.indoorLatest || 0))}`}>
          {summary.indoorLatest}
        </div>
        <div className={styles.cardLabel}>Latest AQI</div>
      </div>
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Outdoor</h3>
        <div className={`${styles.cardValue} ${getAQICSSClass(parseFloat(summary.outdoorLatest || 0))}`}>
          {summary.outdoorLatest}
        </div>
        <div className={styles.cardLabel}>Latest AQI</div>
      </div>
    </div>
  );
};

export default SummaryCards; 