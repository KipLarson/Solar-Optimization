"""Generate full-year (8760 hours) test data"""
import pandas as pd
import numpy as np
import os

# Create test_data directory
os.makedirs("test_data", exist_ok=True)


def generate_full_year_pv_production():
    """
    Generate realistic full-year PV production profile (8760 hours).
    
    Creates a sinusoidal pattern that varies by season and time of day.
    """
    hours = range(1, 8761)
    
    production = []
    for hour in hours:
        # Day of year (1-365)
        day_of_year = ((hour - 1) // 24) + 1
        
        # Hour of day (0-23)
        hour_of_day = (hour - 1) % 24
        
        # Seasonal variation (winter = lower, summer = higher)
        # Approximate: peak in June (day ~172), minimum in December
        seasonal_factor = 0.7 + 0.3 * np.cos(2 * np.pi * (day_of_year - 172) / 365)
        
        # Daily pattern: zero at night, peaks at noon
        if 6 <= hour_of_day <= 18:  # Daytime (6 AM to 6 PM)
            # Sinusoidal curve peaking at hour 12 (noon)
            normalized_hour = (hour_of_day - 6) / 12  # 0 to 1 over 12 hours
            daily_pattern = np.sin(normalized_hour * np.pi)
            # Peak production ~0.9 MWh/MW on a good summer day
            prod = daily_pattern * 0.9 * seasonal_factor
        else:
            prod = 0.0
        
        production.append(max(0.0, prod))  # Ensure non-negative
    
    df = pd.DataFrame({
        'Hour': hours,
        'Production_MWh_per_MW': production
    })
    
    return df


def generate_full_year_pricing():
    """
    Generate realistic full-year pricing profile (8760 hours).
    
    Creates prices with daily patterns (higher during peak hours)
    and some variability.
    """
    hours = range(1, 8761)
    np.random.seed(42)  # For reproducibility
    
    prices = []
    for hour in hours:
        hour_of_day = (hour - 1) % 24
        
        # Base price: $40/MWh
        base_price = 40.0
        
        # Peak hours (10 AM - 8 PM): higher prices
        if 10 <= hour_of_day <= 20:
            peak_multiplier = 1.5  # $60/MWh during peak
        else:
            peak_multiplier = 0.75  # $30/MWh off-peak
        
        # Add some random variation (±10%)
        variation = np.random.uniform(0.9, 1.1)
        
        price = base_price * peak_multiplier * variation
        prices.append(price)
    
    df = pd.DataFrame({
        'Hour': hours,
        'Price_per_MWh': prices
    })
    
    return df


if __name__ == "__main__":
    print("Generating full-year (8760 hours) test data...")
    
    pv_df = generate_full_year_pv_production()
    pricing_df = generate_full_year_pricing()
    
    # Save to CSV
    pv_file = "test_data/pv_production_8760h.csv"
    pricing_file = "test_data/pricing_8760h.csv"
    
    pv_df.to_csv(pv_file, index=False)
    pricing_df.to_csv(pricing_file, index=False)
    
    print(f"Created {pv_file}")
    print(f"Created {pricing_file}")
    print(f"\nPV Production Stats:")
    print(f"  Total hours: {len(pv_df)}")
    print(f"  Min: {pv_df['Production_MWh_per_MW'].min():.4f} MWh/MW")
    print(f"  Max: {pv_df['Production_MWh_per_MW'].max():.4f} MWh/MW")
    print(f"  Mean: {pv_df['Production_MWh_per_MW'].mean():.4f} MWh/MW")
    print(f"\nPricing Stats:")
    print(f"  Total hours: {len(pricing_df)}")
    print(f"  Min: ${pricing_df['Price_per_MWh'].min():.2f}/MWh")
    print(f"  Max: ${pricing_df['Price_per_MWh'].max():.2f}/MWh")
    print(f"  Mean: ${pricing_df['Price_per_MWh'].mean():.2f}/MWh")
