import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go
from datetime import datetime
import pytz

# 1. إعداد الصفحة والمزامنة بتوقيت القاهرة
st.set_page_config(page_title="نظام AI المسيطر - البورصة المصرية", layout="wide")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🤖 المحرك الذكي المسيطر (القرار للآلة)")
st.sidebar.info(f"📍 توقيت القاهرة الحالي: {cairo_now}")

# 2. إدخال كود رويترز
ticker_input = st.text_input("أدخل كود رويترز للسهم (مثال: COMI.CA, ABUK.CA, MFOT.CA):", "COMI.CA")

def ai_governed_analysis(symbol):
    try:
        # جلب البيانات (يتم التعامل مع الرمز ككود رويترز مباشرة)
        df = yf.download(symbol, period="200d", interval="1d", progress=False)
        
        if df.empty or len(df) < 50:
            return None

        # تحويل المؤشر الزمني لتوقيت القاهرة للمزامنة
        df.index = df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # --- هندسة الميزات للذكاء الاصطناعي ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0) # بصمة السيولة
        
        # الهدف: التنبؤ باتجاه الشمعة القادمة
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # اختيار الميزات التي سيسيطر بها الـ AI على القرار
        features = ['RSI', 'ATR', 'FVG']
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features.extend(macd_cols)
        
        data_clean = df.dropna()
        X = data_clean[features]
        y = data_clean['Target']

        # --- محرك RandomForest (المعامل الرقمي 27 في النواة) ---
        # هنا الـ AI يحلل الأنماط التاريخية ليعطي قراره الخاص
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # حساب احتمالية الصعود (السيطرة الذكية)
        last_row = X.iloc[[-1]]
        prediction_prob = model.predict_proba(last_row)[0][1]
        ai_score = round(prediction_prob * 100, 2)

        return df, ai_score, symbol, model, features

    except Exception as e:
        st.error(f"خطأ في معالجة البيانات: {e}")
        return None

if ticker_input:
    # التأكد من استخدام صيغة رويترز الصحيحة للبورصة المصرية
    if not ticker_input.upper().endswith(".CA"):
        st.warning("⚠️ تنبيه: أكواد البورصة المصرية في رويترز يجب أن تنتهي بـ .CA")
    
    result = ai_governed_analysis(ticker_input.upper())
    
    if result:
        df, score, name, model, feature_list = result
        
        # واجهة القرار المسيطر
        st.subheader(f"🔍 تحليل المحرك الذكي لسهم: {name}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("درجة ثقة الـ AI في الصعود", f"{score}%")
            if score >= 65:
                st.success("🤖 قرار الـ AI: شراء مؤكد (Strong Buy Signal)")
            elif score <= 35:
                st.error("🤖 قرار الـ AI: خروج/تجنب (Strong Sell Signal)")
            else:
                st.warning("🤖 قرار الـ AI: منطقة حياد (Neutral Zone)")
            
            st.write("---")
            st.write("**لماذا اتخذ الـ AI هذا القرار؟**")
            importances = model.feature_importances_
            feat_imp = pd.Series(importances, index=feature_list).sort_values(ascending=False)
            st.write(feat_imp)

        with col2:
            # الرسم البياني المزامر بتوقيت القاهرة
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=name
            )])
            fig.update_layout(title=f"حركة السعر (مزامنة القاهرة)", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        st.info("💡 تم تدريب النموذج وتحديث البيانات لتعمل بمزامنة توقيت القاهرة وتتبع أكواد رويترز (.CA).")
