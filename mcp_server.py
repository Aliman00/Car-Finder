import json
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class McpServerConfig:
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = None

class McpManager:
    def __init__(self):
        self.servers = {}
        
    def add_server(self, config: McpServerConfig):
        self.servers[config.name] = config
        
    def get_mcp_tools_config(self) -> List[Dict[str, Any]]:
        """Generate MCP tools configuration for OpenAI client"""
        tools = []
        for server_name, config in self.servers.items():
            tools.append({
                "type": "mcp",
                "mcp": {
                    "server_name": server_name,
                    "server": {
                        "command": config.command,
                        "args": config.args,
                        "env": config.env or {}
                    }
                }
            })
        return tools

# Configure your MCP servers with correct paths
mcp_manager = McpManager()

# Web scraping server
mcp_manager.add_server(McpServerConfig(
    name="web_scraper",
    command="python",
    args=["webscraper.py"],  # Direct file reference
    env={"USER_AGENT": "Car-Finder/1.0"}
))

# Data analysis server
mcp_manager.add_server(McpServerConfig(
    name="data_analyzer", 
    command="python",
    args=["data-analysis.py"]  # Direct file reference
))

# Car database server
mcp_manager.add_server(McpServerConfig(
    name="car_database",
    command="python",
    args=["-m", "mcp_servers.car_database"]
))