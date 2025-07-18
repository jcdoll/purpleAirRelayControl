"""
Google Sheets API client for filter efficiency analysis.

This module provides functions to read sensor data from Google Sheets
and write analysis results back to the same or different sheet.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
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
                "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
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
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                # Load from file (for local development)
                credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
                if os.path.exists(credentials_file):
                    self.credentials = Credentials.from_service_account_file(
                        credentials_file,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                else:
                    raise FileNotFoundError(
                        f"Google Sheets credentials not found. "
                        f"Set GOOGLE_SHEETS_CREDENTIALS environment variable or "
                        f"place credentials.json file in working directory."
                    )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.logger.info("Google Sheets API service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise
    
    def read_sensor_data(
        self, 
        days_back: int = 7,
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read sensor data from Google Sheets.
        
        Args:
            days_back: Number of days of historical data to read
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
        start_date = end_date - timedelta(days=days_back)
        
        try:
            # Read data from sheet
            range_name = f"{sheet_name}!A1:{chr(ord('A') + 10)}{max_rows}"  # A1:K{max_rows}
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
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
    
    def _clean_sensor_data(
        self, 
        df: pd.DataFrame, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
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
        
        # Map common column names to standard names
        column_mapping = {
            'Timestamp': 'timestamp',
            'Time': 'timestamp',
            'DateTime': 'timestamp',
            'Indoor AQI': 'indoor_aqi',
            'Indoor': 'indoor_aqi',
            'Outdoor AQI': 'outdoor_aqi',
            'Outdoor': 'outdoor_aqi',
            'PurpleAir Indoor': 'indoor_aqi',
            'PurpleAir Outdoor': 'outdoor_aqi'
        }
        
        # Rename columns
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
        df = df[mask]
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Remove duplicates (keep last)
        df = df.drop_duplicates(subset=['timestamp'], keep='last')
        
        self.logger.info(f"Cleaned data: {len(df)} valid records between {start_date} and {end_date}")
        return df
    
    def write_analysis_results(
        self, 
        results: Dict[str, Any],
        sheet_name: Optional[str] = None
    ) -> bool:
        """
        Write filter efficiency analysis results to Google Sheets.
        
        Args:
            results: Analysis results dictionary
            sheet_name: Sheet name for results (uses config default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if sheet_name is None:
            sheet_name = self.config['results_sheet']
        
        spreadsheet_id = self.config['spreadsheet_id']
        
        try:
            # Prepare results data for writing
            results_data = self._prepare_results_data(results)
            
            # Check if results sheet exists, create if not
            self._ensure_results_sheet_exists(sheet_name)
            
            # Write headers if sheet is empty
            self._write_results_headers(sheet_name)
            
            # Append new results
            range_name = f"{sheet_name}!A:Z"  # Will append to next empty row
            
            body = {
                'values': [results_data]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            self.logger.info(f"Successfully wrote analysis results to sheet '{sheet_name}'")
            return True
            
        except HttpError as e:
            self.logger.error(f"HTTP error writing to Google Sheets: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error writing analysis results: {e}")
            return False
    
    def _prepare_results_data(self, results: Dict[str, Any]) -> List[str]:
        """
        Prepare analysis results for writing to sheets.
        
        Args:
            results: Analysis results dictionary
            
        Returns:
            List of values for a single row
        """
        timestamp = results.get('analysis_timestamp', datetime.now())
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)
        
        # Extract key metrics
        performance = results.get('filter_performance', {})
        quality = results.get('model_quality', {})
        data_period = results.get('data_period', {})
        recommendations = results.get('recommendations', {})
        
        # Format data row
        data_row = [
            timestamp_str,
            performance.get('efficiency_percentage', ''),
            performance.get('infiltration_rate', ''),
            quality.get('r_squared', ''),
            quality.get('rmse', ''),
            data_period.get('n_points_clean', ''),
            recommendations.get('filter_status', ''),
            '; '.join(recommendations.get('alerts', [])),
            '; '.join(recommendations.get('actions', [])[:2]),  # Top 2 actions
            str(data_period.get('start', '')),
            str(data_period.get('end', ''))
        ]
        
        # Convert all values to strings
        return [str(val) for val in data_row]
    
    def _ensure_results_sheet_exists(self, sheet_name: str):
        """
        Ensure the results sheet exists, create if not.
        
        Args:
            sheet_name: Name of the results sheet
        """
        spreadsheet_id = self.config['spreadsheet_id']
        
        try:
            # Get existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name not in existing_sheets:
                # Create the sheet
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
                self.logger.info(f"Created new sheet: {sheet_name}")
        
        except Exception as e:
            self.logger.warning(f"Could not ensure results sheet exists: {e}")
    
    def _write_results_headers(self, sheet_name: str):
        """
        Write headers to results sheet if it's empty.
        
        Args:
            sheet_name: Name of the results sheet
        """
        spreadsheet_id = self.config['spreadsheet_id']
        
        try:
            # Check if sheet is empty
            range_name = f"{sheet_name}!A1:A1"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values or not values[0]:
                # Sheet is empty, write headers
                headers = [
                    'Analysis Timestamp',
                    'Filter Efficiency (%)',
                    'Infiltration Rate (ACH)',
                    'Model R²',
                    'Model RMSE',
                    'Data Points Used',
                    'Filter Status',
                    'Alerts',
                    'Recommended Actions',
                    'Data Period Start',
                    'Data Period End'
                ]
                
                body = {
                    'values': [headers]
                }
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A1:K1",
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                self.logger.info(f"Wrote headers to results sheet: {sheet_name}")
        
        except Exception as e:
            self.logger.warning(f"Could not write headers: {e}")
    
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
            # Read timestamp column
            range_name = f"{sheet_name}!A:A"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
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
            
            # Try to get spreadsheet info
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            self.logger.info(f"Successfully connected to spreadsheet: '{title}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Google Sheets: {e}")
            return False 