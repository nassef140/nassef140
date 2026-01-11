import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات الواجهة
st.set_page_config(page_title="AI Multi-Source Radar", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 رادار السيولة اللحظي (Yahoo + Alpha Vantage)")
st.markdown(f"**📍 توقيت القاهرة:** `{cairo_now}`")
st.write("---")

# صف البحث وزر التحديث القسري
col_search, col_refresh = st.columns([3, 1])
with col_search:
    ticker_input = st.text_input("أدخل كود السهم (LCSW, COMI):", "LCSW")
with col_refresh:
    st.write(" ") 
    force_update = st.button("🚀 تحديث زارا")

def get_comprehensive_data(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        
        # --- [المصدر 1: ياهو فاينانس للسعر اللحظي] ---
        ticker = yf.Ticker(symbol)
        live_df = ticker.history(period="1d")
        
        if live_df.empty:
            return {"error": "فشل جلب البيانات من المصدر الرئيسي."}
            
        last_price = live_df['Close'].iloc[-1]
        prev_close = ticker.info.get('previousClose', last_price)
        change_pct = ((last_price - prev_close) / prev_close) * 100

        # --- [المصدر 2: التحليل الاستراتيجي SMC] ---
        # جلب البيانات التاريخية للتحليل (4 ساعات)
        df = yf.download(symbol, period="250d", interval="4h", auto_adjust=True, progress=False)
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_convert(cairo_tz) if df.index.tz else df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # استراتيجية SMC والقياس الرقمي
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        
        # مستويات فيبوناتشي
        h_max, l_min = df['High'].max(), df['Low'].min()
        fib_entry = l_min + (h_max - l_min) * 0.618
        fib_target = h_max
        stop_loss = l_min * 0.98

        # محرك AI للتوقع
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features = ['FVG', macd_h]
        clean = df.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(clean[features][:-1], clean['Target'][:-1])
        prob = model.predict_proba(clean[features].iloc[[-1]])[0][1]

        return {
            "symbol": symbol, "price": last_price, "change": change_pct,
            "confidence": round(prob * 100, 1), "fvg": df['FVG'].iloc[-1],
            "rsi": rsi, "entry": fib_entry, "target": fib_target, "stop": stop_loss
        }
    except Exception as e:
        return {"error": str(e)}

if ticker_input or force_update:
    with st.spinner('جاري مزامنة البيانات من ياهو و Alpha Vantage...'):
        res = get_comprehensive_data(ticker_input)
    
    if res and "error" not in res:
        # عرض السعر اللحظي ونسبة التغيير (الإضافة الجديدة)
        c_color = "#00ff00" if res['change'] >= 0 else "#ff4b4b"
        st.markdown(f"""
        <div style="background-color:#1e1e1e; padding:20px; border-radius:10px; border-left: 5px solid {c_color}">
            <h2 style="margin:0;">السعر الحالي: {res['price']:.2f} ج.م</h2>
            <h3 style="margin:0; color:{c_color};">التغيير اليومي: {res['change']:.2f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")

        # تقرير الاستراتيجية (SMC)
        st.subheader("📊 بصمة السيولة والذكاء الاصطناعي")
        col1, col2 = st.columns(2)
        col1.metric("ثقة الاتجاه", f"{res['confidence']}%")
        col2.metric("حالة FVG", "دخول مؤسسات ✅" if res['fvg'] == 1 else "تخارج مؤسسات ❌" if res['fvg'] == -1 else "هدوء")

        # تقرير المحلل الفني الكامل
        st.subheader("🖋️ رؤية المستشار الفني")
        if res['confidence'] >= 70 and res['price'] <= res['entry']:
            stance, msg = "🔵 تجميع (Buy Zone)", "السعر الحالي مثالي للدخول؛ المؤسسات تدعم هذا المستوى تاريخياً."
        elif res['rsi'] > 75:
            stance, msg = "🔴 تضخم (Overbought)", "السعر ارتفع بشكل حاد؛ نسبة المخاطرة الآن أعلى من العائد المتوقع."
        else:
            stance, msg = "🟡 حياد (Waiting)", "ننتظر تأكيد كسر الهيكل السعري قبل اتخاذ قرار جديد."
        
        st.info(f"**القرار المقترح:** {stance}\n\n**التحليل:** {msg}")

        # أهداف التداول
        st.markdown("### **🎯 المستهدفات السعرية:**")
        st.success(f"🟢 منطقة الدخول: {res['entry']:.2f}")
        st.info(f"🔵 الهدف الأول: {res['target']:.2f}")
        st.error(f"🔴 وقف الخسارة: {res['stop']:.2f}")
    else:
        st.error(f"فشل التحديث: {res.get('error')}")

st.caption("تم تحديث البيانات قسرياً من خلال 'زارا' لضمان الدقة اللحظية.")
