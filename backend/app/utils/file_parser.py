"""CSV file parsing utilities"""
import pandas as pd
from typing import Tuple
import io


def parse_pv_production_csv(file_content: bytes) -> pd.Series:
    """
    Parse PV production profile CSV file.
    
    Expected format:
    Hour,Production_MWh_per_MW
    1,0.0
    2,0.0
    ...
    8760,0.5
    
    Args:
        file_content: CSV file content as bytes
        
    Returns:
        pandas Series with production values (indexed by hour 1-8760)
        
    Raises:
        ValueError: If file format is invalid
    """
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        
        # Validate required columns
        if 'Hour' not in df.columns or 'Production_MWh_per_MW' not in df.columns:
            raise ValueError("CSV must contain 'Hour' and 'Production_MWh_per_MW' columns")
        
        # Validate we have 8760 hours
        if len(df) != 8760:
            raise ValueError(f"Expected 8760 hours, got {len(df)}")
        
        # Validate hour range
        if df['Hour'].min() != 1 or df['Hour'].max() != 8760:
            raise ValueError("Hours must be in range 1-8760")
        
        # Validate no negative production
        if (df['Production_MWh_per_MW'] < 0).any():
            raise ValueError("Production values cannot be negative")
        
        # Set hour as index and return production series
        df = df.set_index('Hour')
        production = df['Production_MWh_per_MW']
        
        return production
        
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing PV production CSV: {str(e)}")


def parse_pricing_csv(file_content: bytes) -> pd.Series:
    """
    Parse nodal pricing CSV file.
    
    Expected format:
    Hour,Price_per_MWh
    1,45.2
    2,42.1
    ...
    8760,38.5
    
    Args:
        file_content: CSV file content as bytes
        
    Returns:
        pandas Series with price values (indexed by hour 1-8760)
        
    Raises:
        ValueError: If file format is invalid
    """
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        
        # Validate required columns
        if 'Hour' not in df.columns or 'Price_per_MWh' not in df.columns:
            raise ValueError("CSV must contain 'Hour' and 'Price_per_MWh' columns")
        
        # Validate we have 8760 hours
        if len(df) != 8760:
            raise ValueError(f"Expected 8760 hours, got {len(df)}")
        
        # Validate hour range
        if df['Hour'].min() != 1 or df['Hour'].max() != 8760:
            raise ValueError("Hours must be in range 1-8760")
        
        # Validate no negative prices (prices can be negative in some markets, but we'll warn)
        if (df['Price_per_MWh'] < 0).any():
            # Just log a warning, don't fail - negative prices are valid in some markets
            pass
        
        # Set hour as index and return price series
        df = df.set_index('Hour')
        prices = df['Price_per_MWh']
        
        return prices
        
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing pricing CSV: {str(e)}")


def validate_csv_files(pv_production: bytes, pricing: bytes) -> Tuple[pd.Series, pd.Series]:
    """
    Validate and parse both CSV files.
    
    Args:
        pv_production: PV production CSV file content
        pricing: Pricing CSV file content
        
    Returns:
        Tuple of (pv_production_series, pricing_series)
    """
    pv_series = parse_pv_production_csv(pv_production)
    price_series = parse_pricing_csv(pricing)
    
    return pv_series, price_series
