#!/usr/bin/env python3
"""
Error Handling Component
Provides consistent error handling and user feedback across the dashboard
"""

import streamlit as st
import traceback
from typing import Optional, Callable, Any
import time

class ErrorHandler:
    """Centralized error handling for the dashboard"""
    
    @staticmethod
    def handle_database_error(error: Exception, context: str = "") -> None:
        """Handle database-related errors with user-friendly messages"""
        error_msg = str(error).lower()
        
        if "connection" in error_msg or "database" in error_msg:
            st.error(f"""
            <div class="error-message">
                <h4>🚨 Database Connection Error</h4>
                <p><strong>Context:</strong> {context}</p>
                <p><strong>Error:</strong> {str(error)}</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Check if the database file exists and is accessible</li>
                    <li>Ensure you have read permissions for the database file</li>
                    <li>Try refreshing the page or restarting the application</li>
                    <li>Contact support if the issue persists</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        elif "table" in error_msg or "column" in error_msg:
            st.error(f"""
            <div class="error-message">
                <h4>🚨 Database Schema Error</h4>
                <p><strong>Context:</strong> {context}</p>
                <p><strong>Error:</strong> {str(error)}</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>The database schema may have changed</li>
                    <li>Try refreshing the data cache</li>
                    <li>Check if all required tables exist</li>
                    <li>Contact support for schema updates</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.error(f"""
            <div class="error-message">
                <h4>🚨 Database Error</h4>
                <p><strong>Context:</strong> {context}</p>
                <p><strong>Error:</strong> {str(error)}</p>
                <p>Please try refreshing the page or contact support.</p>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def handle_query_error(error: Exception, query: str = "", context: str = "") -> None:
        """Handle query execution errors"""
        st.error(f"""
        <div class="error-message">
            <h4>🚨 Query Execution Error</h4>
            <p><strong>Context:</strong> {context}</p>
            <p><strong>Error:</strong> {str(error)}</p>
            <p><strong>Query:</strong> <code>{query[:200]}{'...' if len(query) > 200 else ''}</code></p>
            <p><strong>Solutions:</strong></p>
            <ul>
                <li>Check if the selected filters are valid</li>
                <li>Try selecting different date ranges or properties</li>
                <li>Refresh the data cache</li>
                <li>Contact support if the issue persists</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def handle_data_validation_error(error: Exception, context: str = "") -> None:
        """Handle data validation errors"""
        st.warning(f"""
        <div class="warning-message">
            <h4>⚠️ Data Validation Warning</h4>
            <p><strong>Context:</strong> {context}</p>
            <p><strong>Issue:</strong> {str(error)}</p>
            <p>This may affect the accuracy of displayed data. Please verify your selections.</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def handle_component_error(error: Exception, component: str = "") -> None:
        """Handle component loading or rendering errors"""
        st.error(f"""
        <div class="error-message">
            <h4>🚨 Component Error</h4>
            <p><strong>Component:</strong> {component}</p>
            <p><strong>Error:</strong> {str(error)}</p>
            <p><strong>Solutions:</strong></p>
            <ul>
                <li>Try refreshing the page</li>
                <li>Check if all component files are present</li>
                <li>Try selecting a different dashboard</li>
                <li>Contact support if the issue persists</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def handle_performance_warning(execution_time: float, context: str = "") -> None:
        """Handle performance warnings for slow operations"""
        if execution_time > 5.0:
            st.warning(f"""
            <div class="warning-message">
                <h4>⚠️ Performance Warning</h4>
                <p><strong>Context:</strong> {context}</p>
                <p><strong>Execution Time:</strong> {execution_time:.2f} seconds</p>
                <p>This operation is taking longer than expected. Consider:</p>
                <ul>
                    <li>Narrowing your date range or property selection</li>
                    <li>Refreshing the data cache</li>
                    <li>Contacting support if this persists</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif execution_time > 2.0:
            st.info(f"⏱️ {context} took {execution_time:.2f} seconds to complete")
    
    @staticmethod
    def safe_execute(func: Callable, *args, context: str = "", **kwargs) -> Optional[Any]:
        """Safely execute a function with error handling"""
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Check for performance issues
            ErrorHandler.handle_performance_warning(execution_time, context)
            
            return result
            
        except Exception as e:
            ErrorHandler.handle_component_error(e, context)
            return None
    
    @staticmethod
    def show_loading_state(message: str = "Loading..."):
        """Show a loading state with spinner"""
        return st.spinner(f"🔄 {message}")
    
    @staticmethod
    def show_success_message(message: str, context: str = ""):
        """Show a success message"""
        st.success(f"""
        <div class="success-message">
            <h4>✅ Success</h4>
            <p><strong>Context:</strong> {context}</p>
            <p>{message}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_info_message(message: str, context: str = ""):
        """Show an info message"""
        st.info(f"""
        <div class="info-message">
            <h4>ℹ️ Information</h4>
            <p><strong>Context:</strong> {context}</p>
            <p>{message}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def validate_filters(date_range, selected_properties, fund_filter, book_filter):
        """Validate user-selected filters"""
        errors = []
        
        # Validate date range
        if not date_range or len(date_range) != 2:
            errors.append("Date range must be selected")
        elif date_range[0] >= date_range[1]:
            errors.append("Start date must be before end date")
        
        # Validate properties
        if not selected_properties:
            errors.append("At least one property must be selected")
        
        # Validate fund filter
        if not fund_filter:
            errors.append("Fund filter must be selected")
        
        # Validate book filter
        if not book_filter:
            errors.append("Book filter must be selected")
        
        return errors
    
    @staticmethod
    def show_validation_errors(errors: list):
        """Show validation errors to the user"""
        if errors:
            st.error(f"""
            <div class="error-message">
                <h4>⚠️ Validation Errors</h4>
                <p>Please fix the following issues:</p>
                <ul>
                    {''.join([f'<li>{error}</li>' for error in errors])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            return True
        return False

def with_error_handling(func: Callable) -> Callable:
    """Decorator to add error handling to functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_component_error(e, func.__name__)
            return None
    return wrapper

def with_loading_state(message: str = "Loading..."):
    """Decorator to add loading state to functions"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with st.spinner(f"🔄 {message}"):
                return func(*args, **kwargs)
        return wrapper
    return decorator
