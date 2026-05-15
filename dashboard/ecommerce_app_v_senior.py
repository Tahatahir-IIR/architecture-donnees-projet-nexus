import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Market Intelligence | Premium Edition",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN GLASSMORPHISM CSS & ANIMATIONS ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    /* Global Base & Dark Theme */
    .stApp {
        background-color: #0f111a;
        background-image: 
            radial-gradient(at 0% 0%, rgba(17, 24, 39, 1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, rgba(31, 25, 48, 1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, rgba(17, 24, 39, 1) 0, transparent 50%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headings */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h2 { border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; }
    
    /* Metrics & Cards Glassmorphism */
    div[data-testid="metric-container"], .report-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        padding: 24px;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
    }
    div[data-testid="metric-container"]:hover, .report-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    /* Typography inside metrics */
    [data-testid="stMetricLabel"] { font-size: 1rem; color: #94a3b8; font-weight: 500; }
    [data-testid="stMetricValue"] { font-size: 2.5rem; background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; font-family: 'Outfit', sans-serif; }
    
    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.6) 0%, rgba(109, 40, 217, 0.6) 100%);
        backdrop-filter: blur(10px);
        padding: 30px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    .header-banner::before {
        content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: rotateBg 20s linear infinite; z-index: 0;
    }
    @keyframes rotateBg { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .header-content { position: relative; z-index: 1; }
    
    /* Blinking Live Indicator */
    .live-dot {
        height: 10px; width: 10px; background-color: #10b981; border-radius: 50%; display: inline-block;
        margin-right: 8px; box-shadow: 0 0 10px #10b981; animation: blink 1.5s infinite;
    }
    @keyframes blink { 0% { opacity: 1; box-shadow: 0 0 10px #10b981; } 50% { opacity: 0.3; box-shadow: 0 0 2px #10b981; } 100% { opacity: 1; box-shadow: 0 0 10px #10b981; } }

    /* Action Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #6366f1, #8b5cf6);
        color: white; border: none; border-radius: 8px; padding: 10px 24px;
        font-weight: 600; font-family: 'Inter', sans-serif; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6); }

    /* Custom Scrollbar & Sidebar */
    [data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0f111a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }

    /* Catalog Cards */
    .product-price { font-size: 1.4rem; font-weight: 700; background: -webkit-linear-gradient(45deg, #34d399, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .product-btn {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e2e8f0; padding: 6px 16px; border-radius: 20px; text-decoration: none; font-size: 0.85rem;
        transition: all 0.3s ease; display: inline-block; font-weight: 500;
    }
    .product-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; transform: translateY(-2px); border-color: #38bdf8; box-shadow: 0 0 15px rgba(56, 189, 248, 0.3); }
    
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=60)
def load_real_data():
    raw_file = "ecommerce_sales.json"
    if os.path.exists(raw_file):
        with open(raw_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            if not df.empty:
                df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce')
                df = df.dropna(subset=['current_price'])
            return df
    return pd.DataFrame()

df_raw = load_real_data()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.markdown("<h2 style='font-family: Outfit; font-weight: 700; color: #fff; margin-bottom: 20px;'>🌌 DeepFilter™</h2>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        
        price_min = int(df_raw['current_price'].min())
        price_max = int(df_raw['current_price'].max())
        price_range = st.slider("Price Range (DH)", price_min, price_max, (price_min, price_max))
        
        sources = st.multiselect("Data Sources", df_raw['source'].unique(), default=df_raw['source'].unique())
        search_query = st.text_input("🔍 Search AI-Index...")

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.8rem; color: #64748b; text-align: center;'>AI Engine: Active | Status: Optimal</p>", unsafe_allow_html=True)

# --- FILTER LOGIC ---
df = df_raw.copy()
if not df.empty:
    df = df[(df['current_price'] >= price_range[0]) & (df['current_price'] <= price_range[1])]
    df = df[df['source'].isin(sources)]
    if search_query:
        df = df[df['name'].str.contains(search_query, case=False, na=False)]

# --- MAIN DASHBOARD AREA ---
current_time = datetime.now().strftime('%H:%M:%S')
st.markdown(f"""
    <div class='header-banner'>
        <div class='header-content'>
            <h1 style='color: white; margin: 0; font-size: 2.8rem; font-weight: 700; letter-spacing: -1px;'>Nexus Analytics</h1>
            <p style='margin: 8px 0 0 0; font-size: 1.1rem; color: #cbd5e1; font-weight: 300;'>Real-time AI Market Surveillance & Price Intelligence</p>
        </div>
        <div class='header-content' style='text-align: right; background: rgba(0,0,0,0.3); padding: 15px 25px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>
            <span style='font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8;'><span class='live-dot'></span>Live Stream</span><br>
            <span style='font-size: 1.5rem; font-weight: 700; font-family: Outfit; color: #fff;'>{current_time}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

if not df.empty:
    # --- TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Command Center", "🗂️ Actionable Catalog", "⚡ Pulse Alerts", "➕ Add Item"])
    
    with tab1:
        st.markdown("<p style='color:#94a3b8; font-size:1rem; margin-bottom: 20px;'>Macro-level intelligence derived from the current dataset.</p>", unsafe_allow_html=True)
        
        # --- METRICS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Skus Tracked", f"{len(df):,}", "↑ Real-time")
        avg_p = df['current_price'].mean()
        c2.metric("Avg Market Price", f"{avg_p:,.0f} DH", "Market Median")
        cheapest = df.loc[df['current_price'].idxmin()]
        c3.metric("Entry Level Price", f"{cheapest['current_price']:,.0f} DH", "Aggressive")
        premium = df.loc[df['current_price'].idxmax()]
        c4.metric("Premium Ceiling", f"{premium['current_price']:,.0f} DH", "High Margin")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- ADVANCED CHARTS (PLOTLY DARK THEME) ---
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            st.markdown("<div class='report-card'><h3 style='margin-top:0;'>Volatility & Price Distribution</h3>", unsafe_allow_html=True)
            fig_dist = px.histogram(df, x="current_price", color="category", marginal="box", nbins=30,
                                   color_discrete_sequence=['#38bdf8', '#818cf8', '#c084fc', '#f472b6', '#34d399'])
            fig_dist.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                                   height=400, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig_dist, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("<div class='report-card'><h3 style='margin-top:0;'>Market Share by Category</h3>", unsafe_allow_html=True)
            fig_pie = px.sunburst(df, path=['source', 'category'], values='current_price',
                                 color_discrete_sequence=['#3b82f6', '#8b5cf6', '#ec4899', '#10b981'])
            fig_pie.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                                  height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bottom row
        col_bl, col_br = st.columns(2)
        with col_bl:
            st.markdown("<div class='report-card'><h3 style='margin-top:0;'>Competitive Pricing Landscape</h3>", unsafe_allow_html=True)
            df_avg = df.groupby(['category', 'source'])['current_price'].mean().reset_index()
            fig_bar_avg = px.bar(df_avg, x="category", y="current_price", color="source", barmode="group",
                            color_discrete_sequence=['#38bdf8', '#c084fc'])
            fig_bar_avg.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                                      height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_bar_avg, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_br:
            st.markdown("<div class='report-card'><h3 style='margin-top:0;'>Density Heatmap</h3>", unsafe_allow_html=True)
            fig_scatter = px.scatter(df, x="current_price", y="category", color="source", size="current_price", hover_name="name",
                                    color_discrete_sequence=['#34d399', '#f472b6'])
            fig_scatter.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                                      height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<p style='color:#94a3b8; font-size:1rem;'>AI-Curated price comparison engine (Fused Listings).</p>", unsafe_allow_html=True)
        
        def format_stock(val):
            if val in ['In Stock', 'En Stock']:
                return "<span style='color:#34d399; font-size:0.85rem; font-weight:600;'><span class='live-dot' style='width:6px;height:6px;'></span>Available</span>"
            return "<span style='color:#f87171; font-size:0.85rem; font-weight:600;'>Out of Stock</span>"

        # --- FUSE IDENTICAL PRODUCTS (Idealo Style) ---
        def get_offers(group):
            offers = {}
            for _, r in group.sort_values(['current_price', 'timestamp'], ascending=[True, False]).iterrows():
                src = r['source']
                if src not in offers:
                    offers[src] = {
                        'source': src,
                        'price': r['current_price'],
                        'url': r['url'],
                        'stock_status': r['stock_status']
                    }
            return list(offers.values())
            
        df_fused = df.groupby('name', as_index=False).agg({
            'category': 'first',
            'current_price': 'min',
        })
        
        offers_dict = {name: get_offers(group) for name, group in df.groupby('name')}
        df_fused['offers'] = df_fused['name'].map(offers_dict)

        # --- SUB-CATEGORY NAVIGATION ---
        available_cats = sorted(df_fused['category'].unique())
        
        if len(available_cats) > 1:
            st.markdown("<h4 style='color: #cbd5e1; margin-bottom: 10px; font-weight: 500;'>Browse Catalog by Category:</h4>", unsafe_allow_html=True)
            
            # Using Streamlit's horizontal radio buttons for clean tab-like navigation
            selected_sub_cat = st.radio("Select a category", available_cats, horizontal=True, label_visibility="collapsed")
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            df_catalog = df_fused[df_fused['category'] == selected_sub_cat]
        else:
            df_catalog = df_fused

        # Render the filtered catalog
        for index, row in df_catalog.sort_values(by='current_price').head(30).iterrows():
            offers = row['offers']
            
            # Create the badges for sources
            sources_html = ""
            for off in offers:
                color = "#f97316" if off['source'] == "Jumia" else ("#eab308" if off['source'] == "MarjaneMall" else "#3b82f6")
                sources_html += f"<a href='{off['url']}' target='_blank' style='display:inline-block; margin-right:8px; margin-top:8px; background:rgba(255,255,255,0.05); border:1px solid {color}; padding:6px 12px; border-radius:6px; text-decoration:none; color:#f8fafc; font-size:0.8rem; font-weight:500; transition: all 0.2s;' onmouseover=\"this.style.background='{color}20'\" onmouseout=\"this.style.background='rgba(255,255,255,0.05)'\">{off['source']}: <strong style='color:{color};'>{off['price']:,.0f} DH</strong> ↗</a>"

            st.markdown(f"""
            <div class='report-card' style='padding: 20px; display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;'>
                <div style='flex: 1;'>
                    <h4 style='margin: 0; color: #f8fafc; font-size: 1.1rem; font-weight: 600;'>{row['name']}</h4>
                    <p style='margin: 5px 0 10px 0; color: #64748b; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;'>
                        <span style='color: #8b5cf6;'>{row['category']}</span> • {len(offers)} Offers available
                    </p>
                    <div>{sources_html}</div>
                </div>
                <div style='text-align: right; margin-left: 20px;'>
                    <div style='font-size:0.8rem; color:#94a3b8; text-transform:uppercase;'>Best Price</div>
                    <div class='product-price'>{row['current_price']:,.0f} DH</div>
                    {format_stock(offers[0]['stock_status'])}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("<p style='color:#94a3b8; font-size:1rem;'>Real-time AI surveillance logs & critical price drops.</p>", unsafe_allow_html=True)
        df_notifications = df.sort_values(by='timestamp', ascending=False)
        
        for i, row in df_notifications.head(8).iterrows():
            st.markdown(f"""
            <div class='report-card' style='border-left: 4px solid #38bdf8; padding: 15px 20px; margin-bottom: 12px;'>
                <div style='display:flex; justify-content:space-between;'>
                    <div><span style='color:#38bdf8; font-weight:700;'>[ALERT]</span> New Data Point: <strong>{row['name']}</strong></div>
                    <div style='color:#94a3b8; font-size:0.85rem;'>Just now</div>
                </div>
                <div style='color:#64748b; font-size:0.9rem; margin-top:5px;'>Logged via {row['source']} crawler at {row['current_price']:,.0f} DH.</div>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("<p style='color:#94a3b8; font-size:1rem;'>Paste a product URL to auto-extract, or fill the details manually if the site is protected.</p>", unsafe_allow_html=True)
        
        # Initialize session state
        if 'ext_name' not in st.session_state:
            st.session_state['ext_name'] = ""
        if 'ext_price' not in st.session_state:
            st.session_state['ext_price'] = 0.0
        if 'ext_source' not in st.session_state:
            st.session_state['ext_source'] = "Manual Entry"
            
        url_input = st.text_input("Product URL", placeholder="https://www.jumia.ma/...", key="url_input")
        
        if st.button("Auto-Extract Metadata"):
            if not url_input.startswith("http"):
                st.error("Please provide a valid URL starting with http/https.")
            else:
                with st.spinner("Bypassing security & extracting..."):
                    import requests
                    from bs4 import BeautifulSoup
                    import re
                    
                    name = ""
                    price = 0.0
                    source = "External Link"
                    if "jumia" in url_input.lower(): source = "Jumia"
                    elif "marjane" in url_input.lower(): source = "MarjaneMall"
                    
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                        }
                        response = requests.get(url_input, headers=headers, timeout=10)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract Name
                        h1 = soup.find('h1')
                        if h1: name = h1.text.strip()
                        elif soup.title: name = soup.title.text.replace('- Jumia Maroc', '').strip()
                        
                        if "Just a moment" in name or "Attention Required" in name:
                            st.warning("⚠️ Anti-bot protection (Cloudflare) blocked the AI. Please enter the details manually below.")
                            name = ""
                        else:
                            # Extract Price
                            price_text = ""
                            jumia_price = soup.find('span', class_='-b -ltr -tal -fs24')
                            if jumia_price: price_text = jumia_price.text
                            else:
                                for tag in soup.find_all(string=re.compile(r'Dhs|DH', re.IGNORECASE)):
                                    if tag.parent and len(tag.parent.text) < 20:
                                        price_text = tag.parent.text
                                        break
                            
                            if price_text:
                                num = re.sub(r'[^\d]', '', price_text.split(',')[0].split('.')[0])
                                if num: price = float(num)
                                
                    except Exception as e:
                        st.warning(f"Could not fully scrape page: {e}")
                    
                    # --- LOCAL AI CATEGORIZATION VIA OLLAMA (Qwen 3.5 4B) ---
                    predicted_cat = "Other"
                    debug_log = ""
                    if name and not ("Just a moment" in name or "Attention Required" in name):
                        try:
                            cat_options = ["Informatique", "Smartphones", "Électroménager", "TV & Audio", "Mode", "Gaming", "Beauté & Santé", "Maison & Bureau", "Sport", "Supermarché", "Automobile", "Other"]
                            prompt = f"Categorize this product: '{name}'. Choose EXACTLY ONE category from this list: {', '.join(cat_options)}. Output ONLY the exact category name, nothing else."
                            
                            debug_log += f"**Prompt Sent to Qwen 3.5 4B:**\n`{prompt}`\n\n"
                            
                            payload = {
                                "model": "qwen3.5:4b",
                                "prompt": prompt,
                                "stream": False,
                                "system": "You are a strict data classification AI. You must output exactly one category from the list provided. Do not write sentences. Do not try to search the web. Do not output URLs. Only output the category name.",
                                "options": {
                                    "temperature": 0.0,
                                    "top_p": 0.1
                                }
                            }
                            
                            res = None
                            try:
                                # Try Docker host network first
                                res = requests.post("http://host.docker.internal:11434/api/generate", json=payload, timeout=30)
                                debug_log += f"**Connection Status:** Successfully hit `host.docker.internal:11434`\n\n"
                            except Exception as e1:
                                debug_log += f"**host.docker.internal Error:** `{e1}`\n\n"
                                # Fallback to strict localhost
                                res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
                                debug_log += f"**Connection Status:** Successfully hit `localhost:11434`\n\n"
                            
                            if res and res.status_code == 200:
                                result = res.json().get("response", "").strip()
                                debug_log += f"**Raw Response from Qwen 3.5 4B:**\n`{result}`\n\n"
                                
                                for c in cat_options:
                                    if c.lower() in result.lower():
                                        predicted_cat = c
                                        debug_log += f"✅ **Matched Category:** `{predicted_cat}`\n"
                                        break
                                
                                if predicted_cat == "Other":
                                    debug_log += f"❌ **Failed Match:** The AI output did not perfectly match any allowed category string.\n"
                            else:
                                debug_log += f"**Ollama HTTP Status:** `{res.status_code if res else 'Unknown'}`\n"
                                if res: debug_log += f"**Response:** `{res.text}`\n"
                                st.warning(f"Ollama returned status code: {res.status_code if res else 'Unknown'}")
                        except Exception as e:
                            debug_log += f"**Fatal Exception:** `{e}`\n"
                            st.warning(f"⚠️ Ollama Connection Error: {e}. Is Qwen 3.5 4B running on your host machine?")
                    
                    st.session_state['ext_name'] = name
                    st.session_state['ext_price'] = price
                    st.session_state['ext_source'] = source
                    st.session_state['ext_category'] = predicted_cat
                    st.session_state['ext_debug'] = debug_log
                    st.rerun()

        st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
        
        if st.session_state.get('ext_debug'):
            with st.expander("🛠️ Ollama Qwen 3.5 4B Debug Log"):
                st.markdown(st.session_state['ext_debug'])
        
        with st.form("add_item_form"):
            st.markdown("<h3 style='margin-top: 0;'>Product Details</h3>", unsafe_allow_html=True)
            
            new_name = st.text_input("Product Name", value=st.session_state.get('ext_name', ''))
            
            c1, c2 = st.columns(2)
            with c1:
                cat_options = ["Informatique", "Smartphones", "Électroménager", "TV & Audio", "Mode", "Gaming", "Beauté & Santé", "Maison & Bureau", "Sport", "Supermarché", "Automobile", "Other"]
                
                # Fetch prediction from session state, fallback to Other
                predicted = st.session_state.get('ext_category', 'Other')
                default_idx = cat_options.index(predicted) if predicted in cat_options else len(cat_options)-1
                
                new_category = st.selectbox("Category (AI Predicted)", cat_options, index=default_idx)
                new_price = st.number_input("Price (DH)", min_value=0.0, format="%.2f", value=float(st.session_state.get('ext_price', 0.0)))
            with c2:
                sources = ["Manual Entry", "Jumia", "MarjaneMall", "External Link"]
                default_idx = sources.index(st.session_state.get('ext_source', "Manual Entry")) if st.session_state.get('ext_source', "Manual Entry") in sources else 0
                new_source = st.selectbox("Source", sources, index=default_idx)
                new_stock = st.selectbox("Stock Status", ["In Stock", "Out of Stock"])
            
            submitted = st.form_submit_button("Inject into Database")
            if submitted:
                if new_name.strip() == "":
                    st.error("Product Name is required.")
                else:
                    new_item = {
                        "name": new_name,
                        "category": new_category,
                        "current_price": new_price,
                        "original_price": new_price,
                        "discount": 0,
                        "stock_status": new_stock,
                        "url": url_input if url_input else "https://",
                        "source": new_source,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Update json file
                    raw_file = "ecommerce_sales.json"
                    data = []
                    if os.path.exists(raw_file):
                        with open(raw_file, 'r', encoding='utf-8') as f:
                            try:
                                data = json.load(f)
                            except:
                                data = []
                    
                    data.append(new_item)
                    
                    with open(raw_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    
                    st.cache_data.clear()
                    st.session_state['ext_name'] = ""
                    st.session_state['ext_price'] = 0.0
                    st.session_state['ext_source'] = "Manual Entry"
                    st.session_state['ext_category'] = "Other"
                    st.session_state['ext_debug'] = ""
                    st.success(f"Success! '{new_name}' was injected.")
                    st.rerun()

else:
    st.markdown("""
        <div style='text-align:center; padding: 50px; background: rgba(30,41,59,0.5); border-radius:16px; border:1px dashed #334155;'>
            <h2 style='color:#94a3b8;'>Awaiting Data Stream...</h2>
            <p style='color:#64748b;'>The AI Engine is currently waiting for the ETL pipeline to ingest data.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Initialize Scrapers"):
        st.info("System initializing...")
