#!/usr/bin/env python3
"""
Data Utilities Module
Provides data processing, validation, and formatting utilities for the dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
import yaml
from pathlib import Path

class DataUtils:
    """Utility class for data processing and validation"""
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            st.error(f"Failed to load configuration: {str(e)}")
            return {}
    
    @staticmethod
    def format_currency(value: float, decimals: int = 0) -> str:
        """Format currency values with enhanced handling"""
        if pd.isna(value) or value == 0:
            return "$0"
        
        abs_value = abs(value)
        if abs_value >= 1e9:
            return f"${value/1e9:.{decimals}f}B"
        elif abs_value >= 1e6:
            return f"${value/1e6:.{decimals}f}M"
        elif abs_value >= 1e3:
            return f"${value/1e3:.{decimals}f}K"
        else:
            return f"${value:,.{decimals}f}"
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format percentage values with enhanced handling"""
        if pd.isna(value):
            return "0.0%"
        return f"{value:.{decimals}f}%"
    
    @staticmethod
    def format_area(value: float, decimals: int = 0) -> str:
        """Format square footage values with enhanced handling"""
        if pd.isna(value) or value == 0:
            return "0 SF"
        
        abs_value = abs(value)
        if abs_value >= 1e6:
            return f"{value/1e6:.{decimals}f}M SF"
        elif abs_value >= 1e3:
            return f"{value/1e3:.{decimals}f}K SF"
        else:
            return f"{value:,.{decimals}f} SF"
    
    @staticmethod
    def convert_excel_date_to_python(excel_date: float) -> date:
        """Convert Excel serial date to Python date"""
        try:
            # Excel serial date is days since January 1, 1900
            # Python date starts from January 1, 1900
            # -2 for Excel's leap year bug
            return date(1900, 1, 1) + timedelta(days=int(excel_date) - 2)
        except Exception:
            return date.today()
    
    @staticmethod
    def convert_python_date_to_excel(python_date: date) -> int:
        """Convert Python date to Excel serial date"""
        try:
            # Convert Python date to Excel serial date
            # +2 for Excel's leap year bug
            return (python_date - date(1900, 1, 1)).days + 2
        except Exception:
            return 0
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date, 
                          min_days: int = 1, max_days: int = 3650) -> List[str]:
        """Validate date range and return list of errors"""
        errors = []
        
        if start_date >= end_date:
            errors.append("Start date must be before end date")
        
        date_diff = (end_date - start_date).days
        if date_diff < min_days:
            errors.append(f"Date range must be at least {min_days} day(s)")
        
        if date_diff > max_days:
            errors.append(f"Date range cannot exceed {max_days} days")
        
        return errors
    
    @staticmethod
    def validate_property_selection(properties: List[str]) -> List[str]:
        """Validate property selection and return list of errors"""
        errors = []
        
        if not properties:
            errors.append("At least one property must be selected")
        
        if len(properties) > 50:
            errors.append("Cannot select more than 50 properties at once")
        
        return errors
    
    @staticmethod
    def build_property_filter(selected_properties: List[str]) -> str:
        """Build SQL property filter from selected properties"""
        if not selected_properties:
            return "1=1"
        
        try:
            property_codes = [prop.split(" - ")[0] for prop in selected_properties]
            quoted_codes = [f"'{code}'" for code in property_codes]
            return f"\"property code\" IN ({', '.join(quoted_codes)})"
        except Exception:
            return "1=1"
    
    @staticmethod
    def build_date_filter(date_range: Tuple[date, date]) -> str:
        """Build SQL date filter from date range"""
        if not date_range or len(date_range) != 2:
            return "1=1"
        
        try:
            start_date, end_date = date_range
            start_serial = DataUtils.convert_python_date_to_excel(start_date)
            end_serial = DataUtils.convert_python_date_to_excel(end_date)
            return f"month BETWEEN {start_serial} AND {end_serial}"
        except Exception:
            return "1=1"
    
    @staticmethod
    def build_book_filter(book_filter: str) -> str:
        """Build SQL book filter from book selection"""
        if book_filter == "Book 46 (FPR)":
            return "AND ft.\"book id\" = 46"
        elif book_filter == "Book 1 (Standard)":
            return "AND ft.\"book id\" = 1"
        else:
            return ""
    
    @staticmethod
    def calculate_percentage_change(current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    @staticmethod
    def calculate_moving_average(data: pd.Series, window: int = 3) -> pd.Series:
        """Calculate moving average for time series data"""
        return data.rolling(window=window, min_periods=1).mean()
    
    @staticmethod
    def detect_outliers(data: pd.Series, method: str = "iqr") -> pd.Series:
        """Detect outliers in data series"""
        if method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (data < lower_bound) | (data > upper_bound)
        elif method == "zscore":
            z_scores = np.abs((data - data.mean()) / data.std())
            return z_scores > 3
        else:
            return pd.Series([False] * len(data))
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare dataframe for display"""
        if df.empty:
            return df
        
        # Remove duplicate rows
        df = df.drop_duplicates()
        
        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Handle infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        
        return df
    
    @staticmethod
    def prepare_chart_data(df: pd.DataFrame, x_col: str, y_col: str, 
                          max_points: int = 100) -> pd.DataFrame:
        """Prepare data for charting with sampling if needed"""
        if df.empty:
            return df
        
        # Sort by y column for better visualization
        df = df.sort_values(y_col, ascending=False)
        
        # Limit number of points for performance
        if len(df) > max_points:
            df = df.head(max_points)
        
        return df
    
    @staticmethod
    def create_summary_stats(df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Create summary statistics for numeric columns"""
        stats = {}
        
        for col in numeric_columns:
            if col in df.columns:
                series = df[col].dropna()
                if not series.empty:
                    stats[col] = {
                        'count': len(series),
                        'mean': series.mean(),
                        'median': series.median(),
                        'std': series.std(),
                        'min': series.min(),
                        'max': series.max(),
                        'sum': series.sum()
                    }
        
        return stats
    
    @staticmethod
    def export_data(df: pd.DataFrame, format: str = "csv", 
                   filename: str = None) -> Tuple[str, str]:
        """Export dataframe to various formats"""
        if df.empty:
            return "", ""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}"
        
        if format.lower() == "csv":
            data = df.to_csv(index=False)
            mime_type = "text/csv"
            file_extension = ".csv"
        elif format.lower() == "excel":
            # This would require openpyxl
            data = df.to_csv(index=False)  # Fallback to CSV
            mime_type = "text/csv"
            file_extension = ".csv"
        else:
            data = df.to_csv(index=False)
            mime_type = "text/csv"
            file_extension = ".csv"
        
        return data, f"{filename}{file_extension}"
    
    @staticmethod
    def create_download_button(df: pd.DataFrame, label: str, 
                             filename: str = None, format: str = "csv"):
        """Create a download button for dataframe"""
        if df.empty:
            st.warning("No data available for download")
            return
        
        data, full_filename = DataUtils.export_data(df, format, filename)
        
        st.download_button(
            label=label,
            data=data,
            file_name=full_filename,
            mime="text/csv"
        )
    
    @staticmethod
    def get_color_scale(data_type: str) -> str:
        """Get appropriate color scale for data type"""
        color_scales = {
            'revenue': 'Blues',
            'noi': 'Greens',
            'margin': 'RdYlGn',
            'risk': 'RdYlBu',
            'occupancy': 'Viridis',
            'growth': 'Plasma'
        }
        return color_scales.get(data_type.lower(), 'Blues')
    
    @staticmethod
    def format_large_number(value: float) -> str:
        """Format large numbers for display"""
        if pd.isna(value) or value == 0:
            return "0"
        
        abs_value = abs(value)
        if abs_value >= 1e9:
            return f"{value/1e9:.1f}B"
        elif abs_value >= 1e6:
            return f"{value/1e6:.1f}M"
        elif abs_value >= 1e3:
            return f"{value/1e3:.0f}K"
        else:
            return f"{value:,.0f}"
    
    @staticmethod
    def calculate_compound_growth_rate(initial_value: float, final_value: float, 
                                     periods: int) -> float:
        """Calculate compound annual growth rate"""
        if initial_value <= 0 or periods <= 0:
            return 0.0
        
        return ((final_value / initial_value) ** (1 / periods) - 1) * 100
