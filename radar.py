import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات الصفحة والمزامنة
st.set_page_config(page_title="AI Bold Advisor EGX", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 المستشار الذكي الجريء")
st.markdown(f"**📍 حالة السوق الفورية:** `{cairo_now}`")
st.write("---")

ticker_input = st.text_input("أدخل كود السهم (مثال: COMI, FWRY, LCSW):", "COMI")

def ai_bold_advisor_pro(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        
        # محاولة جلب البيانات (الأولوية لفريم 4 ساعات، ثم اليومي كخيار احتياطي)
        df = yf.download(symbol, period="200d", interval="4h", progress=False)
        if df.empty or len(df) < 30:
            df = yf.download(symbol, period="300d", interval="1d", progress=False)
        
        if df.empty or len(df) < 20:
            return {"error": "لا توجد بيانات كافية لهذا السهم حالياً."}

        # تصحيح تسمية الأعمدة
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # المزامنة مع توقيت القاهرة
        df.index = df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # حساب المؤشرات (هندسة الميزات)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)
        
        # تدريب المحرك الذكي
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features = ['RSI', 'EMA_20', 'FVG', 'ATR'] + macd_cols
        
        clean_df = df.dropna()
        X = clean_df[features]
        y = clean_df['Target']

        # المحرك المسيطر (نواة الرقم 27)
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # التحليلات النهائية
        prob = model.predict_proba(X.iloc[[-1]])[0][1]
        confidence = round(prob * 100, 1)
        price = df['Close'].iloc[-1]
        atr_v = df['ATR'].iloc[-1]

        return {
            "symbol": symbol, "price": price, "confidence": confidence,
            "fvg": df['FVG'].iloc[-1], "rsi": df['RSI'].iloc[-1],
            "target": price + (atr_v * 2), "sl": price - (atr_v * 1.5),
            "trend": "إيجابي" if price > df['EMA_20'].iloc[-1] else "سلبي"
        }
    except Exception as e:
        return {"error": f"حدث خطأ أثناء التحليل: {str(e)}"}

if ticker_input:
    with st.spinner('⚡ المحرك الذكي يقوم باختراق البيانات الآن...'):
        res = ai_bold_advisor_pro(ticker_input)
    
    if res and "error" not in res:
        st.subheader(f"📄 التقرير الاستشاري: {res['symbol']}")
        
        # تحديد حدة الاستشارة
        if res['confidence'] >= 68:
            title, msg, color = "🔥 هجوم - فرصة ذهبية", "الذكاء الاصطناعي يرصد سيولة مؤسسية ضخمة. النمط يوحي بانفجار سعري وشيك. لا تتردد في الاقتناص.", "green"
        elif res['confidence'] <= 35:
            title, msg, color = "⚠️ هروب - خطر مرتفع", "المحرك يحذر من تصريف خفي. السيولة تخرج ببطء. لا تكن آخر من يخرج من السفينة.", "red"
        else:
            title, msg, color = "⏳ مراقبة - فخ سعري", "السيولة متذبذبة والذكاء الاصطناعي غير واثق. السعر قد يكون في مرحلة تضليل. انتظر بصمة واضحة.", "orange"

        st.markdown(f"### <span style='color:{color}'>{title}</span>", unsafe_allow_html=True)
        st.info(f"💡 **الاستشارة الجريئة:** {msg}")

        # عرض الأرقام في أعمدة
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**💰 السعر الحالي:** `{res['price']:.2f} ج.م`")
            st.write(f"**🤖 ثقة المحرك:** `{res['confidence']}%` status: {res['trend']}")
        with c2:
            st.write(f"**🎯 هدف جريء:** `{res['target']:.2f}`")
            st.write(f"**🛡️ وقف الخسارة:** `{res['sl']:.2f}`")

        st.write("---")
        st.caption(f"تم رصد بصمة السيولة (FVG): {'✅ متوفرة' if res['fvg'] == 1 else '❌ غير مرصودة'}")
    else:
        st.error(f"❌ {res.get('error', 'فشل التحليل')}")

st.write("---")
st.markdown("⚠️ **تنبيه سيطرة:** هذا المحرك يتخذ قراراته بناءً على احتمالات رقمية؛ الاستشارة تعبر عن رؤية الآلة فقط.")
