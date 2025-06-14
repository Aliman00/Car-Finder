import streamlit as st
import asyncio
from mcp_llm_client import MCPLLMClient

st.set_page_config(
    page_title="🚗 Car Finder MCP + LLM",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Car Finder with MCP + LLM")
st.markdown("**AI-powered car analysis using Model Context Protocol**")

# Initialize session state
if 'llm_client' not in st.session_state:
    st.session_state.llm_client = MCPLLMClient()

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar with examples
st.sidebar.header("🎯 Example Queries")
st.sidebar.markdown("""
Try these example questions:

**📊 Market Analysis:**
- "Analyser bilmarkedet på denne lenken: [Finn.no URL]"
- "Hva er gjennomsnittsprisen på Toyota RAV4?"

**🔍 Find Best Deals:**
- "Finn de beste tilbudene under 350000 kr"
- "Hvilke biler har lavest km/år ratio?"

**🤔 General Questions:**
- "Er dette et godt tidspunkt å kjøpe bil?"
- "Hvilken bil anbefaler du for en familie?"
""")

if st.sidebar.button("🔄 Clear Conversation"):
    st.session_state.conversation_history = []
    st.session_state.messages = []
    st.rerun()

# Default Finn.no URL
default_url = "https://www.finn.no/mobility/search/car?location=20007&location=20061&location=20003&location=20002&model=1.813.3074&model=1.813.2000660&price_to=380000&sales_form=1&sort=MILEAGE_ASC&stored-id=80260642&wheel_drive=2&year_from=2019"

st.sidebar.markdown("---")
st.sidebar.markdown("**🔗 Quick Analysis:**")
if st.sidebar.button("📊 Analyze Default Search", use_container_width=True):
    quick_query = f"Kan du analysere bilmarkedet på denne Finn.no-lenken: {default_url}"
    st.session_state.messages.append({"role": "user", "content": quick_query, "auto": True})
    st.rerun()

# Display chat messages
st.header("💬 Chat with AI Car Expert")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            st.markdown(message["content"])
            if "tools_used" in message and message["tools_used"]:
                with st.expander(f"🔧 MCP Tools Used: {', '.join(message['tools_used'])}"):
                    st.write("The AI used these MCP tools to generate this response:")
                    for tool in message["tools_used"]:
                        st.write(f"- `{tool}`")

# Chat input
if prompt := st.chat_input("Spør om bilmarkedet... (f.eks. 'Analyser denne Finn.no lenken: [URL]')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 AI analyserer med MCP tools..."):
            try:
                # Create event loop for async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    st.session_state.llm_client.chat_with_mcp_tools(
                        prompt, 
                        st.session_state.conversation_history
                    )
                )
                
                # Display response
                st.markdown(result["response"])
                
                # Update conversation history
                st.session_state.conversation_history = result["conversation_history"]
                
                # Add to messages for display
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": result["response"],
                    "tools_used": result.get("tools_used", [])
                })
                
                # Show tools used
                if result.get("tools_used"):
                    with st.expander(f"🔧 MCP Tools Used: {', '.join(result['tools_used'])}"):
                        st.write("The AI used these MCP tools to generate this response:")
                        for tool in result["tools_used"]:
                            st.write(f"- `{tool}`")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                loop.close()

# Handle auto-triggered messages
if st.session_state.messages and st.session_state.messages[-1].get("auto"):
    # Remove the auto flag and process the message
    last_message = st.session_state.messages[-1]
    last_message.pop("auto", None)
    
    # Trigger rerun to process the auto message
    st.rerun()

# Information section
with st.expander("ℹ️ How MCP + LLM Works"):
    st.markdown("""
    This application combines **Large Language Models** with **Model Context Protocol** for intelligent car analysis:
    
    **🧠 LLM (AI Brain):**
    - Understands your questions in natural Norwegian
    - Decides which tools to use
    - Interprets results and provides insights
    
    **🔧 MCP Tools:**
    - `fetch_finn_data`: Scrapes Finn.no car listings
    - `analyze_car_market`: Performs statistical analysis  
    - `find_best_deals`: Finds optimal car deals
    
    **🎯 The Magic:**
    1. You ask a question in Norwegian
    2. The LLM understands and chooses appropriate MCP tools
    3. Tools fetch and analyze real data
    4. LLM interprets results and gives you actionable advice
    
    This is the **true power of MCP** - intelligent tool orchestration by AI!
    """)

st.markdown("---")
st.markdown("🚗 **Real MCP + LLM Architecture** | AI decides which tools to use | Built with OpenAI + Streamlit")