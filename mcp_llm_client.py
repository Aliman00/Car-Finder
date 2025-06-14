import asyncio
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class MCPLLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        # Define MCP tools for the LLM
        self.mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "fetch_finn_data",
                    "description": "Fetch and parse car data from Finn.no URLs",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "Finn.no search URL"},
                            "max_pages": {"type": "integer", "default": 1, "description": "Maximum pages to scrape"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "analyze_car_market",
                    "description": "Perform comprehensive market analysis on car data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cars_data": {"type": "array", "description": "Array of car objects"},
                            "analysis_type": {"type": "string", "enum": ["basic", "detailed", "investment"], "default": "basic"}
                        },
                        "required": ["cars_data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_best_deals",
                    "description": "Find the best car deals based on various criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cars_data": {"type": "array"},
                            "max_price": {"type": "integer"},
                            "max_mileage": {"type": "integer"},
                            "min_year": {"type": "integer"}
                        },
                        "required": ["cars_data"]
                    }
                }
            }
        ]
    
    async def chat_with_mcp_tools(self, user_message: str, conversation_history: list = None):
        """Let the LLM use MCP tools to answer user questions"""
        
        # Import our MCP functions
        from test_webscraper import test_fetch_finn_data
        from test_data_analysis import test_analyze_car_market
        from test_mcp_client import test_find_best_deals
        
        if conversation_history is None:
            conversation_history = []
        
        # System prompt to guide the LLM
        system_prompt = """You are a Norwegian car market expert assistant. You have access to powerful MCP (Model Context Protocol) tools that can:

1. fetch_finn_data: Scrape car listings from Finn.no
2. analyze_car_market: Perform detailed market analysis 
3. find_best_deals: Find the best car deals based on criteria

When users ask about cars, use these tools intelligently to provide comprehensive analysis. Always respond in Norwegian and provide actionable insights.

If a user provides a Finn.no URL or asks to analyze cars, use the tools in this order:
1. First fetch the data with fetch_finn_data
2. Then analyze it with analyze_car_market  
3. If they want recommendations, use find_best_deals

Be conversational and explain your findings clearly."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=messages,
                tools=self.mcp_tools,
                tool_choice="auto",
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                # Add the assistant's message with tool calls
                messages.append({
                    "role": "assistant", 
                    "content": message.content,
                    "tool_calls": [tc.dict() for tc in message.tool_calls]
                })
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 LLM is calling MCP tool: {function_name}")
                    
                    # Execute the MCP tool
                    if function_name == "fetch_finn_data":
                        result = await test_fetch_finn_data(arguments["url"], arguments.get("max_pages", 1))
                    elif function_name == "analyze_car_market":
                        result = await test_analyze_car_market(arguments["cars_data"], arguments.get("analysis_type", "basic"))
                    elif function_name == "find_best_deals":
                        result = await test_find_best_deals(arguments)
                    else:
                        result = {"error": f"Unknown function: {function_name}"}
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call.id
                    })
                
                # Get final response from LLM after tool execution
                final_response = self.client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=messages,
                    temperature=0.7
                )
                
                return {
                    "response": final_response.choices[0].message.content,
                    "conversation_history": messages,
                    "tools_used": [tc.function.name for tc in message.tool_calls]
                }
            else:
                return {
                    "response": message.content,
                    "conversation_history": messages,
                    "tools_used": []
                }
                
        except Exception as e:
            return {
                "response": f"Beklager, det oppstod en feil: {str(e)}",
                "conversation_history": messages,
                "tools_used": [],
                "error": str(e)
            }

# Test the LLM with MCP tools
async def test_llm_mcp():
    client = MCPLLMClient()
    
    test_queries = [
        "Kan du analysere bilmarkedet på denne Finn.no-lenken: https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019",
        "Finn de beste tilbudene under 350000 kr med maksimalt 100000 km",
        "Hva er gjennomsnittsprisen på Toyota RAV4 i dette markedet?"
    ]
    
    conversation_history = []
    
    for query in test_queries:
        print(f"\n🗣️ User: {query}")
        print("-" * 80)
        
        result = await client.chat_with_mcp_tools(query, conversation_history)
        
        print(f"🤖 Assistant: {result['response']}")
        print(f"🔧 Tools used: {result.get('tools_used', [])}")
        
        conversation_history = result['conversation_history']
        
        # Add some spacing
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_llm_mcp())