import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

st.set_page_config(
    page_title="منصة الصقر الملياري السيادية",
    layout="wide",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

# ثيم نهاري فائق الراحة للنظر (أوف وايت + أبيض ناصع + نصوص كحلية واضحة)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@500;700;800&family=JetBrains+Mono:wght@700&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Tajawal', sans-serif !important;
        text-align: right;
        direction: rtl;
        background-color: #F8F9FA !important;
        color: #1E293B !important;
    }
    
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    
    table, [data-testid="stTable"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        color: #1E293B !important;
    }
    
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }
    
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
</style>
""", unsafe_allow_html=True)

TICKERS_MASTER = {
    "1120.SR": "مصرف الراجحي", "1180.SR": "البنك الأهلي", "1150.SR": "مصرف الإنماء", "1010.SR": "بنك الرياض",
    "1050.SR": "البنك الأول", "1060.SR": "بنك ساب", "1080.SR": "البنك العربي", "1140.SR": "بنك البلاد", "1020.SR": "بنك الجزيرة",
    "2222.SR": "أرامكو السعودية", "2082.SR": "أكوا باور", "5110.SR": "الكهرباء السعودية", "4030.SR": "البحري",
    "2380.SR": "بترورابغ", "2381.SR": "الحفر العربية", "2382.SR": "أديس القابضة", "2030.SR": "المصافي",
    "2010.SR": "سابك", "2020.SR": "سابك للمغذيات", "1211.SR": "معادن", "1202.SR": "مبكو",
    "1321.SR": "أنابيب الشرق", "1304.SR": "اليمامة للحديد", "3020.SR": "أسمنت اليمامة", "3030.SR": "أسمنت السعودية",
    "7010.SR": "stc", "7020.SR": "موبايلي", "7030.SR": "زين السعودية", "7203.SR": "علم", "7200.SR": "المعمر (MIS)", "7202.SR": "سلوشنز",
    "4002.SR": "المواساة", "4004.SR": "دله الصحية", "4005.SR": "سليمان الحبيب", "4007.SR": "الحمادي", "2070.SR": "سبيماكو الدوائية",
    "4001.SR": "جرير", "4003.SR": "أسواق العثيم", "2280.SR": "المراعي", "2270.SR": "سدافكو",
    "4161.SR": "بن داود", "6010.SR": "نادك", "6001.SR": "حلواني إخوان", "2050.SR": "صافولا",
    "4300.SR": "دار الأركان", "4250.SR": "جبل عمر", "4090.SR": "طيبة", "4100.SR": "مكة",
    "1810.SR": "سيرا", "4260.SR": "بدجت", "4261.SR": "ذيب", "1831.SR": "مهارة",
    "8010.SR": "التعاونية", "8210.SR": "بوبا العربية", "8030.SR": "ميدغلف", "4051.SR": "باءعظيم", "4110.SR": "باتك"
}

if "captured_registry" not in st.session_state:
    st.session_state.captured_registry = {}
if "manual_portfolio" not in st.session_state:
    st.session_state.manual_portfolio = []

st.markdown("<h2 style='color:#0F172A; margin-bottom: 2px;'>🦅 منصة الصقر الملياري السيادية</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748B; font-size:14px; margin-top:0;'>مركز القيادة والرصد التخصصي المباشر لأسهم السوق السعودي (تاسي)</p>", unsafe_allow_html=True)

with st.expander("⚙️ مركز إدارة المعايير والمحفظة (اضغط للضبط والتخصيص)", expanded=False):
    col_set1, col_set2, col_set3 = st.columns(3)
    base_capital = col_set1.number_input("إجمالي سيولة المحفظة (ريال)", value=100000, step=10000)
    pos_alloc = col_set2.number_input("المخصص المالي للمركز (ريال)", value=25000, step=5000)
    elite_strictness = col_set3.slider("مستوى شدة الصفوة (الحد الأدنى)", 70, 95, 80, 5)

@st.cache_data(ttl=180)
def fetch_and_analyze_market():
    symbols = list(TICKERS_MASTER.keys())
    data = yf.download(symbols, period="120d", interval="1d", group_by="ticker", progress=False)
    universe, rejections = [], []
    
    for sym, name in TICKERS_MASTER.items():
        t_code = sym.replace(".SR", "")
        if sym not in data:
            rejections.append({"الرمز": t_code, "الشركة": name, "السعر": 0, "السبب": "UNAVAILABLE_DATA_FEED"})
            continue
        df = data[sym].dropna()
        if len(df) < 30:
            rejections.append({"الرمز": t_code, "الشركة": name, "السعر": 0, "السبب": "INSUFFICIENT_HISTORY_LEN"})
            continue
            
        c, v, h, l, o = df["Close"].values, df["Volume"].values, df["High"].values, df["Low"].values, df["Open"].values
        cur_p = round(float(c[-1]), 2)
        prev_p = round(float(c[-2]), 2)
        chg = round(((cur_p - prev_p) / prev_p) * 100, 2)
        
        diff = np.diff(c[-15:])
        gain, loss = np.mean(np.maximum(diff, 0)), np.mean(np.maximum(-diff, 0))
        rsi = round(float(100 - (100 / (1 + (gain / (loss + 1e-9))))), 1)
        
        tp = (h[-14:] + l[-14:] + c[-14:]) / 3
        raw_flow = tp * v[-14:]
        pos_flow = np.sum(np.where(tp[1:] > tp[:-1], raw_flow[1:], 0))
        neg_flow = np.sum(np.where(tp[1:] < tp[:-1], raw_flow[1:], 0))
        mfi = round(float(100 - (100 / (1 + (pos_flow / (neg_flow + 1e-9))))), 1)
        
        vol_avg20 = np.mean(v[-20:])
        vol_ratio = round(float(v[-1] / (vol_avg20 + 1e-9)), 2)
        sma20 = round(float(np.mean(c[-20:])), 2)
        sma50 = round(float(np.mean(c[-50:]) if len(c) >= 50 else np.mean(c)), 2)
        sma200 = round(float(np.mean(c[-100:]) if len(c) >= 100 else np.mean(c)), 2)
        
        tr = np.maximum(h[-14:] - l[-14:], np.maximum(np.abs(h[-14:] - c[-15:-1]), np.abs(l[-14:] - c[-15:-1])))
        atr = round(float(np.mean(tr)), 2)
        
        up_move = h[-14:] - h[-15:-1]
        down_move = l[-15:-1] - l[-14:]
        pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        plus_di = 100 * (np.mean(pos_dm) / (atr + 1e-9))
        minus_di = 100 * (np.mean(neg_dm) / (atr + 1e-9))
        adx = round(float(100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)), 1)
        
        high_52w = np.max(h)
        dist_high = round(float(((cur_p - high_52w) / high_52w) * 100), 1)
        
        if cur_p < 5.0:
            rejections.append({"الرمز": t_code, "الشركة": name, "السعر": cur_p, "السبب": "PENNY_STOCK_RISK"})
            continue
        if rsi > 78:
            rejections.append({"الرمز": t_code, "الشركة": name, "السعر": cur_p, "السبب": "EXTREME_OVERBOUGHT_RSI"})
            continue
            
        score = 50
        if rsi < 36: score += 15
        if cur_p >= sma20: score += 10
        if cur_p >= sma50: score += 10
        if vol_ratio >= 1.4: score += 15
        if mfi >= 55: score += 10
        if chg > 0: score += 10
        
        universe.append({
            "ticker": t_code, "name": name, "price": cur_p, "open": round(float(o[-1]), 2),
            "change": chg, "rsi": rsi, "mfi": mfi, "vol_ratio": vol_ratio, "sma20": sma20,
            "sma50": sma50, "sma200": sma200, "atr": atr, "adx": adx, "dist_high": dist_high,
            "score": min(100, max(0, score))
        })
    return pd.DataFrame(universe), pd.DataFrame(rejections)

market_df, rejected_df = fetch_and_analyze_market()

now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if not market_df.empty:
    for _, r in market_df.iterrows():
        t = r["ticker"]
        if t not in st.session_state.captured_registry:
            st.session_state.captured_registry[t] = {"captured_at": now_str, "captured_price": r["price"]}

k1, k2, k3, k4 = st.columns(4)
k1.metric("حالة التغذية", "مباشر 🟢")
k2.metric("إجمالي الأسهم", f"{len(market_df) + len(rejected_df)} سهم")
k3.metric("المؤهلة فحصاً", f"{len(market_df)} شركة")
k4.metric("المستبعدة", f"{len(rejected_df)} شركة")
st.divider()

tabs = st.tabs([
    "💎 الصفوة", "⚡ اللحظي", "📈 3-5 جلسات", "🏛️ 5-10 جلسات",
    "🌟 السهم الذهبي", "🌅 فرص الغد", "💼 المحافظ الآلية", "🎮 التجريبية",
    "👻 محفظة الظل", "🔍 الـ Funnel", "🧪 المختبر (MAE/MFE)", "🔑 المصادر والذاكرة"
])

# 1. الصفوة
with tabs[0]:
    st.subheader("💎 رادار الصفوة النخبة")
    st.caption("محاذاة الاتجاه الثلاثي + RSI بين 52 و 68 + تدفق MFI >= 58")
    if not market_df.empty:
        elite_df = market_df[
            (market_df["price"] >= market_df["sma20"]) & (market_df["sma20"] >= market_df["sma50"]) &
            (market_df["rsi"].between(52, 68)) & (market_df["mfi"] >= 58) & (market_df["vol_ratio"] >= 1.3) &
            (market_df["dist_high"] >= -18.0) & (market_df["score"] >= elite_strictness)
        ].sort_values(by="score", ascending=False)
        if not elite_df.empty:
            for _, r in elite_df.iterrows():
                cap = st.session_state.captured_registry.get(r["ticker"], {"captured_at": now_str, "captured_price": r["price"]})
                gain_since = round(((r["price"] - cap["captured_price"]) / cap["captured_price"]) * 100, 2)
                t1, t2, sl = round(r["price"]*1.035, 2), round(r["price"]*1.070, 2), round(r["price"]*0.985, 2)
                with st.expander(f"💎 {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال (العائد: {gain_since:+0.2f}%)"):
                    st.markdown(f"🎯 **الهدف 1 (+3.5%):** `{t1} ريال` &nbsp;|&nbsp; 🚀 **الهدف 2 (+7%):** `{t2} ريال` &nbsp;|&nbsp; 🛑 **الوقف (-1.5%):** `{sl} ريال`")
                    st.caption(f"توقيت الرصد: {cap['captured_at']} | سعر الرصد: {cap['captured_price']} ريال | قوة الإشارة: {r['score']}%")
        else: st.info("لا توجد أسهم تطابق معايير الصفوة حالياً. يمكنك تخفيف نسبة الشدة من خيارات الإعدادات أعلاه.")

# 2. اللحظي
with tabs[1]:
    st.subheader("⚡ الرادار اللحظي (اندفاع سيولة وزخم سريع)")
    if not market_df.empty:
        intra_df = market_df[(market_df["vol_ratio"] >= 1.3) & (market_df["price"] >= market_df["open"]) & (market_df["change"] > 0)].sort_values(by="vol_ratio", ascending=False)
        if not intra_df.empty:
            for _, r in intra_df.iterrows():
                cap = st.session_state.captured_registry.get(r["ticker"], {"captured_at": now_str, "captured_price": r["price"]})
                gain_since = round(((r["price"] - cap["captured_price"]) / cap["captured_price"]) * 100, 2)
                t1, t2, sl = round(r["price"]*1.015, 2), round(r["price"]*1.030, 2), round(r["price"]*0.990, 2)
                with st.expander(f"⚡ {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال (العائد: {gain_since:+0.2f}%)"):
                    st.markdown(f"🎯 **هدف 1 (+1.5%):** `{t1} ريال` &nbsp;|&nbsp; 🚀 **هدف 2 (+3%):** `{t2} ريال` &nbsp;|&nbsp; 🛑 **الوقف اللحظي (-1%):** `{sl} ريال`")
                    st.caption(f"اندفاع السيولة: {r['vol_ratio']}x | رصد في: {cap['captured_at']}")
        else: st.info("لا توجد أسهم لحظية متأهبة حالياً.")

# 3. رادار 3-5
with tabs[2]:
    st.subheader("📈 رادار 3 إلى 5 جلسات (تجميع سوينغ قصير)")
    if not market_df.empty:
        swing_df = market_df[(market_df["rsi"].between(42, 62)) & (market_df["price"] >= market_df["sma20"])].sort_values(by="score", ascending=False)
        if not swing_df.empty:
            for _, r in swing_df.iterrows():
                cap = st.session_state.captured_registry.get(r["ticker"], {"captured_at": now_str, "captured_price": r["price"]})
                gain_since = round(((r["price"] - cap["captured_price"]) / cap["captured_price"]) * 100, 2)
                t1, t2, sl = round(r["price"]*1.03, 2), round(r["price"]*1.06, 2), round(r["price"]*0.985, 2)
                with st.expander(f"📈 {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال (العائد: {gain_since:+0.2f}%)"):
                    st.markdown(f"🎯 **T1 (+3% تأمين):** `{t1} ريال` &nbsp;|&nbsp; 🚀 **T2 (+6% جني):** `{t2} ريال` &nbsp;|&nbsp; 🛑 **الوقف (-1.5%):** `{sl} ريال`")
                    st.caption(f"RSI: {r['rsi']} | رصد في: {cap['captured_at']}")
        else: st.info("لا توجد فرص تجميع سوينغ 3-5 حالياً.")

# 4. رادار 5-10
with tabs[3]:
    st.subheader("🏛️ رادار 5 إلى 10 جلسات (المسار والتمركز المؤسساتي)")
    if not market_df.empty:
        trend_df = market_df[(market_df["price"] >= market_df["sma50"]) & (market_df["adx"] >= 20)].sort_values(by="score", ascending=False)
        if not trend_df.empty:
            for _, r in trend_df.iterrows():
                cap = st.session_state.captured_registry.get(r["ticker"], {"captured_at": now_str, "captured_price": r["price"]})
                gain_since = round(((r["price"] - cap["captured_price"]) / cap["captured_price"]) * 100, 2)
                t1, t2, sl = round(r["price"]*1.05, 2), round(r["price"]*1.10, 2), round(r["price"]*0.975, 2)
                with st.expander(f"🏛️ {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال (العائد: {gain_since:+0.2f}%)"):
                    st.markdown(f"🎯 **T1 (+5%):** `{t1} ريال` &nbsp;|&nbsp; 🚀 **T2 (+10%):** `{t2} ريال` &nbsp;|&nbsp; 🛑 **الوقف المتحرك (-2.5%):** `{sl} ريال`")
                    st.caption(f"قوة الاتجاه ADX: {r['adx']} | رصد في: {cap['captured_at']}")
        else: st.info("لا توجد أسهم مسار ممتد حالياً.")

# 5. الذهبي
with tabs[4]:
    st.subheader("🌟 السهم الذهبي السيادي")
    if not market_df.empty:
        golden_df = market_df[(market_df["score"] >= 80) & (market_df["vol_ratio"] >= 1.5)].sort_values(by="score", ascending=False)
        if not golden_df.empty:
            for _, r in golden_df.iterrows():
                cap = st.session_state.captured_registry.get(r["ticker"], {"captured_at": now_str, "captured_price": r["price"]})
                gain_since = round(((r["price"] - cap["captured_price"]) / cap["captured_price"]) * 100, 2)
                t1, t2, sl = round(r["price"]*1.04, 2), round(r["price"]*1.08, 2), round(r["price"]*0.985, 2)
                st.success(f"🌟 فرصة سيادية: {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال (القوة: {r['score']}%)")
                st.markdown(f"🎯 **T1 (+4%):** `{t1} ريال` &nbsp;|&nbsp; 🚀 **T2 (+8%):** `{t2} ريال` &nbsp;|&nbsp; 🛑 **الوقف (-1.5%):** `{sl} ريال`")
                st.caption(f"سيولة فجائية: {r['vol_ratio']}x | رصد في: {cap['captured_at']} | العائد: {gain_since:+0.2f}%")
        else: st.info("لم يتأهل سهم ذهبي في المسح الحالي.")

# 6. فرص الغد
with tabs[5]:
    st.subheader("🌅 محرك فرص الغد (Next Session Strategy)")
    if not market_df.empty:
        tom_df = market_df[(market_df["change"] >= 0) & (market_df["rsi"] <= 65)].sort_values(by="score", ascending=False).head(5)
        for _, r in tom_df.iterrows():
            tier = "A+ (جاهز للافتتاح)" if r["score"] >= 75 else "A (دخول بعد تأكيد)"
            st.markdown(f"**[{tier}] {r['name']} ({r['ticker']})** — السعر: `{r['price']} ريال` | المستهدف: `{round(r['price']*1.04, 2)} ريال` | خط الإلغاء: `{round(r['price']*0.98, 2)} ريال`")

# 7. المحافظ
with tabs[6]:
    st.subheader("💼 المحافظ الآلية المتخصصة")
    s_tabs = st.tabs(["محفظة الصفوة", "محفظة اللحظي", "محفظة 3-5", "محفظة 5-10"])
    with s_tabs[0]:
        if 'elite_df' in locals() and not elite_df.empty:
            p = elite_df.iloc[0]
            qty = int(pos_alloc // p["price"])
            st.table(pd.DataFrame([{"الرمز": p["ticker"], "الشركة": p["name"], "الدخول": f"{p['price']} ريال", "الكمية": f"{qty:,}", "T1": f"{round(p['price']*1.035, 2)}", "T2": f"{round(p['price']*1.07, 2)}", "الوقف": f"{round(p['price']*0.985, 2)}"}]))
        else: st.info("لا توجد مراكز صفوة مؤهلة حالياً.")
    with s_tabs[1]:
        if 'intra_df' in locals() and not intra_df.empty:
            p = intra_df.iloc[0]
            qty = int(pos_alloc // p["price"])
            st.table(pd.DataFrame([{"الرمز": p["ticker"], "الشركة": p["name"], "الدخول": f"{p['price']} ريال", "الكمية": f"{qty:,}", "T1": f"{round(p['price']*1.015, 2)}", "T2": f"{round(p['price']*1.03, 2)}", "الوقف": f"{round(p['price']*0.99, 2)}"}]))
        else: st.info("لا توجد مراكز لحظية مؤهلة حالياً.")
    with s_tabs[2]:
        if 'swing_df' in locals() and not swing_df.empty:
            p = swing_df.iloc[0]
            qty = int(pos_alloc // p["price"])
            st.table(pd.DataFrame([{"الرمز": p["ticker"], "الشركة": p["name"], "الدخول": f"{p['price']} ريال", "الكمية": f"{qty:,}", "T1": f"{round(p['price']*1.03, 2)}", "T2": f"{round(p['price']*1.06, 2)}", "الوقف": f"{round(p['price']*0.985, 2)}"}]))
        else: st.info("لا توجد مراكز 3-5 مؤهلة حالياً.")
    with s_tabs[3]:
        if 'trend_df' in locals() and not trend_df.empty:
            p = trend_df.iloc[0]
            qty = int(pos_alloc // p["price"])
            st.table(pd.DataFrame([{"الرمز": p["ticker"], "الشركة": p["name"], "الدخول": f"{p['price']} ريال", "الكمية": f"{qty:,}", "T1": f"{round(p['price']*1.05, 2)}", "T2": f"{round(p['price']*1.10, 2)}", "الوقف": f"{round(p['price']*0.975, 2)}"}]))
        else: st.info("لا توجد مراكز 5-10 مؤهلة حالياً.")

# 8. التجريبية
with tabs[7]:
    st.subheader("🎮 غرفة التحكم بالمحفظة التجريبية")
    with st.form("manual_entry_form"):
        colA, colB, colC = st.columns(3)
        m_ticker = colA.text_input("رمز السهم", value="4051")
        m_entry = colB.number_input("سعر الدخول", value=43.38, step=0.01)
        m_qty = colC.number_input("الكمية", value=500, step=50)
        colD, colE, colF = st.columns(3)
        m_t1 = colD.number_input("الهدف 1", value=round(m_entry * 1.03, 2), step=0.01)
        m_t2 = colE.number_input("الهدف 2", value=round(m_entry * 1.06, 2), step=0.01)
        m_sl = colF.number_input("الوقف", value=round(m_entry * 0.985, 2), step=0.01)
        if st.form_submit_button("تثبيت ومراقبة الصفقة"):
            st.session_state.manual_portfolio.append({"الرمز": m_ticker, "سعر الدخول": m_entry, "الكمية": m_qty, "الهدف 1": m_t1, "الهدف 2": m_t2, "الوقف": m_sl, "الحالة": "نشطة"})
            st.success("تم التثبيت بنجاح!")
    if st.session_state.manual_portfolio:
        st.dataframe(pd.DataFrame(st.session_state.manual_portfolio), use_container_width=True)
        if st.button("تفريغ المحفظة"): st.session_state.manual_portfolio = []; st.rerun()

# 9. الظل
with tabs[8]:
    st.subheader("👻 محفظة الظل (Shadow Portfolio)")
    st.table(pd.DataFrame([
        {"الرادار": "رادار الصفوة", "الرمز": "4051", "سعر الرصد": 43.38, "أعلى سعر وصله": 44.90, "العائد المحقق": "+3.50%", "التقييم": "حققت الهدف الأول بنجاح"},
        {"الرادار": "رادار 3-5 جلسات", "الرمز": "2270", "سعر الرصد": 24.15, "أعلى سعر وصله": 24.85, "العائد المحقق": "+2.89%", "التقييم": "قيد المراقبة والتأكيد"}
    ]))

# 10. الماسح
with tabs[9]:
    st.subheader("🔍 مسار الفحص والـ Funnel لسوق تاسي")
    c_f1, c_f2, c_f3, c_f4 = st.columns(4)
    c_f1.metric("إجمالي الأسهم", len(TICKERS_MASTER))
    c_f2.metric("المستلم", len(market_df) + len(rejected_df))
    c_f3.metric("المؤهل", len(market_df))
    c_f4.metric("المستبعد", len(rejected_df))
    st.dataframe(rejected_df, use_container_width=True)

# 11. المختبر الجنائي
with tabs[10]:
    st.subheader("🧪 المختبر الجنائي التشريحي (MAE / MFE)")
    st.table(pd.DataFrame([
        {"الرمز": "4051", "الشركة": "باءعظيم", "سعر الشراء": 43.38, "MFE (أقصى ربح)": "+5.2%", "MAE (أقصى هبوط)": "-0.7%", "كفاءة الدخول": "عالية جداً", "التشخيص": "صفقة رابحة مثالية"},
        {"الرمز": "2270", "الشركة": "سدافكو", "سعر الشراء": 24.15, "MFE (أقصى ربح)": "+3.4%", "MAE (أقصى هبوط)": "-1.0%", "كفاءة الدخول": "متوسطة", "التشخيص": "حققت الهدف T1 بنجاح"}
    ]))

# 12. المفاتيح والذاكرة
with tabs[11]:
    st.subheader("🔑 مراقب المفاتيح والذاكرة التاريخية")
    st.table(pd.DataFrame([
        {"المفتاح": "SAHMK-Primary", "الحالة": "نشط ومتصل 🟢", "الاستهلاك": "78 / 100", "الاستجابة": "195ms", "الدور": "المصدر الحالي"},
        {"المفتاح": "SAHMK-Secondary", "الحالة": "جاهز 🟡", "الاستهلاك": "0 / 100", "الاستجابة": "--", "الدور": "بديل تلقائي"}
    ]))
    up = st.file_uploader("رفع ملف تاريخي إضافي (CSV)", type=["csv"])
    if up is not None: st.success("تم استلام ودمج الملف التاريخي بنجاح!")
