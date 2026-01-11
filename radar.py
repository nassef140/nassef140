import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# --- [1. الإعدادات] ---
st.set_page_config(page_title="AI Zara - Risk Analyzer", layout="wide")
cairo_tz = pytz.timezone('Africa/Cairo')

st.title("🦅 محرك زارا - مقيم المخاطر الذكي")
st.write("---")

# --- [2. التحكم] ---
col_t, col_p, col_b = st.columns([2, 2, 1])
with col_t: ticker_input = st.text_input("كود السهم:", "LCSW")
with col_p: manual_price = st.number_input("السعر الحقيقي الآن:", value=0.0, format="%.2f")
with col_b: 
    st.write(" ")
    run_btn = st.button("🚀 تحليل وتحكم")

def run_risk_engine(symbol_raw, m_price):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        df = yf.download(symbol, period="300d", interval="1d", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        current_price = m_price if m_price > 0 else df['Close'].iloc[-1]
        
        # حقن السعر اللحظي
        if current_price != df['Close'].iloc[-1]:
            new_data = pd.DataFrame({'Open':[current_price],'High':[current_price],'Low':[current_price],'Close':[current_price],'Volume':[0]}, index=[pd.Timestamp.now(tz=cairo_tz)])
            df = pd.concat([df, new_data])

        # حساب SMC و فيبوناتشي
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        h_max, l_min = df['High'].tail(100).max(), df['Low'].tail(100).min()
        fib_entry = l_min + (h_max - l_min) * 0.618
        
        # --- [جديد: حساب نسبة المخاطرة للعائد] ---
        potential_profit = h_max - current_price
        potential_loss = current_price - (l_min * 0.98)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0

        # AI
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        clean = df.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(clean[['FVG']][:-1], clean['Target'][:-1])
        prob = model.predict_proba(clean[['FVG']].iloc[[-1]])[0][1]

        return {
            "price": current_price, "confidence": round(prob * 100, 1),
            "fvg": df['FVG'].iloc[-1], "entry": fib_entry, "target": h_max, 
            "stop": l_min * 0.98, "rr_ratio": round(rr_ratio, 2)
        }
    except Exception as e: return {"error": str(e)}

if run_btn:
    res = run_risk_engine(ticker_input, manual_price)
    if "error" not in res:
        # عرض النتائج
        st.subheader(f"📊 تقرير المخاطرة والفرص: {ticker_input}")
        
        # تصميم بطاقة نسبة المخاطرة
        rr = res['rr_ratio']
        rr_color = "green" if rr >= 2 else "orange" if rr >= 1.5 else "red"
        
        c1, c2, c3 = st.columns(3)
        c1.metric("السعر المعتمد", f"{res['price']:.2f}")
        c2.metric("نسبة المخاطرة للعائد", f"1 : {rr}", delta=f"{'ممتازة' if rr>=2 else 'ضعيفة'}")
        c3.metric("ثقة المحرك", f"{res['confidence']}%")

        st.write("---")

        # تقرير المحلل الفني المتكامل
        st.subheader("🖋️ تقرير المحلل الفني")
        
        quality = "عالية الجودة" if rr >= 2 and res['confidence'] >= 65 else "متوسطة" if rr >= 1.5 else "عالية المخاطرة"
        
        opinion = f"الصفقة الحالية تعتبر **{quality}**. "
        if rr < 1.5:
            opinion += f"الربح المتوقع ({res['target']:.2f}) قريب جداً من السعر الحالي مقارنة بوقف الخسارة البعيد. لا ننصح بالدخول هنا."
        else:
            opinion += f"العائد المتوقع يساوِي {rr} ضعف المخاطرة، مما يجعلها صفقة منطقية حسابياً."

        st.info(f"**القرار:** {'🔵 تجميع' if rr >= 1.5 else '🟡 مراقبة'}\n\n**التحليل:** {opinion}")

        # المستهدفات
        st.success(f"📍 نقطة الدخول الذهبية: {res['entry']:.2f}")
        st.info(f"🚀 المستهدف (الربح): {res['target']:.2f}")
        st.error(f"🛡️ وقف الخسارة: {res['stop']:.2f}")
