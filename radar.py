import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# --- [1. الإعدادات والواجهة] ---
st.set_page_config(page_title="AI Zara Elite Radar", layout="wide")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 المحرك المسيطر - تقرير النخبة الفني")
st.markdown(f"**📍 توقيت القاهرة:** `{cairo_now}`")
st.write("---")

# --- [2. شريط التحكم اللحظي] ---
col_search, col_price, col_btn = st.columns([2, 2, 1])
with col_search:
    ticker_input = st.text_input("🔍 أدخل كود السهم (مثال: LCSW, COMI):", "LCSW")
with col_price:
    manual_price = st.number_input("✍️ تصحيح السعر (أدخل السعر الحقيقي الآن):", value=0.0, format="%.2f")
with col_btn:
    st.write(" ")
    run_btn = st.button("🚀 تحليل عميق")

def run_elite_engine(symbol_raw, m_price):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        # جلب البيانات التاريخية
        df = yf.download(symbol, period="300d", interval="1d", auto_adjust=True, progress=False)
        if df.empty: return {"error": "تعذر جلب البيانات."}
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # دمج السعر اللحظي (زارا) لتصحيح البيانات
        current_price = m_price if m_price > 0 else df['Close'].iloc[-1]
        if current_price != df['Close'].iloc[-1]:
            new_row = pd.DataFrame({
                'Open': [current_price], 'High': [current_price], 
                'Low': [current_price], 'Close': [current_price], 'Volume': [0]
            }, index=[pd.Timestamp.now(tz=cairo_tz)])
            df = pd.concat([df, new_row])

        # --- [المحرك التقني: SMC + Momentum] ---
        # 1. سيولة المؤسسات (FVG & BOS)
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        df['BOS'] = np.where(df['Close'] > df['High'].rolling(10).max().shift(1), 1, 0)
        
        # 2. تحليل الزخم والسيولة
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]
        rsi = ta.rsi(df['Close'], length=14)
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1] if df['Volume'].rolling(20).mean().iloc[-1] > 0 else 1

        # 3. مستويات فيبوناتشي (الدورة السعرية)
        h_max, l_min = df['High'].tail(100).max(), df['Low'].tail(100).min()
        fib_entry = l_min + (h_max - l_min) * 0.618
        
        # --- [المحرك الذكي: AI Training] ---
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features = ['FVG', 'BOS', macd_h]
        clean = df.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(clean[features][:-1], clean['Target'][:-1])
        
        accuracy = model.score(clean[features][-30:], clean['Target'][-30:]) * 100
        prob = model.predict_proba(clean[features].iloc[[-1]])[0][1]

        return {
            "symbol": symbol, "price": current_price, "change": ((current_price - df['Close'].iloc[-2])/df['Close'].iloc[-2])*100,
            "confidence": round(prob * 100, 1), "accuracy": round(accuracy, 1),
            "fvg": df['FVG'].iloc[-1], "rsi": rsi.iloc[-1], "vol_ratio": vol_ratio,
            "entry": fib_entry, "target": h_max, "stop": l_min * 0.98
        }
    except Exception as e: return {"error": str(e)}

if run_btn:
    with st.spinner('جاري مزامنة الاستراتيجيات الرقمية...'):
        res = run_elite_engine(ticker_input, manual_price)
    
    if "error" not in res:
        # --- [3. عرض حالة السهم] ---
        p_color = "green" if res['change'] >= 0 else "red"
        st.subheader(f"📊 تقرير الأداء: {res['symbol']}")
        st.markdown(f"**السعر الحالي:** `{res['price']:.2f} ج.م` | **التغيير:** <span style='color:{p_color}'>{res['change']:.2f}%</span>", unsafe_allow_html=True)
        st.write("---")

        # --- [4. رادار الاستراتيجية الرقمية] ---
        st.subheader("🤖 أولاً: نتائج الاستراتيجية الرقمية (SMC/AI)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ثقة المحرك", f"{res['confidence']}%")
        c2.metric("الدقة التاريخية", f"{res['accuracy']}%")
        c3.metric("بصمة المؤسسات", "إيجابية ✅" if res['fvg'] == 1 else "سلبية ❌" if res['fvg'] == -1 else "هادئة")
        c4.metric("حجم التداول", "مرتفع 🔥" if res['vol_ratio'] > 1.2 else "طبيعي")
        st.write("---")

        # --- [5. تقرير المحلل الفني] ---
        st.subheader("🖋️ ثانياً: تقرير المحلل الفني")
        if res['confidence'] >= 65 and res['price'] <= res['entry']:
            stance, s_color = "🔵 تجميع شراء (Discount Zone)", "blue"
            opinion = f"السهم يتداول في منطقة خصم مثالية تحت {res['entry']:.2f}. توافق SMC مع الذكاء الاصطناعي يعطي أفضلية كبيرة للارتداد الصاعد."
        elif res['rsi'] > 75 or res['price'] >= res['target'] * 0.98:
            stance, s_color = "🔴 جني أرباح / خطر", "red"
            opinion = f"السعر دخل مناطق التشبع والاقتراب من المستهدف الرئيسي {res['target']:.2f}. الدخول هنا يرفع نسبة المخاطرة بشكل كبير."
        else:
            stance, s_color = "🟡 مراقبة (Neutral)", "orange"
            opinion = "السعر في منطقة توازن حيادية. يفضل انتظار تصحيح لمستويات الفيبوناتشي أو ظهور بصمة سيولة مؤسسية جديدة."

        st.markdown(f"### **القرار:** <span style='color:{s_color}'>{stance}</span>", unsafe_allow_html=True)
        st.info(f"💡 **التحليل العميق:** {opinion}")

        # --- [6. خريطة الأهداف] ---
        st.markdown("### **🎯 المستهدفات السعرية الرقمية:**")
        col_in, col_out, col_stop = st.columns(3)
        col_in.success(f"📍 نقطة الدخول الذهبية: {res['entry']:.2f}")
        col_out.info(f"🚀 المستهدف الأول: {res['target']:.2f}")
        col_stop.error(f"🛡️ وقف الخسارة: {res['stop']:.2f}")
    else: st.error(f"حدث خطأ: {res['error']}")
