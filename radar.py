import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات المزامنة والواجهة
st.set_page_config(page_title="AI Technical Pro", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("👨‍💻 المستشار الفني والمحرك الذكي")
st.markdown(f"**📅 التاريخ:** `{cairo_now}`")
st.write("---")

ticker_input = st.text_input("أدخل كود السهم (مثال: COMI, FWRY):", "COMI")

def get_technical_report(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        # جلب البيانات (معالجة تحديثات ياهو)
        df = yf.download(symbol, period="250d", interval="4h", auto_adjust=True, progress=False)
        if df.empty:
            df = yf.download(symbol, period="400d", interval="1d", auto_adjust=True, progress=False)
        
        if df.empty: return None

        # إصلاح الجداول والوقت
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_convert(cairo_tz) if df.index.tz else df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # 1. تحليل SMC (Fair Value Gap)
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        
        # 2. مؤشرات الزخم والقياس الرقمي
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]
        rsi = ta.rsi(df['Close'], length=14)
        
        # 3. فيبوناتشي (نقاط الدخول والبيع)
        h_max, l_min = df['High'].max(), df['Low'].min()
        fib_entry = l_min + (h_max - l_min) * 0.618  # منطقة الخصم الذهبية
        fib_target = h_max  # المستهدف القمة السابقة
        stop_loss = l_min * 0.98  # وقف الخسارة تحت آخر قاع

        # 4. تدريب الذكاء الاصطناعي ودقة التوقع
        df['Target_Next'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features = ['FVG', macd_h]
        clean = df.dropna()
        X, y = clean[features], clean['Target_Next']
        
        split = int(len(clean) * 0.8)
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(X[:split], y[:split])
        accuracy = model.score(X[split:], y[split:]) * 100
        prob = model.predict_proba(X.iloc[[-1]])[0][1]

        return {
            "symbol": symbol, "price": df['Close'].iloc[-1], "confidence": round(prob * 100, 1),
            "accuracy": round(accuracy, 1), "fvg": df['FVG'].iloc[-1], "rsi": rsi.iloc[-1],
            "entry": fib_entry, "target": fib_target, "stop": stop_loss
        }
    except Exception as e:
        return {"error": str(e)}

if ticker_input:
    with st.spinner('يتم الآن دمج رؤية المحلل مع نتائج الـ AI...'):
        data = get_technical_report(ticker_input)
    
    if data and "error" not in data:
        # --- الجزء الأول: نتائج الاستراتيجية الرقمية ---
        st.subheader("📊 أولاً: نتائج الاستراتيجية الرقمية (SMC/AI)")
        col1, col2, col3 = st.columns(3)
        col1.metric("ثقة المحرك", f"{data['confidence']}%")
        col2.metric("الدقة التاريخية", f"{data['accuracy']}%")
        col3.metric("بصمة المؤسسات (FVG)", "إيجابية ✅" if data['fvg'] == 1 else "سلبية ❌" if data['fvg'] == -1 else "محايدة")
        
        st.write("---")

        # --- الجزء الثاني: تقرير المحلل الفني ---
        st.subheader("🖋️ ثانياً: تقرير المحلل الفني")
        
        # صياغة رأي المحلل بناءً على البيانات
        if data['confidence'] >= 65 and data['price'] <= data['entry']:
            stance = "🔵 تجميع شراء"
            opinion = "السهم يتداول حالياً في مناطق خصم سعرية (Discount Zone). نلاحظ توافقاً بين بصمة المؤسسات والذكاء الاصطناعي، مما يعطي ضوءاً أخضر لبناء مراكز شرائية."
        elif data['rsi'] > 70:
            stance = "🔴 جني أرباح / خطر"
            opinion = "السهم دخل منطقة تشبع شرائي. بالرغم من قوة الاتجاه، إلا أن المخاطرة في الدخول الآن عالية. يفضل انتظار تصحيح لمستويات الفيبوناتشي."
        else:
            stance = "🟡 مراقبة"
            opinion = "السهم في منطقة عرضية. الزخم الحالي غير كافٍ لتأكيد اختراق القمم. ننصح بالانتظار حتى ظهور بصمة سيولة FVG واضحة."

        st.markdown(f"### **الرأي الفني:** {stance}")
        st.write(opinion)

        # --- الجزء الثالث: التوصية السعرية ---
        st.markdown("### **🎯 خريطة التداول المقترحة:**")
        st.success(f"📍 **نقطة الدخول المثالية:** {data['entry']:.2f} ج.م")
        st.info(f"🚀 **المستهدف الأول (جني أرباح):** {data['target']:.2f} ج.م")
        st.error(f"🛡️ **وقف الخسارة (إلزامي):** {data['stop']:.2f} ج.م")
        
        st.write("---")
        st.caption(f"تم إعداد التقرير آلياً. دقة المحلل على هذا السهم تاريخياً بلغت {data['accuracy']}%.")
    else:
        st.error(f"حدث خطأ: {data.get('error', 'تعذر جلب البيانات')}")
