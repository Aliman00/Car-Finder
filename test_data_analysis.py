import pandas as pd
import numpy as np

async def test_analyze_car_market(cars_data, analysis_type="basic"):
    """Test version of analyze_car_market without MCP"""
    try:
        df = pd.DataFrame(cars_data)
        
        # Filter out sold cars for price analysis
        available_cars = df[df['price'] != 'Solgt'].copy()
        available_cars['price'] = pd.to_numeric(available_cars['price'], errors='coerce')
        
        analysis = {
            "success": True,
            "total_cars": len(df),
            "available_cars": len(available_cars),
            "sold_cars": len(df[df['price'] == 'Solgt']),
            "avg_price": float(available_cars['price'].mean()) if not available_cars.empty else None,
            "median_price": float(available_cars['price'].median()) if not available_cars.empty else None,
            "price_range": {
                "min": float(available_cars['price'].min()) if not available_cars.empty else None,
                "max": float(available_cars['price'].max()) if not available_cars.empty else None
            },
            "avg_mileage": float(df['mileage'].mean()) if 'mileage' in df.columns else None,
            "avg_age": float(df['age'].mean()) if 'age' in df.columns else None
        }
        
        if analysis_type == "detailed":
            analysis.update({
                "mileage_distribution": df['mileage'].describe().to_dict() if 'mileage' in df.columns else None,
                "year_distribution": df['year'].value_counts().to_dict() if 'year' in df.columns else None,
                "price_per_km": calculate_price_per_km(available_cars)
            })
            
        return analysis
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def calculate_price_per_km(df):
    """Calculate price per kilometer for available cars"""
    if 'price' in df.columns and 'mileage' in df.columns:
        valid_data = df[(df['price'].notna()) & (df['mileage'].notna()) & (df['mileage'] > 0)]
        if not valid_data.empty:
            valid_data = valid_data.copy()
            valid_data['price_per_km'] = valid_data['price'] / valid_data['mileage']
            return float(valid_data['price_per_km'].mean())
    return None