import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go
from datetime import datetime
import pytz

# 1. إعدادات الصفحة والمزامنة الزمنية
st.set_page_config(page_title="AI Egyptian Radar - 4H", layout="wide")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🤖 المحرك الذكي المسيطر - فريم 4 ساعات")
st.sidebar.markdown(f"### 📍 توقيت القاهرة\n`{cairo_now}`")
st.sidebar.info("التحليل الحالي يعتمد على إطار 4 ساعات لتوفير إشارات مضاربية دقيقة.")

# 2. إدخال كود السهم (البورصة المصرية)
ticker_input = st.text_input("أدخل كود السهم (مثال: COMI, FWRY, ABUK):", "COMI")

def ai_engine_4h(symbol_input):
    try:
        # تحويل المدخل لكود رويترز
        symbol = symbol_input.upper().strip()
        if not symbol.endswith(".CA"):
            symbol = f"{symbol}.CA"
            
        # جلب بيانات فريم 4 ساعات (نحتاج فترة زمنية كافية للتدريب)
        # ملاحظة: yfinance يدعم فريم 4h لآخر سنتين كحد أقصى
        df = yf.download(symbol, period="730d", interval="4h", progress=False)
        
        if df.empty or len(df) < 50:
            return None

        # مزامنة البيانات مع توقيت القاهرة
        df.index = df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # --- هندسة الميزات الفنية (AI Features) ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        # بصمة المؤسسات على فريم 4 ساعات
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0) 
        
        # الهدف: التنبؤ بحركة الشمعة (الـ 4 ساعات) القادمة
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # اختيار الميزات
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features = ['RSI', 'FVG'] + macd_cols
        
        data_clean = df.dropna()
        X = data_clean[features]
        y = data_clean['Target']

        # --- تدريب محرك RandomForest (نواة المعامل 27) ---
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # حساب احتمالية القرار المسيطر لشمعة الـ 4 ساعات القادمة
        prediction_prob = model.predict_proba(X.iloc[[-1]])[0][1]
        ai_score = round(prediction_prob * 100, 2)

        return df, ai_score, symbol, model, features

    except Exception as e:
        st.error(f"خطأ تقني: {e}")
        return None

if ticker_input:
    res = ai_engine_4h(ticker_input)
    
    if res:
        df, score, full_symbol, model, feature_list = res
        
        # عرض نتائج السيطرة الذكية
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(f"توقعات AI لـ {full_symbol} (4H)", f"{score}%")
            if score >= 60:
                st.success("🤖 القرار: شراء (نمط صاعد على 4 ساعات)")
            elif score <= 40:
                st.error("🤖 القرار: بيع (نمط هابط على 4 ساعات)")
            else:
