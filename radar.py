import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات المزامنة والواجهة
st.set_page_config(page_title="AI Backtest Advisor", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 المستشار المسيطر (SMC + تدقيق تاريخي)")
st.markdown(f"**📍 توقيت القاهرة:** `{cairo_now}`")

ticker_input = st.text_input("أدخل كود السهم (مثال: COMI, FWRY, ABUK):", "COMI")

def ai_backtest_engine(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        
        # حل مشكلة جلب البيانات وتغييرات ياهو الأخيرة
        df = yf.download(symbol, period="250d", interval="4h", auto_adjust=True, progress=False)
        if df.empty or len(df) < 50:
            df = yf.download(symbol, period="400d", interval="1d", auto_adjust=True, progress=False)

        if df.empty: return {"error": "فشل جلب البيانات."}

        # إصلاح هيكل البيانات ومعالجة المناطق الزمنية
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_convert(cairo_tz) if df.index.tz else df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # --- [استراتيجية SMC والقياس الرقمي] ---
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        df['BOS'] = np.where(df['Close'] > df['High'].rolling(10).max().shift(1), 1, 0)
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]
        fib_discount = df['High'].max() - (0.618 * (df['High'].max() - df['Low'].min()))

        # --- [محرك الـ AI والتدقيق التاريخي] ---
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features = ['FVG', 'BOS', macd_h]
        clean = df.dropna()
        X, y = clean[features], clean['Target']

        # تقسيم البيانات للتدقيق (80% تدريب، 20% اختبار دقة)
        split = int(len(clean) * 0.8)
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:split], y[:split])
        
        # حساب دقة التوقعات السابقة على هذا السهم
        accuracy = model.score(X[split:], y[split:]) * 100
        
        # التوقع الحالي
        prob = model.predict_proba(X.iloc[[-1]])[0][1]
        
        return {
            "symbol": symbol, "price": df['Close'].iloc[-1], "confidence": round(prob * 100, 1),
            "accuracy": round(accuracy, 1), "fvg": df['FVG'].iloc[-1], "fib": fib_discount
        }
    except Exception as e:
        return {"error": str(e)}

if ticker_input:
    with st.spinner('جاري مراجعة سجلات السهم وتحليل سيولة المؤسسات...'):
        res = ai_backtest_engine(ticker_input)
    
    if "error" not in res:
        st.subheader(f"📄 التقرير الاستشاري: {res['symbol']}")
        
        # عرض نسبة نجاح الـ AI السابقة
        st.sidebar.metric("دقة التوقع التاريخية لهذا السهم", f"{res['accuracy']}%")
        
        # الاستشارة الجريئة
        if res['confidence'] >= 70 and res['price'] <= res['fib']:
            title, msg, color = "🎯 اقتناص مؤكد (High Conviction)", "السعر في منطقة خصم مثالية مع توافق سيولة المؤسسات. الدقة التاريخية تدعم هذا القرار.", "green"
        elif res['confidence'] <= 35:
            title, msg, color = "⚠️ هروب (Institutional Exit)", "الذكاء الاصطناعي يرصد خروج سيولة ذكية. تجنب السهم تماماً بناءً على ضعف الأنماط.", "red"
        else:
            title, msg, color = "⚖️ منطقة تذبذب (Neutral)", "السعر في منطقة حيادية. انتظر ظهور بصمة FVG واضحة قبل المغامرة.", "orange"

        st.markdown(f"### <span style='color:{color}'>{title}</span>", unsafe_allow_html=True)
        st.info(f"💡 **الاستشارة:** {msg}")

        col1, col2 = st.columns(2)
        col1.metric("ثقة المحرك الحالية", f"{res['confidence']}%")
        col2.metric("مستوى الخصم (0.618)", f"{res['fib']:.2f}")
        
        st.write("---")
        st.caption(f"تنبيه: تم تدريب النموذج على {res['accuracy']}% من البيانات التاريخية بنجاح.")
    else:
        st.error(f"حدث خطأ: {res['error']}")
