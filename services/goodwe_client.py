"""
GoodWe SEMS Portal API Client.

This module provides a client for communicating with the GoodWe SEMS Portal API
to retrieve solar inverter data, energy generation metrics, and battery status.
"""

import base64
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class GoodWeClient:
    """
    Client for GoodWe SEMS Portal API communication.
    
    Provides methods to authenticate and retrieve solar inverter data
    including power generation, energy production, and battery status.
    """
    
    BASE_URLS = {
        "us": "https://us.semsportal.com/api/",
        "eu": "https://eu.semsportal.com/api/",
    }
    
    API_VERSION = "v2.0.4"
    CLIENT_TYPE = "web"
    DEFAULT_LANGUAGE = "en"
    REQUEST_TIMEOUT = 30

    def __init__(self, region: str = "us"):
        """
        Initialize GoodWe API client.
        
        Args:
            region: API region (us or eu)
        """
        self.region = region
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        })

    def _get_base_url(self) -> str:
        """Get base URL for the configured region."""
        return self.BASE_URLS.get(self.region, self.BASE_URLS["us"])

    def _generate_initial_token(self) -> str:
        """
        Generate initial token for first API request.
        
        Returns:
            str: Base64 encoded initial token
        """
        timestamp = str(int(time.time() * 1000))
        
        token_data = {
            "version": self.API_VERSION,
            "client": self.CLIENT_TYPE,
            "language": self.DEFAULT_LANGUAGE,
            "timestamp": timestamp,
            "uid": "",
            "token": "",
        }
        
        return base64.b64encode(json.dumps(token_data).encode()).decode()

    def crosslogin(self, account: str, password: str) -> Optional[str]:
        """
        Authenticate with GoodWe SEMS Portal.
        
        Args:
            account: User account/email
            password: User password
            
        Returns:
            str: Authentication token if successful, None otherwise
        """
        url = f"{self._get_base_url()}v2/Common/CrossLogin"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            "Token": self._generate_initial_token(),
            "Content-Type": "application/json",
            "Origin": f"https://{self.region}.semsportal.com",
            "Referer": f"https://{self.region}.semsportal.com/",
        }
        
        payload = {
            "account": account,
            "pwd": password,
            "validCode": "",
            "is_local": True,
            "timestamp": timestamp,
            "agreement_agreement": True,
        }
        
        try:
            logger.info(f"Attempting login to GoodWe SEMS Portal for account: {account}")
            
            response = self.session.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("data"):
                    try:
                        token = base64.b64encode(
                            json.dumps(data.get("data")).encode()
                        ).decode()
                        self.session.headers.update({"Token": token})
                        logger.info("Successfully authenticated with GoodWe SEMS Portal")
                        return token
                    except Exception as e:
                        logger.error(f"Failed to encode authentication token: {e}")
                        return None
                
                # Fallback for legacy token format
                if (data.get("code") == 10000 and 
                    isinstance(data.get("data"), dict)):
                    token_data = data.get("data", {})
                    if token_data.get("token"):
                        token = token_data.get("token")
                        self.session.headers.update({"Token": token})
                        logger.info("Successfully authenticated (legacy format)")
                        return token
                
                logger.error(f"Login failed: {data.get('msg')} (Code: {data.get('code')})")
            else:
                logger.error(f"Login request failed with status: {response.status_code}")
                
            return None
            
        except requests.RequestException as e:
            logger.error(f"Network error during login: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return None

    def get_inverter_data_by_column(
        self, 
        token: str, 
        inverter_id: str, 
        column: str, 
        date: str
    ) -> Optional[Dict]:
        """
        Retrieve inverter data for a specific column.
        
        Args:
            token: Authentication token
            inverter_id: Inverter identifier
            column: Data column name (e.g., 'Pac', 'Eday', 'Cbattery1')
            date: Date string in YYYY-MM-DD format
            
        Returns:
            dict: API response data or None if failed
        """
        url = f"{self._get_base_url()}PowerStationMonitor/GetInverterDataByColumn"
        
        headers = {
            "Token": token,
            "Content-Type": "application/json",
        }
        
        payload = {
            "id": inverter_id, 
            "date": date, 
            "column": column
        }
        
        try:
            logger.debug(f"Requesting inverter data: {column} for {date}")
            
            response = self.session.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON response from inverter data API")
                    return None
            else:
                logger.error(f"Inverter data request failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error retrieving inverter data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving inverter data: {e}")
            return None

    def _parse_time_series_data(self, response_data: Dict) -> Optional[List[Tuple]]:
        """
        Parse time series data from API response.
        
        Args:
            response_data: Raw API response data
            
        Returns:
            list: List of (datetime, value) tuples or None if parsing failed
        """
        if not response_data:
            return None
            
        data = (response_data if not isinstance(response_data, dict) 
                else response_data.get("data", response_data))
        
        # Find the data list
        candidate_list = None
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    candidate_list = value
                    break
        elif isinstance(data, list):
            candidate_list = data
            
        if not candidate_list:
            return None
            
        series = []
        time_fields = ("date", "time", "collectTime", "timestamp")
        value_fields = ("column", "value", "val", "v")
        
        for item in candidate_list:
            if not isinstance(item, dict):
                continue
                
            # Extract time
            timestamp = None
            for field in time_fields:
                if field in item:
                    timestamp = item[field]
                    break
                    
            if timestamp is None:
                # Look for any field containing 'time' or 'date'
                for key in item.keys():
                    if 'time' in key.lower() or 'date' in key.lower():
                        timestamp = item[key]
                        break
                        
            # Extract value
            value = None
            for field in value_fields:
                if field in item:
                    value = item[field]
                    break
                    
            if value is None:
                # Look for numeric values
                for key, val in item.items():
                    if key not in time_fields and isinstance(val, (int, float)):
                        value = val
                        break
                        
            # Parse timestamp
            parsed_time = self._parse_timestamp(timestamp)
            if parsed_time:
                series.append((parsed_time, value))
                
        return series if series else None

    def _parse_timestamp(self, timestamp: Union[str, int, float]) -> Optional[datetime]:
        """
        Parse various timestamp formats.
        
        Args:
            timestamp: Timestamp in various formats
            
        Returns:
            datetime: Parsed datetime object or None
        """
        if isinstance(timestamp, (int, float)):
            try:
                return datetime.fromtimestamp(float(timestamp))
            except (ValueError, OSError):
                return None
                
        if isinstance(timestamp, str):
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S", 
                "%Y-%m-%d",
                "%d/%m/%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
                    
        return None

    def get_multiple_columns_data(
        self, 
        token: str, 
        inverter_id: str, 
        columns: List[str], 
        date: str,
        use_mock_data: bool = False
    ) -> Dict[str, List[Tuple]]:
        """
        Retrieve data for multiple columns.
        
        Args:
            token: Authentication token
            inverter_id: Inverter identifier
            columns: List of column names to retrieve
            date: Date string in YYYY-MM-DD format
            use_mock_data: Whether to generate mock data on API failure
            
        Returns:
            dict: Column name mapped to time series data
        """
        results = {}
        error_details = {}
        has_real_data = False
        
        for column in columns:
            logger.debug(f"Fetching data for column: {column}")
            
            response = self.get_inverter_data_by_column(
                token, inverter_id, column, date
            )
            
            if response and not response.get('hasError'):
                series = self._parse_time_series_data(response)
                if series:
                    results[column] = series
                    has_real_data = True
                    continue
                    
            # Handle API errors
            if isinstance(response, dict) and response.get('msg'):
                error_details[column] = response.get('msg', 'Unknown error')
                
            # Generate mock data if requested and real data failed
            if use_mock_data:
                logger.warning(f"Using mock data for column: {column}")
                mock_series = self._generate_mock_time_series(column, date)
                results[column] = mock_series
            else:
                logger.error(f"No valid data found for column: {column}")
                results[column] = []
                
        # Include error details for debugging
        if error_details:
            results['_error_details'] = error_details
            
        if not has_real_data and not use_mock_data:
            logger.warning(f"No real data available for inverter: {inverter_id}")
            
        return results

    def _generate_mock_time_series(self, column: str, date_str: str) -> List[Tuple]:
        """
        Generate realistic mock time series data for development.
        
        Args:
            column: Column name for appropriate data pattern
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            list: Mock time series data as (datetime, value) tuples
        """
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        series = []
        
        if column == 'Pac':  # Power generation (kW)
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 6 <= hour <= 18:  # Daylight hours
                    # Solar curve: low at sunrise/sunset, peak at noon
                    solar_factor = abs(12 - hour) / 6.0
                    power = max(0, 5.5 - (solar_factor * 4.5) + random.uniform(-0.5, 0.5))
                    power = round(power, 2)
                else:
                    power = 0.0
                series.append((dt, power))
                
        elif column == 'Eday':  # Daily energy (kWh) - cumulative
            energy = 0.0
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 6 <= hour <= 18:
                    energy += random.uniform(0.3, 1.2)
                series.append((dt, round(energy, 2)))
                
        elif column == 'Cbattery1':  # Battery SOC (%)
            soc = 80.0  # Start at 80%
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 8 <= hour <= 16:  # Charging during solar hours
                    soc = min(100.0, soc + random.uniform(0.5, 2.0))
                elif 18 <= hour <= 23:  # Discharging at night
                    soc = max(20.0, soc - random.uniform(1.0, 3.0))
                series.append((dt, round(soc, 1)))
                
        else:  # Generic column - random values
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                value = round(random.uniform(10, 50), 2)
                series.append((dt, value))
                
        return series

    def get_station_list(self, token: str) -> Optional[List[Dict]]:
        """
        Get list of power stations for authenticated user.
        
        Args:
            token: Authentication token
            
        Returns:
            list: List of power station information
        """
        url = f"{self._get_base_url()}PowerStation/GetMonitorDetailByPowerstationId"
        
        headers = {
            "Token": token,
            "Content-Type": "application/json",
        }
        
        try:
            response = self.session.post(
                url, 
                headers=headers, 
                timeout=self.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.error(f"Failed to get station list: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting station list: {e}")
            return None