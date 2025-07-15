import React from 'react';
import styles from './LoadingError.module.css';

/**
 * Displays loading spinner or error message
 * @param {boolean} loading - Whether data is currently loading
 * @param {string} error - Error message if any
 * @param {Function} onRetry - Function to call when retry button is clicked
 * @returns {JSX.Element|null} Loading spinner, error message, or null
 */
const LoadingError = ({ loading, error, onRetry }) => {
  if (loading) {
    return (
      <div className={styles.loading}>
        <h2>Loading air quality data...</h2>
        <div className={styles.spinner}></div>
        <p>Fetching data from Google Sheets...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h2>Error loading data</h2>
        <p>{error}</p>
        <p>Make sure your Google Sheet is published to web as CSV</p>
        <button onClick={onRetry}>Retry</button>
      </div>
    );
  }

  return null;
};

export default LoadingError;