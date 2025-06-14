import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from test_mcp_client import SimpleMCPClient

st.set_page_config(
    page_title="🚗 Car Finder MCP",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ff6b6b;
}

.deal-card {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.success-badge {
    background-color: #d4edda;
    color: #155724;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("🚗 Car Finder with MCP Architecture")
st.markdown("**Next-generation car analysis powered by Model Context Protocol**")

# Initialize session state
if 'mcp_client' not in st.session_state:
    st.session_state.mcp_client = SimpleMCPClient()

if 'cars_data' not in st.session_state:
    st.session_state.cars_data = None

if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# Sidebar configuration
st.sidebar.header("🔧 MCP Configuration")

# Show MCP status
st.sidebar.markdown("""
<div class="metric-card">
<h4>🔗 MCP Servers Status</h4>
<span class="success-badge">✅ Web Scraper</span><br>
<span class="success-badge">✅ Data Analyzer</span><br>
<span class="success-badge">✅ Deal Finder</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Input section
st.sidebar.header("📋 Search Configuration")

finn_url = st.sidebar.text_input(
    "🔗 Finn.no URL:",
    value="https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019",
    help="Paste a Finn.no search URL here"
)

max_pages = st.sidebar.slider("📄 Max pages to scrape:", 1, 5, 1)

analysis_type = st.sidebar.selectbox(
    "📊 Analysis type:",
    ["basic", "detailed", "investment"],
    index=1
)

# Fetch data button
if st.sidebar.button("🚀 Fetch & Analyze Data", type="primary", use_container_width=True):
    if finn_url:
        with st.spinner("🕷️ MCP Web Scraper is fetching data..."):
            try:
                # Create new event loop for asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Fetch data using MCP
                scraper_result = loop.run_until_complete(
                    st.session_state.mcp_client.call_web_scraper("fetch_finn_data", {
                        "url": finn_url,
                        "max_pages": max_pages
                    })
                )
                
                if scraper_result.get("success"):
                    st.session_state.cars_data = scraper_result["data"]
                    st.sidebar.success(f"✅ Found {scraper_result['cars_found']} cars!")
                    
                    # Analyze data using MCP
                    with st.spinner("📊 MCP Data Analyzer is processing..."):
                        analysis_result = loop.run_until_complete(
                            st.session_state.mcp_client.call_data_analyzer("analyze_car_market", {
                                "cars_data": st.session_state.cars_data,
                                "analysis_type": analysis_type
                            })
                        )
                        
                        if analysis_result.get("success"):
                            st.session_state.analysis_data = analysis_result
                            st.sidebar.success("✅ Analysis completed!")
                        else:
                            st.sidebar.error(f"❌ Analysis failed: {analysis_result.get('error')}")
                else:
                    st.sidebar.error(f"❌ Scraping failed: {scraper_result.get('error')}")
                    
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
            finally:
                loop.close()
    else:
        st.sidebar.warning("⚠️ Please enter a Finn.no URL")

# Main content area
if st.session_state.cars_data and st.session_state.analysis_data:
    
    # Overview metrics
    st.header("📊 Market Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🚗 Total Cars",
            st.session_state.analysis_data.get('total_cars', 0),
            delta=f"{st.session_state.analysis_data.get('available_cars', 0)} available"
        )
    
    with col2:
        avg_price = st.session_state.analysis_data.get('avg_price')
        if avg_price:
            st.metric(
                "💰 Avg Price",
                f"{avg_price:,.0f} kr"
            )
    
    with col3:
        avg_mileage = st.session_state.analysis_data.get('avg_mileage')
        if avg_mileage:
            st.metric(
                "📏 Avg Mileage", 
                f"{avg_mileage:,.0f} km"
            )
    
    with col4:
        avg_age = st.session_state.analysis_data.get('avg_age')
        if avg_age:
            st.metric(
                "📅 Avg Age",
                f"{avg_age:.1f} years"
            )
    
    # Data visualization
    st.header("📈 Market Analysis")
    
    df = pd.DataFrame(st.session_state.cars_data)
    available_df = df[df['price'] != 'Solgt'].copy()
    available_df['price'] = pd.to_numeric(available_df['price'], errors='coerce')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Price distribution
        if not available_df.empty:
            fig_price = px.histogram(
                available_df, 
                x='price', 
                nbins=20,
                title="💰 Price Distribution",
                labels={'price': 'Price (kr)', 'count': 'Number of Cars'}
            )
            fig_price.update_layout(showlegend=False)
            st.plotly_chart(fig_price, use_container_width=True)
    
    with col2:
        # Mileage vs Price scatter
        if not available_df.empty and 'mileage' in available_df.columns:
            fig_scatter = px.scatter(
                available_df,
                x='mileage',
                y='price', 
                color='year',
                title="📏 Mileage vs Price",
                labels={'mileage': 'Mileage (km)', 'price': 'Price (kr)', 'year': 'Year'},
                hover_data=['name', 'age']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Best deals finder
    st.header("🎯 Find Best Deals")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        max_price_filter = st.number_input(
            "💰 Max Price (kr)",
            min_value=0,
            max_value=500000,
            value=370000,
            step=10000
        )
    
    with col2:
        max_mileage_filter = st.number_input(
            "📏 Max Mileage (km)",
            min_value=0,
            max_value=300000,
            value=150000,
            step=10000
        )
    
    with col3:
        min_year_filter = st.number_input(
            "📅 Min Year",
            min_value=2015,
            max_value=2025,
            value=2019,
            step=1
        )
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        find_deals_btn = st.button("🔍 Find Best Deals", type="secondary", use_container_width=True)
    
    if find_deals_btn:
        with st.spinner("🎯 MCP Deal Finder is analyzing..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                deals_result = loop.run_until_complete(
                    st.session_state.mcp_client.call_data_analyzer("find_best_deals", {
                        "cars_data": st.session_state.cars_data,
                        "max_price": max_price_filter,
                        "max_mileage": max_mileage_filter,
                        "min_year": min_year_filter
                    })
                )
                
                if deals_result.get("success"):
                    deals = deals_result.get("best_deals", [])
                    total_matches = deals_result.get("total_matches", 0)
                    
                    st.success(f"✅ Found {total_matches} cars matching criteria, showing top {len(deals)} deals")
                    
                    if deals:
                        st.markdown("### 🏆 Top Best Deals")
                        
                        for i, deal in enumerate(deals, 1):
                            with st.container():
                                st.markdown(f"""
                                <div class="deal-card">
                                <h4>#{i} {deal['name']} ({deal['year']})</h4>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong>💰 {deal['price']:,.0f} kr</strong><br>
                                        📏 {deal['mileage']:,.0f} km | 🏃 {deal['km_per_year']:,.0f} km/year<br>
                                        📊 Value Score: <strong>{deal['value_score']}</strong>
                                    </div>
                                    <div>
                                        <a href="{deal['link']}" target="_blank" style="text-decoration: none;">
                                            <button style="background-color: #ff6b6b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer;">
                                                🔗 View Car
                                            </button>
                                        </a>
                                    </div>
                                </div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("🔍 No cars match the specified criteria. Try adjusting your filters.")
                else:
                    st.error(f"❌ Deal finder error: {deals_result.get('error')}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                loop.close()
    
    # Raw data table
    st.header("📋 All Cars Data")
    
    if st.checkbox("🔍 Show detailed data table"):
        display_df = df.copy()
        
        # Format numeric columns
        if 'price' in display_df.columns:
            display_df['price_formatted'] = display_df['price'].apply(
                lambda x: f"{x:,.0f} kr" if isinstance(x, (int, float)) else str(x)
            )
        
        if 'mileage' in display_df.columns:
            display_df['mileage_formatted'] = display_df['mileage'].apply(
                lambda x: f"{x:,.0f} km" if pd.notna(x) else "N/A"
            )
        
        # Select columns to display
        display_columns = ['name', 'year', 'price_formatted', 'mileage_formatted', 'km_per_year', 'additional_info', 'link']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        st.dataframe(
            display_df[available_columns],
            use_container_width=True,
            hide_index=True
        )

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to Car Finder MCP! 🚗
    
    This application uses **Model Context Protocol (MCP)** architecture to provide advanced car market analysis.
    
    ### 🛠️ MCP Architecture Features:
    
    - **🕷️ Web Scraper Server**: Advanced Finn.no data extraction with multi-page support
    - **📊 Data Analysis Server**: Comprehensive market statistics and insights  
    - **🎯 Deal Finder Server**: AI-powered value scoring and recommendation engine
    - **⚡ Real-time Processing**: Live data fetching and analysis
    - **🔧 Modular Design**: Each server operates independently for maximum reliability
    
    ### 🚀 Getting Started:
    
    1. Enter a Finn.no search URL in the sidebar
    2. Configure your search parameters  
    3. Click "Fetch & Analyze Data" to start the MCP workflow
    4. Explore market insights and find the best deals!
    
    ---
    
    **🔗 Example Finn.no URL structure:**
    ```
    https://www.finn.no/mobility/search/car?model=1.813.3074&price_to=350000&year_from=2019
    ```
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
🚗 Car Finder MCP | Powered by Model Context Protocol | Built with Streamlit
</div>
""", unsafe_allow_html=True)