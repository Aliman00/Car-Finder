import streamlit as st
import asyncio
import pandas as pd  # Add this
from new_main import CarFinderMCP  # Fixed import
from mcp_server import mcp_manager  # Fixed import

st.set_page_config(layout="wide")
st.title("🚗 Car Finder with MCP - Next Generation")

# Initialize MCP-powered car finder
if 'car_finder_mcp' not in st.session_state:
    st.session_state.car_finder_mcp = CarFinderMCP()

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

if 'available_tools' not in st.session_state:
    st.session_state.available_tools = []

# Sidebar for MCP configuration
st.sidebar.header("🔧 MCP Configuration")
st.sidebar.write("**Available MCP Servers:**")
for server_name in mcp_manager.servers.keys():
    st.sidebar.write(f"✅ {server_name}")

# Main interface
st.sidebar.header("⚙️ Data Source")
finn_url = st.sidebar.text_input(
    "Finn.no URL:",
    value="https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"
)

analysis_type = st.sidebar.selectbox(
    "Analysis Type:",
    ["basic", "detailed", "investment"],
    index=1
)

if st.sidebar.button("🚀 Fetch & Analyze with MCP", type="primary"):
    if finn_url:
        with st.spinner("Using MCP tools to fetch and analyze data..."):
            try:
                # Run async function in Streamlit
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    st.session_state.car_finder_mcp.fetch_and_analyze_cars(finn_url, analysis_type)
                )
                st.session_state.analysis_results = result
                st.sidebar.success("Analysis completed using MCP!")
            except Exception as e:
                st.sidebar.error(f"MCP Analysis failed: {e}")
            finally:
                loop.close()
    else:
        st.sidebar.warning("Please enter a Finn.no URL")

# Display results
if st.session_state.analysis_results:
    st.header("🤖 MCP-Powered Analysis Results")
    st.markdown(st.session_state.analysis_results)
    
    # Additional MCP tools
    st.header("🔍 Additional MCP Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Find Best Deals"):
            with st.spinner("Finding best deals using MCP..."):
                # This would call the find_best_deals MCP tool
                st.info("Best deals analysis would run here using MCP data analyzer")
    
    with col2:
        if st.button("📈 Predict Depreciation"):
            with st.spinner("Predicting depreciation using MCP..."):
                # This would call the predict_depreciation MCP tool
                st.info("Depreciation prediction would run here using MCP")

else:
    st.info("Click 'Fetch & Analyze with MCP' to start the enhanced analysis using Model Context Protocol")

# Display MCP capabilities
st.header("🛠️ MCP Enhanced Capabilities")
st.write("""
This upgraded version uses **Model Context Protocol (MCP)** to provide:

- **🕷️ Web Scraping Server**: Advanced Finn.no data extraction with pagination support
- **📊 Data Analysis Server**: Sophisticated market analysis and statistical computations  
- **🏎️ Car Database Server**: Store and query historical car data
- **🔮 Prediction Tools**: AI-powered depreciation and market trend predictions
- **⚡ Real-time Updates**: Live data fetching and analysis
- **🎯 Smart Recommendations**: Advanced filtering and deal-finding algorithms

Each MCP server runs independently and can be scaled, updated, or replaced without affecting the main application.
""")