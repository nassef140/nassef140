import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. المزامنة بتوقيت القاهرة
st.set_page_config(page_title="AI Bold Advisor - EGX", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 المستشار الذكي الجريء - البورصة المصرية")
st.markdown(f"**📍 حالة السوق الآن:** `{cairo_now}`")
st.write("---")

ticker_input = st.text_input("أدخل كود السهم لتحليل استشاري عميق (مثال: COMI, FWRY):", "COMI")

def ai_bold_advisor(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        df = yf.download(symbol, period="300d", interval="4h", progress=False)
        
        if df.empty or len(df) < 50:
            return None

        # مزامنة البيانات
        df.index = df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # هندسة المؤشرات المتقدمة
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0) # فجوة القيمة العادلة (سيولة)
        
        # الذكاء الاصطناعي - التدريب
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        macd_cols = [c for c in df.columns if 'MACD' in c]
        features = ['RSI', 'EMA_20', 'FVG', 'ATR'] + macd_cols
        
        clean = df.dropna()
        X = clean[features]
        y = clean['Target']

        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:-1], y[:-1])

        # الحسابات الاستشارية
        prob = model.predict_proba(X.iloc[[-1]])[0][1]
        confidence = round(prob * 100, 2)
        curr_price = df['Close'].iloc[-1]
        atr_val = df['ATR'].iloc[-1]
        
        # حساب أهداف جريئة (Target & SL)
        target_price = curr_price + (atr_val * 2)
        stop_loss = curr_price - (atr_val * 1.5)

        return {
            "symbol": symbol, "price": curr_price, "confidence": confidence,
            "fvg": df['FVG'].iloc[-1], "rsi": df['RSI'].iloc[-1],
            "target": target_price, "sl": stop_loss, "trend": "صاعد" if curr_price > df['EMA_20'].iloc[-1] else "هابط"
        }
    except Exception as e:
        return {"error": str(e)}

if ticker_input:
    with st.spinner('يتم الآن اختراق البيانات وتحليل نوايا السيولة...'):
        res = ai_bold_advisor(ticker_input)
    
    if res and "error" not in res:
        st.subheader(f"📑 التقرير الاستشاري لسهم: {res['symbol']}")
        
        # صياغة الاستشارة بناءً على قوة الـ AI
        if res['confidence'] >= 70:
            advice_title = "🔥 اقتناص - فرصة هجومية"
            advice_text = f"الذكاء الاصطناعي يكتشف 'تجمعاً مؤسسياً' عنيفاً. النمط الحالي يشير إلى انفجار سعري قريب. **ادخل بجرأة** مع الالتزام بالأهداف."
            color = "green"
        elif res['confidence'] <= 30:
            advice_title = "⚠️ هروب - تحذير عالي الخطورة"
            advice_text = "يتم رصد عمليات 'توزيع' خفية. الذكاء الاصطناعي يشير إلى أن السهم فقد دعمه الرقمي. **لا تكن الضحية الأخيرة**، الخروج هو القرار الأذكى."
            color = "red"
        else:
            advice_title = "⏳ ترقب - السهم في منطقة تضليل"
            advice_text = "السيولة الحالية متذبذبة والذكاء الاصطناعي غير واثق من الاتجاه القادم. **احتفظ بسيولتك** حتى تتضح بصمة المؤسسات."
            color = "orange"

        # عرض التقرير الجريء
        st.markdown(f"### <span style='color:{color}'>{advice_title}</span>", unsafe_allow_html=True)
        st.info(f"💡 **الاستشارة الجريئة:** {advice_text}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **🔍 تفاصيل القوة الرقمية:**
            - السعر الحالي: **{res['price']:.2f} ج.م**
            - ثقة المحرك الذكي: **{res['confidence']}%**
            - الاتجاه العام: **{res['trend']}**
            """)
        
        with col2:
            st.markdown(f"""
            **🎯 الأهداف المقترحة (حسابات ATR):**
            - المستهدف الأول: **{res['target']:.2f} ج.م**
            - وقف الخسارة: **{res['sl']:.2f} ج.م**
            - بصمة السيولة (FVG): **{'مرصودة ✅' if res['fvg'] == 1 else 'غير واضحة ❌'}**
            """)

        # تحليل "خلف الكواليس"
        st.write("---")
        st.markdown(f"**🧠 رؤية AI العميقة:** السهم حالياً يتحرك بزخم (RSI: {res['rsi']:.2f}). النموذج الرقمي 27 يرى أن نسبة المخاطرة مقابل العائد في هذه اللحظة تعتبر {'مغرية' if res['confidence'] > 60 else 'غير متكافئة'}.")
    else:
        st.error("فشل في جلب البيانات الاستشارية. تأكد من كود السهم.")

st.caption("⚠️ هذا النظام هو محرك ذكاء اصطناعي مسيطر؛ الاستشارات مبنية على احتمالات إحصائية رقمية صرفة.")
