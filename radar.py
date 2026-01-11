import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات المزامنة بتوقيت القاهرة
st.set_page_config(page_title="AI Textual Analysis - EGX", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🤖 محرك التحليل النصي الذكي")
st.write(f"📍 **توقيت القاهرة الحالي:** `{cairo_now}`")
st.write("---")

# 2. إدخال كود السهم
ticker_input = st.text_input("أدخل كود البورصة المصرية (مثال: COMI, FWRY):", "COMI")

def ai_textual_engine(symbol_input):
    try:
        symbol = symbol_input.upper().strip()
        if not symbol.endswith(".CA"):
            symbol = f"{symbol}.CA"
            
        # جلب البيانات لفريم 4 ساعات
        df = yf.download(symbol, period="300d", interval="4h", progress=False)
        
        if df.empty or len(df) < 50:
            return None

        # مزامنة التوقيت
        df.index = df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # --- هندسة الميزات للذكاء الاصطناعي ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)
        
        # التنبؤ
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features = ['RSI', 'EMA_20', 'FVG'] + macd_cols
        
        data_clean = df.dropna()
        X = data_clean[features]
        y = data_clean['Target']

        # محرك القرار (المعامل الرقمي 27)
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # استخراج النتائج النهائية
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = ((last_price - prev_price) / prev_price) * 100
        prediction_prob = model.predict_proba(X.iloc[[-1]])[0][1]
        ai_confidence = round(prediction_prob * 100, 2)
        
        # تحليل بصمة السيولة
        fvg_status = "رصد سيولة مؤسسية (FVG) نشطة حالياً" if df['FVG'].iloc[-1] == 1 else "لا توجد بصمة سيولة واضحة في الشمعة الحالية"
        rsi_val = df['RSI'].iloc[-1]

        return {
            "symbol": symbol,
            "price": last_price,
            "change": change,
            "confidence": ai_confidence,
            "fvg": fvg_status,
            "rsi": rsi_val,
            "trend": "صاعد" if last_price > df['EMA_20'].iloc[-1] else "هابط"
        }

    except Exception as e:
        st.error(f"خطأ في التحليل: {e}")
        return None

if ticker_input:
    with st.spinner('جاري معالجة البيانات وتحليل الأنماط...'):
        data = ai_textual_engine(ticker_input)
    
    if data:
        # صياغة التقرير النصي المسيطر
        st.subheader(f"📄 تقرير الذكاء الاصطناعي للسهم: {data['symbol']}")
        
        # تحديد لون الحالة
        if data['confidence'] >= 65:
            decision = "🟢 إشارة شراء قوية (Strong Buy Signal)"
            summary = "يهيمن النمط الشرائي على حركة السهم حالياً، مع توافق المؤشرات الفنية للتحرك نحو مستويات أعلى."
        elif data['confidence'] <= 35:
            decision = "🔴 إشارة بيع/تجنب (Strong Sell Signal)"
            summary = "يرصد الذكاء الاصطناعي ضغوطاً بيعية قوية وتخارجاً محتملاً للسيولة، مما يرفع نسبة المخاطرة."
        else:
            decision = "🟡 حالة انتظار (Neutral Zone)"
            summary = "السعر يتحرك في نطاق عرضي أو غير
