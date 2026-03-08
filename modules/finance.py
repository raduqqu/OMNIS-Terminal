import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# Harta ETF-urilor pe sectoare pentru analiza de corelație macro
SECTOR_ETFS = {
    "Technology": ["XLK", "QQQ", "SOXX"],
    "Energy": ["XLE", "VDE", "XOP"],
    "Financial Services": ["XLF", "KRE", "VFH"],
    "Healthcare": ["XLV", "IBB", "VHT"],
    "Consumer Cyclical": ["XLY", "XRT", "VCR"],
    "Consumer Defensive": ["XLP", "VDC"],
    "Industrials": ["XLI", "VIS", "ITA"],
    "Basic Materials": ["XLB", "VAW"],
    "Real Estate": ["VNQ", "XLRE"],
    "Communication Services": ["XLC", "VOX"],
    "Utilities": ["XLU", "VPU"]
}

def get_global_peers(ticker):
    """Trage companiile similare la nivel global folosind API-ul intern de recomandări Yahoo."""
    try:
        url = f"https://query2.finance.yahoo.com/v6/finance/recommendationsbysymbol/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get('finance', {}).get('result', [])
            if results:
                symbols = results[0].get('recommendedSymbols', [])
                return [s['symbol'] for s in symbols][:10] 
    except Exception:
        pass
    return []

def render_finance_dashboard():
    # ==========================================
    # BARA DE COMANDĂ GLOBALĂ
    # ==========================================
    st.markdown("<h3 class='header-blue'>OMNIS COMMAND LINE</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        ticker = st.text_input("Enter Global Ticker (e.g. AAPL, EGY, TSLA):", value="EGY", label_visibility="collapsed").upper()
    with col2:
        run_btn = st.button("EXECUTE ANALYSIS", use_container_width=True, type="primary")

    if run_btn:
        with st.spinner(f"Aggregating global intelligence for {ticker}..."):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")
                info = stock.info
                
                if hist.empty:
                    st.warning("⚠️ Invalid Ticker or Rate Limit Exceeded. Încearcă alt simbol.")
                    return

                tab_deep, tab_financials, tab_macro = st.tabs([
                    "📊 Deep-Dive & Peers", 
                    "📑 Financial Statements",
                    "🔗 Macro & ETF Evolution"
                ])

                # ==========================================
                # TAB 1: DEEP-DIVE & PEERS
                # ==========================================
                with tab_deep:
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'],
                        increasing_line_color='#00FF00', decreasing_line_color='#FF4B4B', name="Price"
                    )])
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', line=dict(color='cyan', width=1), name='50D SMA'))
                    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=10, b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                    target_mc = info.get('marketCap', 0)
                    sector = info.get('sector', 'Unknown Sector')
                    
                    st.markdown(f"<h4 class='header-blue'>{info.get('shortName', ticker)} - Vitals</h4>", unsafe_allow_html=True)
                    v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                    
                    with v_col1:
                        if target_mc > 0: st.write(f"Cap: **${target_mc/1e9:.2f}B**" if target_mc >= 1e9 else f"Cap: **${target_mc/1e6:.2f}M**")
                        if info.get('trailingPE'): st.write(f"P/E: **{info['trailingPE']}**")
                    with v_col2:
                        if info.get('profitMargins'): st.write(f"Margin: **{info['profitMargins']*100:.2f}%**")
                        if info.get('returnOnEquity'): st.write(f"ROE: **{info['returnOnEquity']*100:.2f}%**")
                    with v_col3:
                        if info.get('beta'): st.write(f"Beta: **{info['beta']}**")
                        if info.get('dividendYield'): st.write(f"Div: **{info['dividendYield']*100:.2f}%**")
                    with v_col4:
                        st.write(f"Sector: **{sector}**")
                        if info.get('recommendationKey'): st.write(f"Analyst: **{str(info['recommendationKey']).upper()}**")

                    st.markdown("---")
                    st.markdown("<h4 class='header-blue'>Valuation-Adjusted Peers</h4>", unsafe_allow_html=True)
                    peers = get_global_peers(ticker)
                    if peers:
                        valid_peers = []
                        for p in peers:
                            try:
                                p_info = yf.Ticker(p).info
                                p_mc = p_info.get('marketCap', 0)
                                if target_mc == 0 or (p_mc > 0 and p_mc <= (target_mc * 1.25)):
                                    price = p_info.get('currentPrice') or p_info.get('previousClose') or 0
                                    valid_peers.append({
                                        "Ticker": p,
                                        "Company": p_info.get('shortName', p)[:20],
                                        "Price": f"${price}",
                                        "Market Cap": f"${p_mc/1e9:.2f}B" if p_mc >= 1e9 else f"${p_mc/1e6:.2f}M",
                                        "P/E": round(p_info.get('trailingPE', 0), 2) if p_info.get('trailingPE') else "-",
                                        "_mc_raw": p_mc
                                    })
                            except: pass
                        if valid_peers:
                            valid_peers = sorted(valid_peers, key=lambda x: x['_mc_raw'], reverse=True)
                            for peer in valid_peers: del peer['_mc_raw']
                            st.dataframe(pd.DataFrame(valid_peers), use_container_width=True, hide_index=True)
                        else:
                            st.info("No smaller or equivalent peers found in database.")

                # ==========================================
                # TAB 2: FINANCIAL STATEMENTS
                # ==========================================
                with tab_financials:
                    st.markdown(f"<h4 class='header-blue'>Accounting Ledgers for {ticker}</h4>", unsafe_allow_html=True)
                    f_tab1, f_tab2, f_tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
                    
                    with f_tab1:
                        if not stock.financials.empty: st.dataframe(stock.financials, use_container_width=True)
                        else: st.info("No Income Statement data available.")
                    with f_tab2:
                        if not stock.balance_sheet.empty: st.dataframe(stock.balance_sheet, use_container_width=True)
                        else: st.info("No Balance Sheet data available.")
                    with f_tab3:
                        if not stock.cashflow.empty: st.dataframe(stock.cashflow, use_container_width=True)
                        else: st.info("No Cash Flow data available.")

                # ==========================================
                # TAB 3: MACRO & ETF EVOLUTION
                # ==========================================
                with tab_macro:
                    st.markdown(f"<h4 class='header-blue'>Global Market Pulse & Risk</h4>", unsafe_allow_html=True)
                    
                    try:
                        # Tragem indecșii principali + datele macro
                        macro_tickers = ["^GSPC", "^IXIC", "^DJI", "^VIX", "CL=F", "^TNX"]
                        macro_data = yf.download(macro_tickers, period="5d", progress=False)['Close']
                        
                        def get_pct(t):
                            return ((macro_data[t].iloc[-1] - macro_data[t].iloc[-2]) / macro_data[t].iloc[-2]) * 100
                        
                        # Randul 1: Market Indices
                        r1c1, r1c2, r1c3 = st.columns(3)
                        r1c1.metric("S&P 500", f"{macro_data['^GSPC'].iloc[-1]:,.2f}", f"{get_pct('^GSPC'):.2f}%")
                        r1c2.metric("NASDAQ", f"{macro_data['^IXIC'].iloc[-1]:,.2f}", f"{get_pct('^IXIC'):.2f}%")
                        r1c3.metric("DOW JONES", f"{macro_data['^DJI'].iloc[-1]:,.2f}", f"{get_pct('^DJI'):.2f}%")
                        
                        st.write("") # Spațiere
                        
                        # Randul 2: Macro Risk
                        vix_val = macro_data['^VIX'].iloc[-1]
                        oil_pct = get_pct('CL=F')
                        tnx_pct = get_pct('^TNX')
                        
                        r2c1, r2c2, r2c3 = st.columns(3)
                        r2c1.metric("VIX (Fear Index)", f"{vix_val:.2f}", f"{get_pct('^VIX'):.2f}%", delta_color="inverse")
                        r2c2.metric("Crude Oil (WTI)", f"${macro_data['CL=F'].iloc[-1]:.2f}", f"{oil_pct:.2f}%")
                        r2c3.metric("10-Yr Yield", f"{macro_data['^TNX'].iloc[-1]:.2f}%", f"{tnx_pct:.2f}%", delta_color="inverse")
                        
                        st.markdown("---")
                        
                        # AI Corelation Logic
                        if vix_val > 25: st.error("🚨 MARKET ALERT: VIX is extremely high. Broad market risk is elevated.")
                        if sector == "Energy":
                            if oil_pct > 1.0: st.success(f"🟢 TAILWIND: Crude Oil is UP. Positive catalyst for {ticker} revenues.")
                            elif oil_pct < -1.0: st.error(f"🔴 HEADWIND: Crude Oil is DOWN. Margins for {ticker} may contract.")
                        elif sector in ["Technology", "Communication Services"]:
                            if tnx_pct > 1.5: st.error(f"🔴 HEADWIND: 10-Year Yields are spiking. Historically bad for high-growth tech like {ticker}.")
                            elif tnx_pct < -1.5: st.success(f"🟢 TAILWIND: Yields are dropping. Bullish catalyst for {ticker} valuation multipliers.")
                        elif sector in ["Financial Services"]:
                            if tnx_pct > 1.0: st.success(f"🟢 TAILWIND: Yields are rising. Usually expands net interest margins for financial firms like {ticker}.")
                        elif sector in ["Industrials", "Consumer Cyclical"]:
                            if oil_pct > 1.5: st.warning(f"⚠️ MARGIN RISK: Oil prices are up, increasing supply chain & transport costs for {ticker}.")

                    except Exception as e:
                        st.warning(f"Standby: Could not load real-time macro indices. {e}")

                    # ==========================================
                    # ETF SECTOR EVOLUTION
                    # ==========================================
                    st.markdown("---")
                    st.markdown(f"<h4 class='header-blue'>Sector Evolution: {sector}</h4>", unsafe_allow_html=True)
                    
                    target_etfs = SECTOR_ETFS.get(sector, ["SPY", "QQQ", "DIA"])
                    
                    with st.spinner(f"Pulling institutional performance for {', '.join(target_etfs)}..."):
                        try:
                            etf_data = yf.download(target_etfs, period="1y", progress=False)['Close']
                            etf_results = []
                            etf_descriptions = {}
                            
                            for etf in target_etfs:
                                if etf in etf_data.columns:
                                    col_data = etf_data[etf].dropna()
                                    L = len(col_data)
                                    if L > 1:
                                        curr = col_data.iloc[-1]
                                        
                                        def get_ret(days_back):
                                            if L > days_back:
                                                return ((curr - col_data.iloc[-(days_back+1)]) / col_data.iloc[-(days_back+1)]) * 100
                                            else:
                                                return ((curr - col_data.iloc[0]) / col_data.iloc[0]) * 100
                                                
                                        d1 = get_ret(1)
                                        w1 = get_ret(5)
                                        m1 = get_ret(21)
                                        m3 = get_ret(63)
                                        m6 = get_ret(126)
                                        m12 = get_ret(252) if L >= 250 else ((curr - col_data.iloc[0]) / col_data.iloc[0]) * 100
                                        
                                        etf_info = yf.Ticker(etf).info
                                        etf_name = etf_info.get('shortName', etf)[:25]
                                        etf_descriptions[etf] = etf_info.get('longBusinessSummary', 'No description available for this ETF.')
                                        
                                        etf_results.append({
                                            "ETF / Index": f"{etf} ({etf_name})",
                                            "Price": f"${curr:.2f}",
                                            "1-Day": round(d1, 2),
                                            "1-Week": round(w1, 2),
                                            "1-Month": round(m1, 2),
                                            "3-Months": round(m3, 2),
                                            "6-Months": round(m6, 2),
                                            "1-Year": round(m12, 2)
                                        })
                            
                            if etf_results:
                                df_etfs = pd.DataFrame(etf_results)
                                st.dataframe(df_etfs.style.map(
                                    lambda x: 'color: #00FF00' if isinstance(x, (int, float)) and x > 0 else ('color: #FF4B4B' if isinstance(x, (int, float)) and x < 0 else ''),
                                    subset=['1-Day', '1-Week', '1-Month', '3-Months', '6-Months', '1-Year']
                                ), use_container_width=True, hide_index=True)
                                
                                st.markdown("##### 📖 Fund Holdings & Strategy")
                                for etf, desc in etf_descriptions.items():
                                    with st.expander(f"What is inside {etf}?"):
                                        st.caption(desc)
                            else:
                                st.info("ETF tracking data currently unavailable.")
                                
                        except Exception as e:
                            st.warning(f"Could not load Sector ETF performance: {e}")

            except Exception as e:
                st.error(f"System Failure: {e}")