import asyncio
import json
from test_webscraper import test_fetch_finn_data
from test_data_analysis import test_analyze_car_market

class SimpleMCPClient:
    """Simple MCP client for testing without full protocol"""
    
    async def call_web_scraper(self, tool_name: str, arguments: dict):
        """Simulate calling web scraper MCP server"""
        if tool_name == "fetch_finn_data":
            return await test_fetch_finn_data(
                arguments["url"], 
                arguments.get("max_pages", 1)
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def call_data_analyzer(self, tool_name: str, arguments: dict):
        """Simulate calling data analyzer MCP server"""
        if tool_name == "analyze_car_market":
            return await test_analyze_car_market(
                arguments["cars_data"],
                arguments.get("analysis_type", "basic")
            )
        elif tool_name == "find_best_deals":
            return await test_find_best_deals(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

async def test_find_best_deals(arguments: dict):
    """Test version of find_best_deals"""
    try:
        cars_data = arguments["cars_data"]
        max_price = arguments.get("max_price")
        max_mileage = arguments.get("max_mileage")  
        min_year = arguments.get("min_year")
        
        import pandas as pd
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
                "success": True,
                "best_deals": best_deals.to_dict('records'),
                "criteria_applied": {
                    "max_price": max_price,
                    "max_mileage": max_mileage,
                    "min_year": min_year
                },
                "total_matches": len(filtered_cars)
            }
        else:
            result = {"success": True, "best_deals": [], "message": "No cars match the criteria"}
            
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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

# Test the complete workflow
async def test_complete_workflow():
    client = SimpleMCPClient()
    
    # Test URL
    finn_url = "https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"
    
    print("🕷️ Testing web scraper...")
    scraper_result = await client.call_web_scraper("fetch_finn_data", {
        "url": finn_url,
        "max_pages": 1
    })
    
    if scraper_result.get("success"):
        print(f"✅ Web scraper found {scraper_result['cars_found']} cars")
        
        print("\n📊 Testing data analyzer...")
        analysis_result = await client.call_data_analyzer("analyze_car_market", {
            "cars_data": scraper_result["data"],
            "analysis_type": "detailed"
        })
        
        if analysis_result.get("success"):
            print("✅ Data analysis completed")
            avg_price = analysis_result.get('avg_price')
            if avg_price:
                print(f"📈 Average price: {avg_price:,.0f} kr")
            print(f"🚗 Available cars: {analysis_result.get('available_cars', 'N/A')}")
            
            price_range = analysis_result.get('price_range', {})
            if price_range.get('min') and price_range.get('max'):
                print(f"💰 Price range: {price_range['min']:,.0f} - {price_range['max']:,.0f} kr")
            
            avg_mileage = analysis_result.get('avg_mileage')
            if avg_mileage:
                print(f"📏 Average mileage: {avg_mileage:,.0f} km")
            
            avg_age = analysis_result.get('avg_age')
            if avg_age:
                print(f"📅 Average age: {avg_age:.1f} years")
            
            price_per_km = analysis_result.get('price_per_km')
            if price_per_km:
                print(f"💲 Average price per km: {price_per_km:.2f} kr/km")
            
            # Test best deals finder
            print("\n🎯 Finding best deals...")
            best_deals_result = await client.call_data_analyzer("find_best_deals", {
                "cars_data": scraper_result["data"],
                "max_price": 360000,  # Increased from 350000
                "max_mileage": 150000,  # Increased from 80000
                "min_year": 2019  # Lowered from 2020
            })
            
            if best_deals_result.get("success"):
                deals = best_deals_result.get("best_deals", [])
                total_matches = best_deals_result.get("total_matches", 0)
                print(f"✅ Found {total_matches} cars matching criteria, showing top {len(deals)} deals")
                
                if deals:
                    print("\n🏆 Top Best Deals:")
                    for i, deal in enumerate(deals, 1):
                        print(f"{i}. {deal['name']} ({deal['year']}) - {deal['price']:,.0f} kr")
                        print(f"   📏 {deal['mileage']:,.0f} km | 🏃 {deal['km_per_year']:,.0f} km/year | 📊 Score: {deal['value_score']}")
                        print(f"   🔗 {deal['link']}")
                        print()
                else:
                    print("No cars match the specified criteria.")
            else:
                print(f"❌ Best deals error: {best_deals_result.get('error')}")
                
        else:
            print(f"❌ Analysis error: {analysis_result.get('error')}")
    else:
        print(f"❌ Scraper error: {scraper_result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())