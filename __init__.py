import os
import pandas as pd
import numpy as np
import sys
import logging
from typing import Dict, Any

# Assuming ConfigModel and exceptions are importable from sibling modules
from .config import ConfigModel
from . import config as config_module # Import classes from config.py
from .exceptions import StataToDfBaseError, DataLoaderError

# Set up logging
logger = logging.getLogger("stata_to_df")
logger.setLevel(logging.DEBUG) # Set to DEBUG for detailed output

# Fetch environment variables for PYSTATA_PATH and STATA_EDITION
PYSTATA_PATH = os.environ.get("PYSTATA_PATH", None) # Read from environment variable
STATA_EDITION = os.environ.get("STATA_EDITION", None) # Read from environment variable

# --- Public API Function ---
def stata_to_df(config_dict: Dict[str, Any], valuelabel=True) -> pd.DataFrame:
    try:
        config = config_module.validate_config(config_dict)
        df = load_data(config,valuelabel=valuelabel)
        return df
    except StataToDfBaseError as e:
        logger.error(f"Error in configuration or data loading: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in export: {e}", exc_info=True)
        raise

# --- Stata Environment Setup ---
def setup_stata():
    """
    Set up the environment for running Python within Stata.
    Attempts to import and initialize pystata.

    Returns:
        The initialized pystata.stata module object.

    Raises:
        DataLoaderError: If PYSTATA_PATH is not set, STATA_EDITION is not set or pystata cannot be imported/initialized.
    """
    logger.debug("Attempting to set up Stata environment...")
    if not PYSTATA_PATH:
        msg = "PYSTATA_PATH environment variable not set. Cannot initialize pystata."
        logger.error(msg)
        raise DataLoaderError(msg)

    if PYSTATA_PATH not in sys.path:
        logger.debug(f"Adding PYSTATA_PATH '{PYSTATA_PATH}' to sys.path.")
        sys.path.append(PYSTATA_PATH)
    else:
        logger.debug(f"PYSTATA_PATH '{PYSTATA_PATH}' already in sys.path.")

    if not STATA_EDITION:
        msg = "STATA_EDITION environment variable not set. Cannot initialize pystata."
        logger.error(msg)
        raise DataLoaderError(msg)

    if STATA_EDITION not in sys.path:
        logger.debug(f"Adding STATA_EDITION '{STATA_EDITION}' to sys.path.")
        sys.path.append(STATA_EDITION)
    else:
        logger.debug(f"STATA_EDITION '{STATA_EDITION}' already in sys.path.")

    try:
        # Import pystata config and initialize Stata interface
        from pystata import config as pystata_config # Ignore linting errors - package will be found using PYSTATA_PATH
        pystata_config.init(STATA_EDITION,splash=False) # Initialize Stata with the specified edition
        print("Stata initialized successfully.")
        from pystata import stata as pystata_stata # Ignore linting errors - package will be found using PYSTATA_PATH
        logger.info("pystata initialized successfully.")

        return pystata_stata
    except ImportError as e:
        msg = f"Failed to import pystata. Ensure PYSTATA_PATH ('{PYSTATA_PATH}') is correct and pystata is installed. Error: {e}"
        logger.error(msg)
        raise DataLoaderError(msg) from e
    except Exception as e: # Catch potential errors during init()
        msg = f"Failed to initialize pystata. Error: {e}"
        logger.error(msg)
        raise DataLoaderError(msg) from e
    
# --- Data Loading Function ---
def load_data(config: ConfigModel, valuelabel=True) -> pd.DataFrame:
    """
    Loads data either from the current Stata session.

    Args:
        config: The configuration dictionary providing the Stata variable names.

    Returns:
        A Pandas DataFrame containing the required data.

    Raises:
        DataLoaderError: If loading from Stata fails (e.g., pystata issues, variables not found).
    """
    required_vars = set(config.row_var + config.col_var + [config.value_var])
    if config.pweight:
        required_vars.add(config.pweight)
    if config.secondary_ref:
        required_vars.add(config.secondary_ref)

    logger.info("Attempting to load data from Stata...")
    try:
        stata = setup_stata() # Initialize Stata environment and get interface

        # Construct variable list for Stata, ensuring uniqueness
        st_import_vars = list(required_vars)
        logger.debug(f"Requesting variables from Stata: {st_import_vars}")

        # Fetch data from Stata using pystata
        # Use valuelabel=True to get labels, missingval=np.nan for consistency
        df = stata.pdataframe_from_data(var=st_import_vars, valuelabel=valuelabel, missingval=np.nan)
        logger.info(f"Successfully loaded DataFrame from Stata with shape {df.shape}.")
        print(f"Loaded DataFrame from Stata with shape {df.shape}.")
        logger.debug(f"Columns loaded from Stata: {list(df.columns)}")

        # Basic check if DataFrame is empty
        if df.empty:
                logger.warning("Loaded DataFrame from Stata is empty.")
        # Could add further validation here if needed, e.g., checking dtypes,
        # but pdataframe_from_data usually handles basic conversion.

        print(df.head(10))
        return df

    except DataLoaderError:
            # Re-raise errors from setup_stata directly
            raise
    except Exception as e:
        # Catch potential errors from pdataframe_from_data (e.g., var not found)
        # Stata errors might come through as various exception types.
        msg = f"Failed to load data from Stata. Ensure variables {st_import_vars} exist. Error: {e}"
        logger.error(msg, exc_info=True) # Include traceback in log
        raise DataLoaderError(msg) from e
