import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import pytz

# 1. إعدادات المزامنة والواجهة
st.set_page_config(page_title="AI Stable Analysis + Volume", layout="centered")
cairo_tz = pytz.timezone('Africa/Cairo')
cairo_now = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🦅 المحرك الاستراتيجي (SMC + تحليل السيولة)")
st.markdown(f"**📍 حالة النظام:** `{cairo_now}`")
st.write("---")

# صف البحث والتحديث
col_search, col_refresh = st.columns([3, 1])
with col_search:
    ticker_input = st.text_input("أدخل كود السهم (مثال: LCSW, COMI):", "LCSW")
with col_refresh:
    st.write(" ") 
    zara_refresh = st.button("🔄 تحديث زارا")

def get_complete_analysis(symbol_raw):
    try:
        symbol = f"{symbol_raw.upper().strip()}.CA"
        
        # جلب أحدث بيانات (4 ساعات للتحليل الاستراتيجي)
        df = yf.download(symbol, period="300d", interval="4h", auto_adjust=True, progress=False)
        if df.empty:
            df = yf.download(symbol, period="400d", interval="1d", auto_adjust=True, progress=False)

        if df.empty: return {"error": "بيانات السهم غير متوفرة حالياً."}

        # تصحيح الجداول والتوقيت
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_convert(cairo_tz) if df.index.tz else df.index.tz_localize('UTC').tz_convert(cairo_tz)

        # حساب السعر ونسبة التغيير
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((last_price - prev_price) / prev_price) * 100

        # --- [تحليل السيولة التراكمي] ---
        # مقارنة الفوليوم الحالي بمتوسط 20 شمعة سابقة
        avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]
        vol_ratio = (current_volume / avg_volume) if avg_volume > 0 else 1

        # --- [تطبيق SMC/ICT] ---
        df['FVG'] = np.where((df['Low'] > df['High'].shift(2)), 1, np.where((df['High'] < df['Low'].shift(2)), -1, 0))
        df['BOS'] = np.where(df['Close'] > df['High'].rolling(10).max().shift(1), 1, 0)
        
        # مؤشرات الزخم
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]
        rsi_val = ta.rsi(df['Close'], length=14).iloc[-1]

        # فيبوناتشي الرقمي (آخر 100 شمعة)
        h_max, l_min = df['High'].tail(100).max(), df['Low'].tail(100).min()
        fib_entry = l_min + (h_max - l_min) * 0.618
        fib_target = h_max

        # تدريب المحرك الذكي
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        features = ['FVG', 'BOS', macd_h]
        clean = df.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=27)
        model.fit(clean[features][:-1], clean['Target'][:-1])
        prob = model.predict_proba(clean[features].iloc[[-1]])[0][1]

        return {
            "symbol": symbol, "price": last_price, "change": change_pct,
            "confidence": round(prob * 100, 1), "fvg": df['FVG'].iloc[-1],
            "rsi": rsi_val, "entry": fib_entry, "target": fib_target,
            "stop": l_min * 0.97, "vol_ratio": vol_ratio,
            "accuracy": model.score(clean[features][-30:], clean['Target'][-30:]) * 100
        }
    except Exception as e:
        return {"error": str(e)}

if ticker_input or zara_refresh:
    with st.spinner('يتم الآن فحص مستويات السيولة وخرائط فيبوناتشي...'):
        res = get_complete_analysis(ticker_input)
    
    if res and "error" not in res:
        # عرض حالة السعر اللحظية
        c_color = "green" if res['change'] >= 0 else "red"
        st.subheader(f"📑 تقرير السهم: {res['symbol']}")
        st.markdown(f"**آخر سعر:** `{res['price']:.2f} ج.م` | **التغيير:** <span style='color:{c_color}'>{res['change']:.2f}%</span>", unsafe_allow_html=True)
        
        st.write("---")

        # عرض مقاييس الاستراتيجية الرقمية
        st.markdown(f"### 🤖 تحليل السيولة والذكاء الاصطناعي (الدقة: {res['accuracy']:.1f}%)")
        c1, c2, c3 = st.columns(3)
        c1.metric("ثقة المحرك", f"{res['confidence']}%")
        c2.metric("بصمة المؤسسات", "إيجابية ✅" if res['fvg'] == 1 else "سلبية ❌" if res['fvg'] == -1 else "هادئة")
        
        # تنبيه الفوليوم
        vol_status = "مرتفع 🔥" if res['vol_ratio'] > 1.5 else "طبيعي ⚖️"
        c3.metric("حجم التداول", vol_status)

        st.write("---")

        # تقرير المحلل الفني
        st.subheader("🖋️ تقرير المحلل الفني المستقل")
        
        # تحديد الرأي بناءً على السعر والفوليوم
        if res['confidence'] >= 65 and res['price'] <= res['entry']:
            if res['vol_ratio'] > 1.1:
                stance, msg = "🔵 شراء هجومي (Strong Accumulation)", "السعر في منطقة خصم مثالية مع زيادة ملحوظة في أحجام التداول، مما يؤكد دخول أموال ذكية (SMC) في هذه المستويات."
            else:
                stance, msg = "🔵 شراء هادئ (Accumulation)", "السعر في منطقة شراء جيدة، لكن أحجام التداول ما زالت ضعيفة. يفضل الدخول على دفعات."
        elif res['rsi'] > 75:
            stance, msg = "🔴 تخفيف / جني أرباح", "السهم متضخم سعرياً (Overbought). ننصح بتأمين الأرباح وانتظار تصحيح لمناطق السيولة الرئيسية."
        else:
            stance, msg = "🟡 انتظار (Hold/Neutral)", "البيانات الحالية لا تظهر دافعاً قوياً للتحرك. نراقب منطقة الـ FVG القادمة لتحديد الاتجاه."

        st.markdown(f"#### **القرار:** {stance}")
        st.info(msg)

        # التوصية السعرية
        st.markdown("### **🎯 خريطة الأهداف:**")
        st_col1, st_col2, st_col3 = st.columns(3)
        st_col1.success(f"📍 الدخول: {res['entry']:.2f}")
        st_col2.info(f"🚀 الهدف: {res['target']:.2f}")
        st_col3.error(f"🛡️ الوقف: {res['stop']:.2f}")

    else:
        st.error(f"خطأ: {res.get('error')}")

st.caption("تنبيه: يتم تحديث البيانات بناءً على أحدث إغلاق متوفر بالمواقع العالمية لضمان استقرار التحليل الاستراتيجي.")
