import asyncio
import json
import pandas as pd
import numpy as np
from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List, Dict, Any

app = Server("data_analyzer")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="analyze_car_market",
            description="Perform comprehensive market analysis on car data",
            inputSchema={
                "type": "object",
                "properties": {
                    "cars_data": {"type": "array", "description": "Array of car objects"},
                    "analysis_type": {"type": "string", "enum": ["basic", "detailed", "investment"], "default": "basic"}
                },
                "required": ["cars_data"]
            }
        ),
        Tool(
            name="find_best_deals",
            description="Find the best car deals based on various criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "cars_data": {"type": "array"},
                    "max_price": {"type": "integer"},
                    "max_mileage": {"type": "integer"},
                    "min_year": {"type": "integer"}
                },
                "required": ["cars_data"]
            }
        ),
        Tool(
            name="predict_depreciation",
            description="Predict car value depreciation based on historical data",
            inputSchema={
                "type": "object",
                "properties": {
                    "car_data": {"type": "object"},
                    "years_ahead": {"type": "integer", "default": 3}
                },
                "required": ["car_data"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analyze_car_market":
        return await analyze_car_market(arguments["cars_data"], arguments.get("analysis_type", "basic"))
    elif name == "find_best_deals":
        return await find_best_deals(arguments)
    elif name == "predict_depreciation":
        return await predict_depreciation(arguments["car_data"], arguments.get("years_ahead", 3))

async def analyze_car_market(cars_data: List[Dict], analysis_type: str = "basic"):
    try:
        df = pd.DataFrame(cars_data)
        
        # Filter out sold cars for price analysis
        available_cars = df[df['price'] != 'Solgt'].copy()
        available_cars['price'] = pd.to_numeric(available_cars['price'], errors='coerce')
        
        analysis = {
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
            
        return [TextContent(
            type="text",
            text=json.dumps(analysis, ensure_ascii=False, default=str)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

def calculate_price_per_km(df):
    """Calculate price per kilometer for available cars"""
    if 'price' in df.columns and 'mileage' in df.columns:
        valid_data = df[(df['price'].notna()) & (df['mileage'].notna()) & (df['mileage'] > 0)]
        if not valid_data.empty:
            valid_data = valid_data.copy()
            valid_data['price_per_km'] = valid_data['price'] / valid_data['mileage']
            return float(valid_data['price_per_km'].mean())
    return None

async def find_best_deals(arguments: dict):
    """Find best car deals based on criteria"""
    try:
        cars_data = arguments["cars_data"]
        max_price = arguments.get("max_price")
        max_mileage = arguments.get("max_mileage")  
        min_year = arguments.get("min_year")
        
        df = pd.DataFrame(cars_data)
        
        # Filter available cars
        filtered_cars = df[df['price'] != 'Solgt'].copy()
        filtered_cars['price'] = pd.to_numeric(filtered_cars['price'], errors='coerce')
        
        # Apply filters
        if max_price:
            filtered_cars = filtered_cars[filtered_cars['price'] <= max_price]
        if max_mileage:
            filtered_cars = filtered_cars[filtered_cars['mileage'] <= max_mileage]
        if min_year:
            filtered_cars = filtered_cars[filtered_cars['year'] >= min_year]
            
        # Calculate value scores
        if not filtered_cars.empty:
            filtered_cars['value_score'] = calculate_value_score(filtered_cars)
            best_deals = filtered_cars.nlargest(5, 'value_score')
            
            result = {
                "best_deals": best_deals.to_dict('records'),
                "criteria_applied": {
                    "max_price": max_price,
                    "max_mileage": max_mileage,
                    "min_year": min_year
                },
                "total_matches": len(filtered_cars)
            }
        else:
            result = {"best_deals": [], "message": "No cars match the criteria"}
            
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, default=str)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

async def predict_depreciation(car_data: dict, years_ahead: int = 3):
    """Predict car depreciation"""
    try:
        current_age = car_data.get('age', 0)
        current_price = car_data.get('price')
        
        if not isinstance(current_price, (int, float)):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Invalid price data for depreciation calculation"})
            )]
            
        # Simple depreciation model (can be enhanced with ML)
        annual_depreciation_rate = 0.15  # 15% per year typical for cars
        
        predictions = []
        for year in range(1, years_ahead + 1):
            future_age = current_age + year
            depreciation_factor = (1 - annual_depreciation_rate) ** year
            predicted_value = current_price * depreciation_factor
            
            predictions.append({
                "year": year,
                "future_age": future_age,
                "predicted_value": round(predicted_value),
                "value_loss": round(current_price - predicted_value),
                "depreciation_rate": round((1 - depreciation_factor) * 100, 1)
            })
            
        result = {
            "car_info": car_data,
            "current_price": current_price,
            "predictions": predictions,
            "model_used": "Linear depreciation at 15% annually"
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, default=str)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

def calculate_value_score(df):
    """Calculate value score for cars"""
    scores = []
    for _, car in df.iterrows():
        score = 0
        
        # Lower km/year is better
        if car.get('km_per_year'):
            if car['km_per_year'] < 15000:
                score += 3
            elif car['km_per_year'] < 20000:
                score += 2
            else:
                score += 1
                
        # Newer cars get higher scores
        if car.get('age'):
            if car['age'] < 3:
                score += 3
            elif car['age'] < 5:
                score += 2
            else:
                score += 1
                
        # Price efficiency (lower price per km is better)
        if car.get('price') and car.get('mileage') and car['mileage'] > 0:
            price_per_km = car['price'] / car['mileage']
            if price_per_km < 2:
                score += 3
            elif price_per_km < 3:
                score += 2
            else:
                score += 1
                
        scores.append(score)
    
    return scores

if __name__ == "__main__":
    import sys
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, 
                write_stream, 
                app.create_initialization_options()
            )
    
    asyncio.run(main())