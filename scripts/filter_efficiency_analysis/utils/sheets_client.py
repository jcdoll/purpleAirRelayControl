"""
Google Sheets API client for filter efficiency analysis.

This module provides functions to read sensor data from Google Sheets
and write analysis results back to the same or different sheet.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

try:
    # Request class available for future authentication needs
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.errors import HttpError  # type: ignore

    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SheetsClient:
    """
    Google Sheets API client for reading and writing filter efficiency data.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Sheets client.

        Args:
            config: Configuration dictionary containing Google Sheets settings
        """
        if not SHEETS_AVAILABLE:
            raise ImportError(
                "Google Sheets dependencies not available. "
                "Install with: pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )

        self.config = config['google_sheets']
        self.logger = logging.getLogger(__name__)

        # Initialize credentials and service
        self.credentials = None
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Sheets API service with credentials."""
        try:
            # Load credentials from environment variable or file
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')

            if credentials_json:
                # Load from environment variable (for GitHub Actions)
                credentials_info = json.loads(credentials_json)
                self.credentials = Credentials.from_service_account_info(
                    credentials_info, scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                # Load from file (for local development)
                credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
                if os.path.exists(credentials_file):
                    self.credentials = Credentials.from_service_account_file(
                        credentials_file, scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                else:
                    raise FileNotFoundError(
                        "Google Sheets credentials not found. "
                        "Set GOOGLE_SHEETS_CREDENTIALS environment variable or "
                        "place credentials.json file in working directory."
                    )

            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.logger.info("Google Sheets API service initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise

    def read_sensor_data(self, days_back: int = 0, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Read sensor data from Google Sheets.

        Args:
            days_back: Number of days of historical data to read (0 = all available data)
            sheet_name: Sheet name (uses config default if None)

        Returns:
            DataFrame with sensor data
        """
        if sheet_name is None:
            sheet_name = self.config['data_sheet']

        spreadsheet_id = self.config['spreadsheet_id']
        max_rows = self.config['max_rows']

        # Calculate date range
        end_date = datetime.now()
        if days_back <= 0:
            # Read all available data - use a very old start date
            start_date = datetime(2020, 1, 1)  # Far enough back to capture all sensor data
        else:
            start_date = end_date - timedelta(days=days_back)

        try:
            # Ensure service is initialized
            if self.service is None:
                raise RuntimeError("Google Sheets service not initialized")

            # Read data from sheet
            range_name = f"{sheet_name}!A1:{chr(ord('A') + 10)}{max_rows}"  # A1:K{max_rows}

            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

            values = result.get('values', [])

            if not values:
                raise ValueError("No data found in the specified sheet range")

            # Convert to DataFrame
            headers = values[0]
            data_rows = values[1:]

            df = pd.DataFrame(data_rows, columns=headers)

            # Clean up the data
            df = self._clean_sensor_data(df, start_date, end_date)

            self.logger.info(f"Read {len(df)} rows of sensor data from sheet '{sheet_name}'")
            return df

        except HttpError as e:
            self.logger.error(f"HTTP error reading from Google Sheets: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading sensor data: {e}")
            raise

    def _clean_sensor_data(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Clean and filter sensor data.

        Args:
            df: Raw dataframe from sheets
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Cleaned dataframe
        """
        # Make a copy to avoid modifying original
        df = df.copy()

        # Use ONLY the configured column names - no fallbacks
        config_columns = self.config.get('columns', {})
        column_mapping = {}

        # Map exactly what's configured
        if 'timestamp' in config_columns:
            column_mapping[config_columns['timestamp']] = 'timestamp'
        if 'indoor_aqi' in config_columns:
            column_mapping[config_columns['indoor_aqi']] = 'indoor_aqi'
        if 'outdoor_aqi' in config_columns:
            column_mapping[config_columns['outdoor_aqi']] = 'outdoor_aqi'

        # Rename columns based on config only
        df = df.rename(columns=column_mapping)

        # Ensure we have required columns
        required_cols = ['timestamp', 'indoor_aqi', 'outdoor_aqi']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            available_cols = list(df.columns)
            raise ValueError(
                f"Missing required columns: {missing_cols}. "
                f"Available columns: {available_cols}. "
                f"Please update column mapping in config or rename columns in your sheet."
            )

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # Convert AQI columns to numeric
        df['indoor_aqi'] = pd.to_numeric(df['indoor_aqi'], errors='coerce')
        df['outdoor_aqi'] = pd.to_numeric(df['outdoor_aqi'], errors='coerce')

        # Remove rows with invalid timestamps or all NaN AQI values
        df = df.dropna(subset=['timestamp'])
        df = df.dropna(subset=['indoor_aqi', 'outdoor_aqi'], how='all')

        # Filter by date range
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        df = df.loc[mask].copy()

        # Remove duplicates (keep last)
        df = df.drop_duplicates(subset=['timestamp'], keep='last')

        self.logger.info(f"Cleaned data: {len(df)} valid records between {start_date} and {end_date}")
        return df

    def write_analysis_results(self, results: Dict[str, Any], sheet_name: Optional[str] = None) -> bool:
        """
        Write filter efficiency analysis results to Google Sheets.
        This clears the existing sheet and writes fresh time-series data.

        Args:
            results: Analysis results dictionary containing time-series data
            sheet_name: Sheet name for results (uses config default if None)

        Returns:
            True if successful, False otherwise
        """
        if sheet_name is None:
            sheet_name = self.config['results_sheet']

        # Ensure we have a valid sheet name
        assert sheet_name is not None

        spreadsheet_id = self.config['spreadsheet_id']

        try:
            # Ensure service is initialized
            if self.service is None:
                raise RuntimeError("Google Sheets service not initialized")

            # Check if results sheet exists, create if not
            self._ensure_results_sheet_exists(sheet_name)

            # Prepare time-series data for writing
            time_series_data = self._prepare_time_series_data(results)

            if not time_series_data:
                self.logger.warning("No time-series data to write")
                return False

            # Prepare headers and data together
            headers = [
                'Timestamp',
                'Indoor PM2.5',
                'Outdoor PM2.5',
                'Ratio',
                'Estimated Filter Efficiency (%)',
                'Efficiency Uncertainty (%)',
                'Predicted Indoor PM2.5',
                'Prediction Error',
            ]

            # Combine headers with data
            all_data = [headers] + time_series_data

            # Clear the entire sheet first to remove any old columns
            clear_range = f"{sheet_name}!A:Z"  # Clear all columns

            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=clear_range,
            ).execute()

            # Write fresh data with correct headers (8 columns only)
            range_name = f"{sheet_name}!A:H"  # 8 columns: A through H

            body = {'values': all_data}

            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body,
            ).execute()

            self.logger.info(
                f"Successfully wrote headers and {len(time_series_data)} time-series records to sheet '{sheet_name}' (sheet cleared and regenerated)"
            )
            return True

        except HttpError as e:
            self.logger.error(f"HTTP error writing to Google Sheets: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error writing analysis results: {e}")
            return False

    def _prepare_time_series_data(self, results: Dict[str, Any]) -> List[List[str]]:
        """
        Prepare time-series analysis results for writing to sheets.

        Args:
            results: Analysis results dictionary containing state_history

        Returns:
            List of rows, each containing values for the 8 columns
        """
        # Extract state history from the tracker
        tracker = results.get('tracker')
        if tracker is None or not hasattr(tracker, 'state_history'):
            self.logger.error("No tracker or state_history found in results")
            return []

        state_history = tracker.state_history
        if not state_history:
            self.logger.warning("State history is empty")
            return []

        time_series_rows = []

        for record in state_history:
            # Calculate efficiency uncertainty from tracker covariance
            if hasattr(tracker, 'covariance'):
                efficiency_uncertainty = float(np.sqrt(tracker.covariance) * 100)  # Convert to percentage
            else:
                efficiency_uncertainty = ''

            # Calculate prediction error
            predicted_indoor = record.get('predicted_indoor', 0.0)
            actual_indoor = record.get('actual_indoor', 0.0)
            prediction_error = float(actual_indoor - predicted_indoor)

            # Calculate I/O ratio
            outdoor_pm25 = record.get('outdoor', 0.0)
            indoor_pm25 = record.get('actual_indoor', 0.0)
            ratio = float(indoor_pm25 / outdoor_pm25) if outdoor_pm25 > 0 else ''

            # Format timestamp
            timestamp = record.get('timestamp')
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)

            # Create row with 8 columns
            row = [
                timestamp_str,  # Timestamp
                str(float(indoor_pm25)),  # Indoor PM2.5
                str(float(outdoor_pm25)),  # Outdoor PM2.5
                str(ratio) if ratio != '' else '',  # Ratio
                str(float(record.get('efficiency', 0.0) * 100)),  # Estimated Filter Efficiency (%)
                str(efficiency_uncertainty) if efficiency_uncertainty != '' else '',  # Efficiency Uncertainty (%)
                str(float(predicted_indoor)),  # Predicted Indoor PM2.5
                str(prediction_error),  # Prediction Error
            ]

            time_series_rows.append(row)

        return time_series_rows

    def _ensure_results_sheet_exists(self, sheet_name: str):
        """
        Ensure the results sheet exists, create if not.

        Args:
            sheet_name: Name of the results sheet
        """
        spreadsheet_id = self.config['spreadsheet_id']

        try:
            # Ensure service is initialized
            if self.service is None:
                raise RuntimeError("Google Sheets service not initialized")

            # Get existing sheets
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

            if sheet_name not in existing_sheets:
                # Create the sheet
                requests = [{'addSheet': {'properties': {'title': sheet_name}}}]

                if self.service is not None:
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id, body={'requests': requests}
                    ).execute()

                self.logger.info(f"Created new sheet: {sheet_name}")

        except Exception as e:
            self.logger.warning(f"Could not ensure results sheet exists: {e}")

    def get_latest_analysis_timestamp(self, sheet_name: Optional[str] = None) -> Optional[datetime]:
        """
        Get the timestamp of the most recent analysis.

        Args:
            sheet_name: Results sheet name (uses config default if None)

        Returns:
            Datetime of latest analysis or None if no previous analysis
        """
        if sheet_name is None:
            sheet_name = self.config['results_sheet']

        spreadsheet_id = self.config['spreadsheet_id']

        try:
            # Ensure service is initialized
            if self.service is None:
                self.logger.warning("Google Sheets service not initialized")
                return None

            # Read timestamp column
            range_name = f"{sheet_name}!A:A"
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()

            values = result.get('values', [])

            if len(values) <= 1:  # Only headers or empty
                return None

            # Get the last timestamp (excluding header)
            timestamp_strings = [row[0] for row in values[1:] if row]

            if not timestamp_strings:
                return None

            # Parse the most recent timestamp
            latest_timestamp_str = timestamp_strings[-1]
            return pd.to_datetime(latest_timestamp_str)

        except Exception as e:
            self.logger.warning(f"Could not get latest analysis timestamp: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test the connection to Google Sheets.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            spreadsheet_id = self.config['spreadsheet_id']

            # Ensure service is initialized
            if self.service is None:
                self.logger.error("Google Sheets service not initialized")
                return False

            # Try to get spreadsheet info
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

            title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            self.logger.info(f"Successfully connected to spreadsheet: '{title}'")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
