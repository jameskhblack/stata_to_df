"""Configuration validation using Pydantic."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ValidationError, model_validator

from .exceptions import ConfigValidationError



# Define the main configuration model
class ConfigModel(BaseModel):
    """Pydantic model for the main application configuration."""
    # Required fields
    row_var: List[str] = Field(..., min_length=1)
    col_var: List[str] = Field(..., min_length=1)
    value_var: str
    
    # Optional fields with defaults
    pweight: Optional[str] = None
    secondary_ref: Optional[str] = None

    # --- Model Validators ---
    @model_validator(mode='after')
    def check_variable_names_distinct(self) -> 'ConfigModel':
        """Ensure core variable names do not overlap."""
        core_vars = {self.value_var}
        if self.pweight:
            core_vars.add(self.pweight)
        if self.secondary_ref:
            core_vars.add(self.secondary_ref)

        all_index_vars = set(self.row_var + self.col_var)

        overlap = core_vars.intersection(all_index_vars)
        if overlap:
            raise ValueError(f"Overlap detected between index variables (row_var, col_var) and core variables (value_var, pweight, secondary_ref): {overlap}")

        # Check for duplicates within row_var or col_var themselves
        if len(self.row_var) != len(set(self.row_var)):
            raise ValueError(f"Duplicate variable names found within row_var: {self.row_var}")
        if len(self.col_var) != len(set(self.col_var)):
            raise ValueError(f"Duplicate variable names found within col_var: {self.col_var}")

        return self



# --- Validation Function ---

def validate_config(config_dict: Dict[str, Any]) -> ConfigModel:
    """
    Validates the raw configuration dictionary using the Pydantic model.

    Args:
        config_dict: The raw configuration dictionary.

    Returns:
        A validated ConfigModel instance.

    Raises:
        ConfigValidationError: If validation fails.
    """
    try:
        # Handle potential alias usage for sdc_rules keys
        if 'sdc_rules' in config_dict and isinstance(config_dict['sdc_rules'], dict):
            rules = config_dict['sdc_rules']
            # Map potential user-facing keys to internal Pydantic field names if needed
            # Pydantic handles alias mapping automatically if alias is set in Field
            pass # Pydantic should handle aliases defined in SDCRules

        validated_config = ConfigModel.model_validate(config_dict)
        return validated_config
    except ValidationError as e:
        # Raise a custom exception with a more user-friendly message potentially
        error_messages = "\n".join([f"- {err['loc']}: {err['msg']}" for err in e.errors()])
        raise ConfigValidationError(f"Configuration validation failed:\n{error_messages}") from e
    except Exception as e: # Catch other potential errors during validation
        raise ConfigValidationError(f"An unexpected error occurred during configuration validation: {e}") from e