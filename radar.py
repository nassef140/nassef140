import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات الواجهة
st.set_page_config(page_title="Zara Manual Control", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')

st.title("🦅 محرك زارا - السيطرة اليدوية الكاملة")
st.write("---")

# 2. وحدات الإدخال (البحث + تصحيح السعر)
col_t, col_p = st.columns([2, 2])
with col_t:
    ticker_input = st.text_input("كود السهم (مثال: LCSW):", "LCSW")
with col_p:
    # هنا تضع السعر الذي تراه في شاشتك الحقيقية (مثل 25.18)
    manual_price = st.number_input("السعر الحقيقي الآن (تصحيح):", value=0.0, format="%.2f")

def run_controlled_analysis(symbol_raw, m_price):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        # جلب البيانات التاريخية للأنماط
        df = yf.download(symbol, period="300d", interval="1d", auto_adjust=True, progress=False)
        
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        # "منطق السيطرة": استخدام سعرك اليدوي إذا تم إدخاله
        current_price = m_price if m_price > 0 else df['Close'].iloc[-1]
        
        # دمج السعر المصحح في مصفوفة البيانات لضبط المؤشرات
        if current_price != df['Close'].iloc[-1]:
            new_row = pd.DataFrame({
                'Open': [current_price], 'High': [current_price], 
                'Low': [current_price], 'Close': [current_price], 'Volume': [0]
            }, index=[pd.Timestamp.now(tz=cairo_tz)])
            df = pd.concat([df, new_row])

        # حساب SMC و Fibonacci بناءً على السعر المصحح
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        h_max, l_min = df['High'].tail(100).max(), df['Low'].tail(100).min()
        fib_entry = l_min + (h_max - l_min) * 0.618  # منطقة الخصم

        # محرك AI
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        clean = df.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(clean[['FVG']][:-1], clean['Target'][:-1])
        prob = model.predict_proba(clean[['FVG']].iloc[[-1]])[0][1]

        return {
            "symbol": symbol, "price": current_price, "confidence": round(prob * 100, 1),
            "fvg": df['FVG'].iloc[-1], "entry": fib_entry, "target": h_max, "stop": l_min * 0.98
        }
    except Exception as e:
        return {"error": str(e)}

if st.button("🚀 تنفيذ التحليل بالسعر المصحح"):
    res = run_controlled_analysis(ticker_input, manual_price)
    
    if "error" not in res:
        # عرض السعر المعتمد في التحليل
        st.info(f"📍 يتم التحليل الآن بناءً على السعر الحقيقي: {res['price']:.2f} ج.م")
        
        # تقرير المحلل الفني
        st.subheader("🖋️ تقرير المحلل الفني")
        
        if res['price'] >= res['target'] * 0.98:
            stance, color = "🔴 منطقة جني أرباح", "red"
            msg = "السعر وصل أو اقترب جداً من المستهدف الرئيسي. ينصح بتأمين الأرباح وعدم فتح مراكز جديدة."
        elif res['price'] <= res['entry']:
            stance, color = "🔵 منطقة تجميع (Discount)", "blue"
            msg = "السعر ما زال في منطقة الخصم الذهبية؛ فرصة جيدة بناءً على استراتيجية SMC."
        else:
            stance, color = "🟡 منطقة انتظار (Premium)", "orange"
            msg = "السعر تجاوز منطقة الدخول المثالية وهو الآن في طريق للمستهدف. المخاطرة تزداد."

        st.markdown(f"### **القرار:** <span style='color:{color}'>{stance}</span>", unsafe_allow_html=True)
        st.write(msg)

        # الأهداف الرقمية
        st.write("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("نقطة الدخول (Fib)", f"{res['entry']:.2f}")
        c2.metric("المستهدف الأول", f"{res['target']:.2f}")
        c3.metric("ثقة المحرك", f"{res['confidence']}%")
    else:
        st.error(f"حدث خطأ: {res['error']}")
