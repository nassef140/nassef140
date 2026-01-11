import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go

# إعدادات الصفحة
st.set_page_config(page_title="رادار البورصة المصرية الذكي", layout="wide")

st.title("🧠 نظام تحليل الأسهم بالذكاء الاصطناعي")
st.write("تحليل معتمد على بصمة المؤسسات (FVG) والمعامل الرقمي 27")

# مدخلات المستخدم
ticker = st.text_input("أدخل رمز السهم (مثال: COMI, FAWR, EAST):", "COMI")

CALC_FACTOR = 27

def analyze_stock(symbol_input):
    try:
        symbol = f"{symbol_input.upper().strip()}.CA"
        df = yf.download(symbol, period="150d", interval="4h", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < CALC_FACTOR:
            st.error("بيانات غير كافية لهذا السهم.")
            return None

        # 1. بصمة المؤسسات (FVG)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)

        # 2. التحليل الرقمي (MACD)
        df.ta.macd(append=True)
        macd_col = [c for c in df.columns if 'MACDh' in c][0]

        # 3. فيبوناتشي
        hi, lo = float(df['High'].max()), float(df['Low'].min())
        curr_p = float(df['Close'].iloc[-1])
        fib_618 = hi - (0.618 * (hi - lo))

        # 4. محرك الذكاء الاصطناعي
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        clean_df = df.dropna()
        X = clean_df[[macd_col, 'FVG']]
        y = clean_df['Target']
        
        model = RandomForestClassifier(n_estimators=CALC_FACTOR, random_state=42)
        model.fit(X[:-1], y[:-1])
        
        prob = model.predict_proba(X.iloc[[-1]])[0][1]
        power = round(prob * 100, 1)

        return df, curr_p, fib_618, power, symbol

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return None

if ticker:
    result = analyze_stock(ticker)
    if result:
        df, curr_p, fib_618, power, full_symbol = result
        
        # عرض النتائج في أعمدة
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("السعر الحالي", f"{curr_p:.2f} ج.م")
        with col2:
            st.metric("قوة التنبؤ الذكي", f"{power}%")
        with col3:
            st.metric("مستوى الخصم (0.618)", f"{fib_618:.2f}")

        # تحديد التوصية
        if power >= 65 and curr_p <= fib_618:
            st.success("🏁 القرار النهائي: شراء قوي (تمركز مؤسسات)")
        elif power >= 50:
            st.warning("🏁 القرار النهائي: مراقبة وانتظار سيولة")
        else:
            st.error("🏁 القرار النهائي: خطر / بيع محتمل")

        # رسم بياني تفاعلي
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="السعر")])
        
        fig.add_hline(y=fib_618, line_dash="dash", line_color="green", annotation_text="منطقة الخصم")
        fig.update_layout(title=f"الرسم البياني لسهم {full_symbol}", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.write("---")
        st.info("💡 ملاحظة: هذا التحليل يعتمد على خوارزمية 'الغابة العشوائية' مع مراعاة فجوات السيولة المؤسسية.")
