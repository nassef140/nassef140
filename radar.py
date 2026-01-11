import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import plotly.graph_objects as go

st.set_page_config(page_title="AI Stock Alpha", layout="wide")

st.title("🤖 محرك الذكاء الاصطناعي المسيطر للبورصة المصرية")
st.write("القرار هنا يُتخذ بواسطة خوارزمية التعلم الآلي التي تحلل أنماط السيولة والزخم.")

ticker = st.text_input("أدخل رمز السهم للتحليل العميق:", "COMI")

def ai_dominant_analysis(symbol_input):
    try:
        symbol = f"{symbol_input.upper().strip()}.CA"
        # جلب بيانات موسعة لتدريب النموذج
        df = yf.download(symbol, period="200d", interval="1d", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 50:
            return None

        # --- تحضير البيانات للذكاء الاصطناعي ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)
        
        # تحديد الهدف: هل سيصعد السعر في اليوم التالي؟
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # تنظيف البيانات
        features = ['RSI', 'EMA_20', 'FVG']
        # إضافة أعمدة الماكد ديناميكياً
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features.extend(macd_cols)
        
        data_clean = df.dropna()
        X = data_clean[features]
        y = data_clean['Target']

        # --- تدريب محرك القرار (Random Forest) ---
        # المعامل الرقمي 27 يستخدم هنا كقاعدة لبناء الغابة العشوائية
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # التنبؤ بالحالة القادمة
        current_features = X.iloc[[-1]]
        prediction_prob = model.predict_proba(current_features)[0][1]
        ai_confidence = round(prediction_prob * 100, 2)

        return df, ai_confidence, symbol, model, features

    except Exception as e:
        st.error(f"Error: {e}")
        return None

if ticker:
    res = ai_dominant_analysis(ticker)
    if res:
        df, confidence, full_name, model, feature_names = res
        
        # عرض "عقل" الذكاء الاصطناعي
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("ثقة الذكاء الاصطناعي بالصعود", f"{confidence}%")
            if confidence > 60:
                st.success("🤖 القرار: شراء - النمط إيجابي جداً")
            elif confidence < 40:
                st.error("🤖 القرار: بيع/تجنب - النمط سلبي")
            else:
                st.warning("🤖 القرار: منطقة حيرة - النمط غير مكتمل")

        with col2:
            # أهمية المؤشرات بالنسبة للذكاء الاصطناعي
            importances = model.feature_importances_
            feat_imp = pd.Series(importances, index=feature_names).sort_values()
            st.write("📊 ترتيب المؤشرات حسب تأثيرها على قرار الـ AI حالياً:")
            st.bar_chart(feat_imp)

        # الرسم البياني
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(title=f"تحليل المسار الذكي لـ {full_name}")
        st.plotly_chart(fig, use_container_width=True)

        st.info(f"💡 الذكاء الاصطناعي قام بمعالجة {len(df)} يوم تداول لاتخاذ هذا القرار.")
