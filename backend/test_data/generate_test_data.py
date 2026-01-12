"""Generate test CSV files for testing optimization"""
import pandas as pd
import numpy as np
import os

# Create test_data directory
os.makedirs("test_data", exist_ok=True)


def generate_pv_production_profile(num_hours=24):
    """
    Generate a simple PV production profile.
    
    For testing, creates a sinusoidal curve peaking at noon.
    
    Args:
        num_hours: Number of hours in profile (default 24 for one day)
    """
    hours = range(1, num_hours + 1)
    
    # Simple sinusoidal curve: zero at night, peaks at midday
    # Assumes hour 12 is noon
    production = []
    for hour in hours:
        if 6 <= hour <= 18:  # Daytime hours (6 AM to 6 PM)
            # Sinusoidal curve peaking at hour 12 (noon)
            normalized_hour = (hour - 6) / 12  # 0 to 1 over 12 hours
            prod = np.sin(normalized_hour * np.pi) * 0.8  # Peak of 0.8 MWh per MW
        else:
            prod = 0.0
        production.append(prod)
    
    df = pd.DataFrame({
        'Hour': hours,
        'Production_MWh_per_MW': production
    })
    
    return df


def generate_pricing_profile(num_hours=24):
    """
    Generate a simple pricing profile.
    
    Creates prices that vary by time of day (higher during peak hours).
    
    Args:
        num_hours: Number of hours in profile (default 24 for one day)
    """
    hours = range(1, num_hours + 1)
    
    # Base price: $40/MWh
    # Peak hours (10 AM - 8 PM): $60/MWh
    # Off-peak: $30/MWh
    prices = []
    for hour in hours:
        if 10 <= hour <= 20:  # Peak hours
            price = 60.0
        else:
            price = 30.0
        prices.append(price)
    
    df = pd.DataFrame({
        'Hour': hours,
        'Price_per_MWh': prices
    })
    
    return df


if __name__ == "__main__":
    # Generate small test dataset (24 hours = 1 day)
    print("Generating test data...")
    
    pv_df = generate_pv_production_profile(num_hours=24)
    pricing_df = generate_pricing_profile(num_hours=24)
    
    # Save to CSV
    pv_file = "test_data/pv_production_test_24h.csv"
    pricing_file = "test_data/pricing_test_24h.csv"
    
    pv_df.to_csv(pv_file, index=False)
    pricing_df.to_csv(pricing_file, index=False)
    
    print(f"Created {pv_file}")
    print(f"Created {pricing_file}")
    print("\nPV Production Profile (first 12 hours):")
    print(pv_df.head(12))
    print("\nPricing Profile (first 12 hours):")
    print(pricing_df.head(12))
