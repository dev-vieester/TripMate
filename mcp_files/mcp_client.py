import os
import sys
from pathlib import Path

import certifi
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openrouter import ChatOpenRouter

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PROJECT_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = PROJECT_DIR / "custom_weather_mcp_server.py"

AVIATION_ENV = os.environ.copy()
AVIATION_ENV["AVIATIONSTACK_API_KEY"] = AVIATION_STACK_API_KEY or ""

WEATHER_ENV = os.environ.copy()
WEATHER_ENV["OPENWEATHER_API_KEY"] = OPENWEATHER_API_KEY or ""

llm = ChatOpenRouter(
    model="inclusionai/ling-3.0-flash-vl",
    temperature=0,
    api_key=OPENROUTER_API_KEY,
)

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            ),
        },
        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp_files",
            ],
            "env": AVIATION_ENV,
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(WEATHER_SERVER_PATH),
            ],
            "env": WEATHER_ENV,
        },
    }
)


async def get_all_tools():
    """
    Load each MCP server separately. A broken server should not prevent the
    remaining working servers from loading.
    """
    all_tools = []

    for server_name in ("tavily", "aviationstack", "weather"):
        try:
            tools = await client.get_tools(server_name=server_name)
            all_tools.extend(tools)

            print(f"\nAvailable tools from {server_name} MCP:\n")
            for tool in tools:
                print(tool.name)
        except Exception as error:
            print(f"\nCould not connect to {server_name} MCP:\n{error}\n")

    return all_tools


search_tool = None


async def initial_mcp():
    global search_tool

    if search_tool is not None:
        return

    tools = await client.get_tools(server_name="tavily")
    tools_by_name = {tool.name: tool for tool in tools}
    search_tool = tools_by_name.get("tavily_search")

    if search_tool is None:
        available_tools = ", ".join(tools_by_name.keys())
        raise RuntimeError(
            "Tavily MCP connected, but the 'tavily_search' tool was not found. "
            f"Available tools: {available_tools or 'none'}"
        )


async def tavily_mcp_search(query: str):
    await initial_mcp()

    return await search_tool.ainvoke(
        {
            "query": query,
        }
    )


aviation_tools = {}


async def initialize_aviation_tools():
    global aviation_tools

    if aviation_tools:
        return

    mcp_tools = await client.get_tools(server_name="aviationstack")
    aviation_tools = {tool.name: tool for tool in mcp_tools}

    if not aviation_tools:
        raise RuntimeError("AviationStack MCP connected but returned no tools.")


async def aviation_mcp_call(tool_name: str, tool_args: dict | None = None):
    await initialize_aviation_tools()

    tool = aviation_tools.get(tool_name)

    if tool is None:
        available_tools = ", ".join(sorted(aviation_tools.keys()))
        raise ValueError(
            f"AviationStack tool '{tool_name}' was not found. "
            f"Available tools: {available_tools or 'none'}"
        )

    return await tool.ainvoke(tool_args or {})


weather_tool = None
forecast_tool = None


async def initialize_weather_tools():
    global weather_tool
    global forecast_tool

    if weather_tool is not None and forecast_tool is not None:
        return

    tools = await client.get_tools(server_name="weather")
    tools_by_name = {tool.name: tool for tool in tools}

    weather_tool = tools_by_name.get("get_current_weather")
    forecast_tool = tools_by_name.get("get_forecast")

    missing_tools = []

    if weather_tool is None:
        missing_tools.append("get_current_weather")

    if forecast_tool is None:
        missing_tools.append("get_forecast")

    if missing_tools:
        available_tools = ", ".join(tools_by_name.keys())
        raise RuntimeError(
            f"Missing Weather MCP tools: {', '.join(missing_tools)}. "
            f"Available tools: {available_tools or 'none'}"
        )


async def weather_mcp_search(city: str):
    await initialize_weather_tools()

    return await weather_tool.ainvoke(
        {
            "city": city,
        }
    )


async def forecast_mcp_search(city: str):
    await initialize_weather_tools()

    return await forecast_tool.ainvoke(
        {
            "city": city,
        }
    )


def extract_destination(query: str):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()
