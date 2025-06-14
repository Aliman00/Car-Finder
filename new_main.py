import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from mcp_server import mcp_manager  # Fixed import

load_dotenv()

# Initialize OpenAI client with MCP support
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

class CarFinderMCP:
    def __init__(self):
        self.client = client
        self.mcp_tools = mcp_manager.get_mcp_tools_config()
        
    async def fetch_and_analyze_cars(self, finn_url: str, analysis_type: str = "detailed"):
        """Fetch cars using MCP web scraper and analyze using MCP data analyzer"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a car market expert. Use the available MCP tools to fetch and analyze car data from Finn.no."
            },
            {
                "role": "user", 
                "content": f"Please fetch car data from {finn_url} and perform a {analysis_type} market analysis. Provide insights and recommendations in Norwegian."
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=messages,
                tools=self.mcp_tools,
                tool_choice="auto"
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error during analysis: {str(e)}"
    
    async def find_best_deals(self, cars_data: list, criteria: dict):
        """Find best deals using MCP data analyzer"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a car buying advisor. Use MCP tools to find the best car deals based on the given criteria."
            },
            {
                "role": "user",
                "content": f"Find the best car deals from the provided data with criteria: {criteria}. Explain why these are good deals in Norwegian."
            }
        ]
        
        # Add the cars data as context
        messages.append({
            "role": "user",
            "content": f"Car data: {cars_data}"
        })
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free", 
                messages=messages,
                tools=self.mcp_tools,
                tool_choice="auto"
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error finding deals: {str(e)}"

# Example usage
if __name__ == "__main__":
    car_finder = CarFinderMCP()
    
    # Example Finn.no URL from your current code
    finn_url = "https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"
    
    async def main():
        result = await car_finder.fetch_and_analyze_cars(finn_url, "detailed")
        print(result)
    
    asyncio.run(main())