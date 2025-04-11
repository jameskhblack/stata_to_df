"""Custom exception classes for the Stata to DataFrame application."""

class StataToDfBaseError(Exception):
    """Base class for all custom exceptions in the Stata to DataFrame application."""
    pass

class ConfigValidationError(StataToDfBaseError):
    """Exception raised for errors during configuration validation."""
    pass

class DataLoaderError(StataToDfBaseError):
    """Exception raised for errors during data loading (e.g., pystata issues, missing variables)."""
    pass
