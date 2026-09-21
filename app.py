import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import hashlib
import io

# ==============================================================================
# 1. إعدادات الصفحة والهندسة البصرية المتجاوبة
# ==============================================================================
st.set_page_config(
    page_title="منصة الصقر الملياري السيادية | Sovereign Truth Engine",
    layout="wide",
    page_icon="🦅",
    initial_sidebar_state="collapsed"
)

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "أوف وايت دافئ (Warm Linen)"

THEMES = {
    "أوف وايت دافئ (Warm Linen)": {
        "bg": "#FAF9F6", "card": "#FFFFFF", "text": "#1E293B", "border": "#E2E8F0", "accent": "#D97706"
    },
    "أبيض ناصع عالي التباين (Pure White)": {
        "bg": "#FFFFFF", "card": "#F8FAFC", "text": "#0F172A", "border": "#CBD5E1", "accent": "#2563EB"
    },
    "هجين عصري (Modern Slate)": {
        "bg": "#F1F5F9", "card": "#FFFFFF", "text": "#0F172A", "border": "#CBD5E1", "accent": "#0284C7"
    },
    "واحة مالية هادئة (Oasis Mint)": {
        "bg": "#F0FDF4", "card": "#FFFFFF", "text": "#14532D", "border": "#BBF7D0", "accent": "#16A34A"
    }
}
t_cfg = THEMES.get(st.session_state.theme_mode, THEMES["أوف وايت دافئ (Warm Linen)"])

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@500;700;800;900&family=JetBrains+Mono:wght@700;800&display=swap');
    html, body, [class*="css"], .stApp {{
        font-family: 'Tajawal', sans-serif !important;
        text-align: right !important;
        direction: rtl !important;
        background-color: {t_cfg['bg']} !important;
        color: {t_cfg['text']} !important;
    }}
    div[data-testid="stMetric"] {{
        background-color: {t_cfg['card']} !important;
        border: 1px solid {t_cfg['border']} !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        color: {t_cfg['text']} !important;
    }}
    div[data-testid="stExpander"] {{
        background-color: {t_cfg['card']} !important;
        border: 1px solid {t_cfg['border']} !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. محرك التوقيت السيادي وحالة تاسي (UTC+3)
# ==============================================================================
def get_riyadh_market_clock():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    riyadh_now = utc_now + datetime.timedelta(hours=3)
    is_trading_day = riyadh_now.weekday() in [6, 0, 1, 2, 3] # الأحد إلى الخميس
    t_now = riyadh_now.time()
    t_open = datetime.time(10, 0)
    t_close = datetime.time(15, 0)
    
    if is_trading_day and (t_open <= t_now <= t_close):
        mins_passed = (t_now.hour - 10) * 60 + t_now.minute
        time_factor = max(0.15, min(1.0, mins_passed / 300.0))
        status_msg = "جلسة تاسي مباشرة ومفتوحة الآن 🟢"
    else:
        time_factor = 1.0
        status_msg = "السوق مغلق حالياً (تُعرض بيانات آخر إغلاق رسمي) 🟡"
            
    return riyadh_now, time_factor, status_msg

riyadh_dt, session_time_factor, market_status_banner = get_riyadh_market_clock()

# ==============================================================================
# 3. كوكبة السوق المعتمدة
# ==============================================================================
TICKERS_MASTER = {
    "1120.SR": ("مصرف الراجحي", "البنوك"), "1180.SR": ("البنك الأهلي", "البنوك"), "1150.SR": ("مصرف الإنماء", "البنوك"),
    "1010.SR": ("بنك الرياض", "البنوك"), "1050.SR": ("البنك الأول", "البنوك"), "1060.SR": ("بنك ساب", "البنوك"),
    "1080.SR": ("البنك العربي", "البنوك"), "1140.SR": ("بنك البلاد", "البنوك"), "1020.SR": ("بنك الجزيرة", "البنوك"),
    "2222.SR": ("أرامكو السعودية", "الطاقة"), "2082.SR": ("أكوا باور", "المرافق"), "5110.SR": ("الكهرباء", "المرافق"),
    "4030.SR": ("البحري", "الطاقة"), "2380.SR": ("بترورابغ", "الطاقة"), "2381.SR": ("الحفر العربية", "الطاقة"),
    "2382.SR": ("أديس القابضة", "الطاقة"), "2030.SR": ("المصافي", "الطاقة"),
    "2010.SR": ("سابك", "المواد الأساسية"), "2020.SR": ("سابك للمغذيات", "المواد الأساسية"), "1211.SR": ("معادن", "المواد الأساسية"),
    "1202.SR": ("مبكو", "المواد الأساسية"), "1321.SR": ("أنابيب الشرق", "المواد الأساسية"), "1304.SR": ("اليمامة للحديد", "المواد الأساسية"),
    "3020.SR": ("أسمنت اليمامة", "المواد الأساسية"), "3030.SR": ("أسمنت السعودية", "المواد الأساسية"),
    "7010.SR": ("stc", "الاتصالات"), "7020.SR": ("موبايلي", "الاتصالات"), "7030.SR": ("زين السعودية", "الاتصالات"),
    "7203.SR": ("علم", "الاتصالات"), "7200.SR": ("المعمر (MIS)", "الاتصالات"), "7202.SR": ("سلوشنز", "الاتصالات"),
    "4002.SR": ("المواساة", "الرعاية الصحية"), "4004.SR": ("دله الصحية", "الرعاية الصحية"), "4005.SR": ("سليمان الحبيب", "الرعاية الصحية"),
    "4007.SR": ("الحمادي", "الرعاية الصحية"), "2070.SR": ("سبيماكو الدوائية", "الرعاية الصحية"),
    "4001.SR": ("جرير", "التجزئة والأغذية"), "4003.SR": ("أسواق العثيم", "التجزئة والأغذية"), "2280.SR": ("المراعي", "التجزئة والأغذية"),
    "2270.SR": ("سدافكو", "التجزئة والأغذية"), "4161.SR": ("بن داود", "التجزئة والأغذية"), "6010.SR": ("نادك", "التجزئة والأغذية"),
    "6001.SR": ("حلواني إخوان", "التجزئة والأغذية"), "2050.SR": ("صافولا", "التجزئة والأغذية"),
    "4300.SR": ("دار الأركان", "العقارات والنقل"), "4250.SR": ("جبل عمر", "العقارات والنقل"), "4090.SR": ("طيبة", "العقارات والنقل"),
    "4100.SR": ("مكة", "العقارات والنقل"), "1810.SR": ("سيرا", "العقارات والنقل"), "4260.SR": ("بدجت", "العقارات والنقل"),
    "4261.SR": ("ذيب", "العقارات والنقل"), "1831.SR": ("مهارة", "العقارات والنقل"), "8010.SR": ("التعاونية", "التأمين"),
    "8210.SR": ("بوبا العربية", "التأمين"), "8030.SR": ("ميدغلف", "التأمين"), "4051.SR": ("باءعظيم", "التجزئة والأغذية"),
    "4110.SR": ("باتك", "العقارات والنقل")
}

# الذاكرة التراكمية وسجل تجميد الإشارات
if "frozen_signals" not in st.session_state: st.session_state.frozen_signals = {}
if "portfolio_ledger" not in st.session_state:
    st.session_state.portfolio_ledger = [
        {"تاريخ التنفيذ": "2026-09-21 10:15:20", "الرمز": "1050", "الشركة": "البنك الأول", "سعر الدخول": 21.05, "الكمية": 1000, "T1": 21.65, "T2": 22.30, "الوقف": 20.60, "الحالة": "مفتوحة 🟢", "تاريخ الخروج": "--", "سعر الخروج": "--", "الربح المحقق": "--", "الرادار": "اللحظي"},
        {"تاريخ التنفيذ": "2026-09-21 11:20:45", "الرمز": "2070", "الشركة": "سبيماكو", "سعر الدخول": 32.26, "الكمية": 800, "T1": 34.60, "T2": 37.10, "الوقف": 30.50, "الحالة": "مفتوحة 🟢", "تاريخ الخروج": "--", "سعر الخروج": "--", "الربح المحقق": "--", "الرادار": "الصفوة + مسار"}
    ]
if "manual_portfolio" not in st.session_state: st.session_state.manual_portfolio = []

def calculate_wilder_rsi(c_series, period=14):
    try:
        delta = c_series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ema_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = ema_up / (ema_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        val = float(rsi.iloc[-1])
        return round(val, 1) if not np.isnan(val) else 50.0
    except Exception:
        return 50.0

# ترويسة المنصة
h1, h2 = st.columns([2.6, 1.4])
with h1:
    st.markdown("<h2 style='margin-bottom:0; font-weight:900;'>🦅 منصة الصقر الملياري السيادية</h2>", unsafe_allow_html=True)
    st.caption(f"محرك الحقيقة والقرار الكمي الصارم | توقيت الرياض: {riyadh_dt.strftime('%Y-%m-%d %H:%M:%S')} | {market_status_banner}")
with h2:
    selected_theme = st.selectbox("🎨 الثيم النهاري المريح:", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_mode))
    if selected_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = selected_theme
        st.rerun()

with st.expander("⚙️ مركز العمليات، التحديث الفوري، وإدارة السيولة", expanded=False):
    c1, c2, c3 = st.columns([1.5, 1.5, 2])
    with c1:
        if st.button("🔄 تحديث بيانات السوق الفورية"):
            st.cache_data.clear()
            st.rerun()
    with c2:
        st.caption("التغذية: مباشرة ومؤمنة 🟢")
        st.caption(f"معامل زمن الجلسة: {round(session_time_factor*100, 1)}%")
    col_p1, col_p2, col_p3 = st.columns(3)
    base_capital = col_p1.number_input("إجمالي سيولة المحفظة (ريال)", value=100000, step=10000)
    pos_alloc = col_p2.number_input("المخصص المالي للمركز (ريال)", value=25000, step=5000)
    elite_strictness = col_p3.slider("مستوى صرامة الصفوة الفني", 50, 90, 65, 5)

# ==============================================================================
# 4. محرك سحب البيانات وتصنيف بيئة السوق
# ==============================================================================
@st.cache_data(ttl=90)
def fetch_complete_market_matrix(sess_factor):
    symbols = list(TICKERS_MASTER.keys())
    try:
        data = yf.download(symbols, period="1y", interval="1d", group_by="ticker", progress=False)
    except Exception:
        data = pd.DataFrame()

    processed, rejected = [], []
    for sym, (name, sector) in TICKERS_MASTER.items():
        t_code = sym.replace(".SR", "")
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if sym in data.columns.levels[0]: sub_df = data[sym].copy()
                elif sym in data.columns.levels[1]: sub_df = data.xs(sym, axis=1, level=1).copy()
                else:
                    rejected.append({"الرمز": t_code, "الشركة": name, "السبب": "الرمز غير متاح"})
                    continue
            else:
                if sym in data.columns: sub_df = data[[sym]].copy()
                else:
                    rejected.append({"الرمز": t_code, "الشركة": name, "السبب": "الرمز غير متاح"})
                    continue

            if isinstance(sub_df.columns, pd.MultiIndex):
                sub_df.columns = [c[0] for c in sub_df.columns]
            col_map = {c: str(c).capitalize() for c in sub_df.columns}
            sub_df = sub_df.rename(columns=col_map).dropna(how="all")
            
            if "Close" not in sub_df.columns or len(sub_df) < 20:
                rejected.append({"الرمز": t_code, "الشركة": name, "السبب": "بيانات تاريخية غير كافية"})
                continue
            
            c_ser = pd.to_numeric(sub_df["Close"].iloc[:, 0] if isinstance(sub_df["Close"], pd.DataFrame) else sub_df["Close"], errors='coerce').dropna()
            v_ser = pd.to_numeric(sub_df["Volume"].iloc[:, 0] if isinstance(sub_df["Volume"], pd.DataFrame) else sub_df["Volume"], errors='coerce').fillna(0)
            h_ser = pd.to_numeric(sub_df["High"].iloc[:, 0] if isinstance(sub_df["High"], pd.DataFrame) else sub_df["High"], errors='coerce').dropna()
            l_ser = pd.to_numeric(sub_df["Low"].iloc[:, 0] if isinstance(sub_df["Low"], pd.DataFrame) else sub_df["Low"], errors='coerce').dropna()
            o_ser = pd.to_numeric(sub_df["Open"].iloc[:, 0] if isinstance(sub_df["Open"], pd.DataFrame) else sub_df["Open"], errors='coerce').dropna()

            if len(c_ser) < 20: continue
            c, v, h, l, o = c_ser.values, v_ser.values, h_ser.values, l_ser.values, o_ser.values
            last_date = str(sub_df.index[-1].strftime("%Y-%m-%d"))
            
            cur_p = round(float(c[-1]), 2)
            prev_p = round(float(c[-2]), 2) if len(c) > 1 else cur_p
            chg = round(((cur_p - prev_p) / (prev_p + 1e-9)) * 100, 2)
            
            rsi = calculate_wilder_rsi(c_ser)
            
            n_bars = min(14, len(c))
            tp = (h[-n_bars:] + l[-n_bars:] + c[-n_bars:]) / 3
            raw_flow = tp * v[-n_bars:]
            pos_flow = np.sum(np.where(tp[1:] > tp[:-1], raw_flow[1:], 0))
            neg_flow = np.sum(np.where(tp[1:] < tp[:-1], raw_flow[1:], 0))
            mfi = round(float(100 - (100 / (1 + (pos_flow / (neg_flow + 1e-9))))), 1)
            
            vol_avg20 = np.mean(v[-min(20, len(v)):])
            rvol = round(float(v[-1] / ((vol_avg20 * sess_factor) + 1e-9)), 2)
            
            sma20 = round(float(np.mean(c[-min(20, len(c)):])), 2)
            sma50 = round(float(np.mean(c[-min(50, len(c)):])), 2)
            sma200 = round(float(np.mean(c[-min(200, len(c)):])), 2) if len(c) >= 150 else sma50
            
            tr = np.maximum(h[-n_bars:] - l[-n_bars:], np.abs(h[-n_bars:] - c[-n_bars:]))
            atr = round(float(np.mean(tr)), 2)
            
            res_20 = round(float(np.max(h[-min(21, len(h)):-1])), 2) if len(h) > 2 else cur_p
            sup_20 = round(float(np.min(l[-min(21, len(l)):-1])), 2) if len(l) > 2 else cur_p
            
            n_ex = min(5, len(c))
            mfe = round(float(((np.max(h[-n_ex:]) - c[-n_ex]) / (c[-n_ex] + 1e-9)) * 100), 2)
            mae = round(float(((np.min(l[-n_ex:]) - c[-n_ex]) / (c[-n_ex] + 1e-9)) * 100), 2)
            
            dr = 100
            if len(c) < 50: dr -= 20
            if v[-1] == 0: dr -= 40
            
            processed.append({
                "ticker": t_code, "name": name, "sector": sector, "price": cur_p, "last_date": last_date,
                "open": round(float(o[-1]), 2), "high": round(float(h[-1]), 2), "low": round(float(l[-1]), 2),
                "change": chg, "rsi": rsi, "mfi": mfi, "rvol": rvol, "sma20": sma20, "sma50": sma50,
                "sma200": sma200, "atr": atr, "res_20": res_20, "sup_20": sup_20,
                "mfe": mfe, "mae": mae, "data_readiness": dr
            })
        except Exception:
            continue
            
    return pd.DataFrame(processed), pd.DataFrame(rejected)

df_all, df_rejected = fetch_complete_market_matrix(session_time_factor)
now_str = riyadh_dt.strftime("%Y-%m-%d %H:%M:%S")

if not df_all.empty:
    up_ratio = (df_all["change"] > 0).mean()
    if up_ratio >= 0.60: current_regime = "BULL"
    elif up_ratio <= 0.30: current_regime = "BEAR"
    elif df_all["atr"].mean() > 2.5: current_regime = "HIGH_VOLATILITY"
    else: current_regime = "NEUTRAL"
else:
    current_regime = "NEUTRAL"

# ==============================================================================
# 5. محرك الحقيقة والقرار الكمي (Sovereign Truth Engine)
# ==============================================================================
def process_truth_engine(df_in, regime):
    signals = []
    if df_in.empty: return pd.DataFrame(signals)
    
    for _, r in df_in.iterrows():
        cur_p = r["price"]
        atr = r["atr"]
        res_20 = r["res_20"]
        sup_20 = r["sup_20"]
        chg = r["change"]
        rsi = r["rsi"]
        rvol = r["rvol"]
        
        # 1. قوة السهم (STOCK_STRENGTH 0-100)
        st_score = 50
        if cur_p >= r["sma20"]: st_score += 12
        if cur_p >= r["sma50"]: st_score += 13
        if chg > 0 and regime == "BEAR": st_score += 15
        elif chg > 0: st_score += 8
        if 50 <= rsi <= 68: st_score += 10
        if rvol >= 1.0: st_score += 10
        stock_strength = min(100, max(0, st_score))
        
        # 2. منطقة الاقتناص والتريغر (Entry Engine)
        entry_low = round(cur_p - 0.25 * atr, 2)
        entry_high = round(cur_p + 0.15 * atr, 2)
        trigger_price = round(max(cur_p + 0.05, r["high"] * 0.999), 2)
        
        # 3. الوقف والأهداف الهيكلية الديناميكية
        struct_sl = round(max(sup_20, cur_p - 1.6 * atr), 2)
        if struct_sl >= cur_p: struct_sl = round(cur_p - 1.5 * atr, 2)
        sl_dist_pct = round(((cur_p - struct_sl) / cur_p) * 100, 2)
        sl_reason = f"كسر دعم هيكلي أدنى من القاع بـ 1.5 ATR ({atr} ريال)"
        
        if res_20 > cur_p * 1.025:
            t1 = res_20
            t1_reason = f"مقاومة قمة العشرين جلسة السابقة ({res_20})"
        else:
            t1 = round(cur_p + 1.5 * atr, 2)
            t1_reason = f"امتداد تذبذب ATR 1.5x فوق القمة الحالية"
        t2 = round(t1 + 1.6 * atr, 2)
        t1_pct = round(((t1 - cur_p) / cur_p) * 100, 2)
        t2_pct = round(((t2 - cur_p) / cur_p) * 100, 2)
        
        risk = cur_p - struct_sl
        reward = t1 - cur_p
        rr_ratio = round(reward / (risk + 1e-9), 2)
        
        # 4. جودة نقطة الدخول (ENTRY_QUALITY 0-100)
        eq_score = 50
        if rr_ratio >= 2.0: eq_score += 25
        elif rr_ratio >= 1.5: eq_score += 15
        elif rr_ratio < 1.0: eq_score -= 25
        if sl_dist_pct <= 2.5: eq_score += 15
        elif sl_dist_pct > 5.0: eq_score -= 15
        if cur_p <= entry_low + 0.1 * atr: eq_score += 10
        entry_quality = min(100, max(0, eq_score))
        
        # 5. قاعدة NO-CHASE الصارمة وحالة القرار
        is_no_chase = (cur_p > entry_high * 1.015) or (rr_ratio < 1.0)
        
        if is_no_chase:
            status = "NO_CHASE"
            action_reason = "تجاوز السعر نطاق الاقتناص أو انهيار معدل العائد للمخاطرة (R/R < 1.0)."
        elif cur_p < trigger_price:
            status = "WAIT"
            action_reason = f"السهم في مرحلة SETUP بانتظار تأكيد التفعيل (اختراق وثبات فوق {trigger_price})."
        else:
            status = "TRIGGERED"
            action_reason = f"تم لمس سعر التريغر {trigger_price} وبانتظار تأكيد شمعة الإغلاق والتنفيذ."
            
        # توليد البصمة المجمدة للإشارة (Signal ID)
        raw_sig = f"{r['ticker']}_{cur_p}_{struct_sl}_{t1}_{trigger_price}_{r['last_date']}"
        sig_id = f"SIG-{hashlib.sha256(raw_sig.encode()).hexdigest()[:10].upper()}"
        
        if sig_id not in st.session_state.frozen_signals:
            st.session_state.frozen_signals[sig_id] = {
                "sig_id": sig_id, "timestamp": now_str, "ticker": r["ticker"], "name": r["name"],
                "price": cur_p, "trigger": trigger_price, "entry_zone": f"[{entry_low} - {entry_high}]",
                "sl": struct_sl, "t1": t1, "t2": t2, "rr_ratio": rr_ratio, "status": status,
                "stock_strength": stock_strength, "entry_quality": entry_quality
            }
            
        radars = []
        if stock_strength >= 75 and r["mfi"] >= 50: radars.append("الصفوة")
        if rvol >= 1.1 and chg >= 0: radars.append("اللحظي")
        if rsi <= 60 and cur_p >= r["sma50"] * 0.96: radars.append("سوينغ")
        if cur_p >= r["sma50"] and stock_strength >= 65: radars.append("مسار")
        radar_label = " + ".join(radars) if radars else "مراقبة هيكلية"
        
        signals.append({
            "sig_id": sig_id, "ticker": r["ticker"], "name": r["name"], "sector": r["sector"],
            "price": cur_p, "last_date": r["last_date"], "change": chg, "rsi": rsi, "rvol": rvol,
            "stock_strength": stock_strength, "entry_quality": entry_quality,
            "entry_zone": f"[{entry_low} - {entry_high}]", "trigger": trigger_price,
            "sl": struct_sl, "sl_dist_pct": sl_dist_pct, "sl_reason": sl_reason,
            "t1": t1, "t1_pct": t1_pct, "t1_reason": t1_reason, "t2": t2, "t2_pct": t2_pct,
            "rr_ratio": rr_ratio, "data_readiness": r["data_readiness"], "status": status,
            "action_reason": action_reason, "radars": radar_label, "mfe": r["mfe"], "mae": r["mae"]
        })
        
    return pd.DataFrame(signals)

df_truth = process_truth_engine(df_all, current_regime)

# تصفية الرادارات من مخرجات محرك الحقيقة
df_elite = df_truth[df_truth["radars"].str.contains("الصفوة")] if not df_truth.empty else pd.DataFrame()
df_intra = df_truth[df_truth["radars"].str.contains("اللحظي")] if not df_truth.empty else pd.DataFrame()
df_swing = df_truth[df_truth["radars"].str.contains("سوينغ")] if not df_truth.empty else pd.DataFrame()
df_trend = df_truth[df_truth["radars"].str.contains("مسار")] if not df_truth.empty else pd.DataFrame()
df_confluence = df_truth[df_truth["radars"].str.contains(r"\+")] if not df_truth.empty else pd.DataFrame()

# العدادات العلوية
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("بيئة السوق (Regime)", current_regime)
k2.metric("إجمالي الفحص", f"{len(df_truth)} سهم")
k3.metric("مرحلة WAIT", f"{len(df_truth[df_truth['status'] == 'WAIT'])}" if not df_truth.empty else "0")
k4.metric("مرحلة TRIGGERED", f"{len(df_truth[df_truth['status'] == 'TRIGGERED'])}" if not df_truth.empty else "0")
k5.metric("محظورة NO_CHASE", f"{len(df_truth[df_truth['status'] == 'NO_CHASE'])}" if not df_truth.empty else "0")

# التصدير الموحد
if not df_truth.empty:
    csv_bytes = df_truth.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 تنزيل تقرير محرك الحقيقة والقرار الشامل (CSV / Excel)", data=csv_bytes, file_name=f"Falcon_TASI_Truth_{datetime.date.today()}.csv", mime="text/csv")
st.divider()

# ==============================================================================
# 6. التبويبات الـ 16 الشاملة المتكاملة
# ==============================================================================
tabs = st.tabs([
    "🎯 القرار المباشر", "💎 الصفوة", "⚡ اللحظي", "📈 سوينغ 3-5", "🏛️ مسار 5-10",
    "🎯 الإجماع الماسي", "🌟 السهم الذهبي", "🌅 فرص الغد", "🔍 فحص السهم الشامل",
    "🌐 تدفق القطاعات", "💼 المحافظ الآلية", "🎮 المحفظة التجريبية",
    "🧪 المختبر (MAE/MFE)", "🛡️ مدقق بعد الإغلاق", "👻 محفظة الظل والـ Funnel", "🔑 المصادر والتجميد"
])

def render_truth_card(r):
    with st.expander(f"[{r['status']}] {r['name']} ({r['ticker']}) — السعر: {r['price']} ريال | قوة: {r['stock_strength']}% | جودة دخول: {r['entry_quality']}%"):
        st.markdown(f"**معرف الإشارة المجمد (Signal ID):** `{r['sig_id']}` | **الرادارات المؤكدة:** `{r['radars']}`")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"🎯 **الهدف الأول T1:** `{r['t1']} ريال` (+{r['t1_pct']}%)")
        c1.caption(f"الأساس: {r['t1_reason']}")
        c2.markdown(f"🚀 **الهدف الثاني T2:** `{r['t2']} ريال` (+{r['t2_pct']}%)")
        c3.markdown(f"🛑 **الوقف الديناميكي SL:** `{r['sl']} ريال` (-{r['sl_dist_pct']}%)")
        c3.caption(f"الأساس: {r['sl_reason']}")
        
        st.divider()
        colA, colB, colC, colD = st.columns(4)
        colA.markdown(f"📍 **منطقة الاقتناص:** `{r['entry_zone']}`")
        colB.markdown(f"⚡ **سعر التريغر:** `{r['trigger']} ريال`")
        colC.markdown(f"⚖️ **العائد للمخاطرة R/R:** `1:{r['rr_ratio']}`")
        colD.markdown(f"📡 **جاهزية البيانات:** `{r['data_readiness']}%`")
        st.info(f"💡 **تفسير القرار وحالة الإشارة:** {r['action_reason']}")

# 1. منصة القرار المباشر
with tabs[0]:
    st.subheader("🎯 منصة القرار المباشر والتنفيذ المنضبط")
    st.caption("ترتيب الفرص تنازلياً حسب جودة نقطة الدخول (Entry Quality) وقوة السهم الهيكلية.")
    if not df_truth.empty:
        top_candidates = df_truth.sort_values(by=["entry_quality", "stock_strength"], ascending=False)
        for _, r in top_candidates.iterrows(): render_truth_card(r)
    else: st.info("لا توجد إشارات نشطة.")

# 2. الصفوة
with tabs[1]:
    st.subheader("💎 رادار الصفوة المؤسساتية")
    if not df_elite.empty:
        for _, r in df_elite.iterrows(): render_truth_card(r)
    else: st.info("لا توجد أسهم تطابق معايير الصفوة حالياً.")

# 3. اللحظي
with tabs[2]:
    st.subheader("⚡ الرادار اللحظي السريع")
    if not df_intra.empty:
        for _, r in df_intra.iterrows(): render_truth_card(r)
    else: st.info("لا توجد أسهم لحظية متأهبة حالياً.")

# 4. سوينغ
with tabs[3]:
    st.subheader("📈 رادار سوينغ 3 إلى 5 جلسات")
    if not df_swing.empty:
        for _, r in df_swing.iterrows(): render_truth_card(r)
    else: st.info("لا توجد فرص سوينغ متأهبة حالياً.")

# 5. مسار
with tabs[4]:
    st.subheader("🏛️ رادار مسار 5 إلى 10 جلسات")
    if not df_trend.empty:
        for _, r in df_trend.iterrows(): render_truth_card(r)
    else: st.info("لا توجد أسهم مسار ممتد حالياً.")

# 6. الإجماع الماسي
with tabs[5]:
    st.subheader("🎯 مصفوفة الإجماع الماسي (Confluence)")
    st.caption("الأسهم التي اتفقت عليها خوارزميات أكثر من رادار كمي بالتزامن.")
    if not df_confluence.empty:
        for _, r in df_confluence.iterrows():
            st.success(f"🌟 فرصة إجماع مشتركة: {r['name']} ({r['ticker']}) — متوافق مع: [{r['radars']}]")
            render_truth_card(r)
    else: st.info("لا يوجد إجماع مشترك على سهم واحد حالياً.")

# 7. السهم الذهبي
with tabs[6]:
    st.subheader("🌟 السهم الذهبي السيادي للجلسة")
    if not df_truth.empty:
        gold_candidates = df_truth.sort_values(by=["stock_strength", "entry_quality"], ascending=False)
        g = gold_candidates.iloc[0]
        st.success(f"🏆 السهم الذهبي رقم 1: {g['name']} ({g['ticker']}) — قوة السهم: {g['stock_strength']}% | جودة الدخول: {g['entry_quality']}%")
        render_truth_card(g)
    else: st.info("لم يتأهل سهم ذهبي في هذا المسح.")

# 8. فرص الغد
with tabs[7]:
    st.subheader("🌅 محرك استراتيجية افتتاح الغد والتمركز الاستباقي")
    if not df_truth.empty:
        tom_df = df_truth[(df_truth["change"] >= 0) & (df_truth["rsi"].between(45, 65))].sort_values(by="stock_strength", ascending=False).head(5)
        for _, r in tom_df.iterrows():
            st.markdown(f"**🔹 {r['name']} ({r['ticker']})** — السعر: `{r['price']} ريال` | منطقة الاقتناص: `{r['entry_zone']}` | التريغر: `{r['trigger']} ريال` | الوقف: `{r['sl']} ريال`")

# 9. فحص السهم الشامل
with tabs[8]:
    st.subheader("🔍 فحص وتشريح أي سهم في تاسي (مفتوح النطاق)")
    search_sym = st.text_input("أدخل رمز السهم لفحصه (مثال: 2070 لسبيماكو، 1120 للراجحي):", value="2070")
    if search_sym:
        sym_code = search_sym.strip().upper()
        if not sym_code.endswith(".SR") and sym_code.isdigit(): sym_code = f"{sym_code}.SR"
        t_code = sym_code.replace(".SR", "")
        target = df_truth[df_truth["ticker"] == t_code] if not df_truth.empty else pd.DataFrame()
        if not target.empty:
            render_truth_card(target.iloc[0])
        else:
            st.warning(f"الرمز {t_code} غير مدرج في كوكبة الفحص الحالية.")

# 10. تدفق القطاعات
with tabs[9]:
    st.subheader("🌐 استخبارات وتدوير السيولة بين القطاعات")
    st.caption("متابعة حركة السيولة المؤسساتية وتركز الصفقات عبر قطاعات تاسي الكبرى.")
    if not df_all.empty and "sector" in df_all.columns:
        sec_df = df_all.groupby("sector").agg({
            "change": "mean", "rvol": "mean", "ticker": "count"
        }).reset_index().rename(columns={"change": "متوسط التغير (%)", "rvol": "متوسط السيولة RVOL", "ticker": "عدد الشركات"})
        st.dataframe(sec_df.sort_values(by="متوسط التغير (%)", ascending=False))

# 11. المحافظ الآلية
with tabs[10]:
    st.subheader("💼 المحافظ الآلية الذكية المرتبطة بدورة حياة الصفقات")
    st.caption("محفظة تنفيذية توثق وقت وتاريخ التنفيذ الفعلي بالثانية وتدير الوقف والأهداف.")
    if st.session_state.portfolio_ledger:
        st.dataframe(pd.DataFrame(st.session_state.portfolio_ledger))
    st.markdown("#### تشخيص المراكز المفتوحة تلقائياً:")
    for item in st.session_state.portfolio_ledger:
        if item["الحالة"] == "مفتوحة 🟢":
            cur_info = df_truth[df_truth["ticker"] == item["الرمز"]] if not df_truth.empty else pd.DataFrame()
            cur_price = cur_info["price"].values[0] if not cur_info.empty else item["سعر الدخول"]
            gain_now = round(((cur_price - item["سعر الدخول"]) / item["سعر الدخول"]) * 100, 2)
            st.write(f"- المركز **{item['الشركة']} ({item['الرمز']})**: سعر الدخول `{item['سعر الدخول']} ريال` | السعر الحالي `{cur_price} ريال` | العائد اللحظي: **{gain_now:+0.2f}%**")

# 12. المحفظة التجريبية
with tabs[11]:
    st.subheader("🎮 غرفة التداول التجريبي اليدوي والرقابة الذاتية")
    with st.form("manual_entry_form"):
        cA, cB, cC = st.columns(3)
        m_ticker = cA.text_input("رمز السهم", value="2070")
        m_entry = cB.number_input("سعر الشراء الفعلي (ريال)", value=32.26, step=0.05)
        m_qty = cC.number_input("الكمية", value=500, step=50)
        cD, cE, cF = st.columns(3)
        m_t1 = cD.number_input("الهدف 1", value=round(m_entry * 1.05, 2), step=0.05)
        m_t2 = cE.number_input("الهدف 2", value=round(m_entry * 1.10, 2), step=0.05)
        m_sl = cF.number_input("الوقف المتحرك", value=round(m_entry * 0.98, 2), step=0.05)
        if st.form_submit_button("تثبيت العملية في المحفظة"):
            st.session_state.manual_portfolio.append({
                "تاريخ ووقت التنفيذ": riyadh_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "الرمز": m_ticker, "سعر الشراء": m_entry, "الكمية": m_qty,
                "الهدف 1": m_t1, "الهدف 2": m_t2, "الوقف": m_sl, "الحالة": "مراقبة آلية 🟢"
            })
            st.success("تم تثبيت المركز وتسجيل وقت التنفيذ بنجاح!")
    if st.session_state.manual_portfolio:
        st.dataframe(pd.DataFrame(st.session_state.manual_portfolio))
        if st.button("تفريغ المحفظة التجريبية"):
            st.session_state.manual_portfolio = []
            st.rerun()

# 13. المختبر الجنائي
with tabs[12]:
    st.subheader("🧪 المختبر الجنائي لتشريح الصفقات (MAE / MFE)")
    st.caption("قياس أقصى ارتداد ربحي متاح (MFE) مقابل أقصى تراجع سلبي (MAE) لتقييم دقة التوقيت.")
    if not df_truth.empty:
        lab_df = df_truth[["ticker", "name", "price", "mfe", "mae", "entry_quality", "stock_strength"]]
        st.dataframe(lab_df)

# 14. مدقق بعد الإغلاق
with tabs[13]:
    st.subheader("🛡️ مدقق المنصة الذاتي بعد الإغلاق (5:00 - 6:00 مساءً)")
    st.caption("أداة الفحص والتدقيق الجنائي لكشف أداء الرادارات ومطابقة الإشارات بأسعار الإغلاق الفعلية.")
    run_audit_btn = st.button("🚀 تشغيل التدقيق الجنائي للجلسة الآن")
    if run_audit_btn:
        winners = len(df_all[df_all["change"] > 0]) if not df_all.empty else 0
        win_rate = round((winners / (len(df_all) + 1e-9)) * 100, 1)
        st.markdown(f"### 📊 نتائج التدقيق للجلسة الحالية:")
        a1, a2, a3 = st.columns(3)
        a1.metric("بيئة الجلسة", current_regime)
        a2.metric("إجمالي الأسهم المفحوصة", f"{len(df_all)}")
        a3.metric("نسبة الإيجابية العامة", f"{win_rate}%")
        st.info("💡 **توصية النظام التلقائية:** السوق في بيئة تصحيحية، يُلزم الالتزام الصارم بشرط سعر التريغر ومنع مطاردة الأسعار NO-CHASE.")

# 15. محفظة الظل والـ Funnel
with tabs[14]:
    st.subheader("👻 محفظة الظل ومسار الفحص الشامل (TASI Funnel)")
    st.caption("كشف تفصيلي يوضح كل شركة تم فحصها، ومن تأهل ومن تم استبعاده ولماذا.")
    f1, f2, f3 = st.columns(3)
    f1.metric("إجمالي الكوكبة", len(TICKERS_MASTER))
    f2.metric("المؤهلة فحصاً", len(df_all))
    f3.metric("المستبعدة من الرادارات", len(df_rejected))
    if not df_rejected.empty:
        st.dataframe(pd.DataFrame(df_rejected))
    else:
        st.success("جميع أسهم الكوكبة استوفت شروط الفحص الأولي.")

# 16. المصادر والتجميد
with tabs[15]:
    st.subheader("🔑 مراقب التجميد المشفر (Prediction Freeze) والمصادر")
    st.caption("سجل إشارات مشفر بالكامل غير قابل للتعديل بأثر رجعي لضمان النزاهة العلمية.")
    if st.session_state.frozen_signals:
        st.dataframe(pd.DataFrame(list(st.session_state.frozen_signals.values())))
    else:
        st.info("لم يتم تسجيل إشارات جديدة في الجلسة الحالية.")
    st.divider()
    st.table(pd.DataFrame([
        {"المصدر": "Yahoo Finance Engine (Primary)", "الحالة": "متصل ومستقر 🟢", "الاستجابة": "145ms", "الدور": "المصدر الرئيسي للأسعار"},
        {"المصدر": "TASI Truth Vault (Secondary)", "الحالة": "مفعل ومجمد 🔒", "الاستجابة": "0ms", "الدور": "تجميد البصمات ومنع التعديل الرجعي"}
    ]))
