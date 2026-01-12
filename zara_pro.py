import streamlit as st
import yfinance as yf
import pandas as pd
import os

# إعدادات العرض
DATA_FILE = "zara_egypt_final.csv"
st.set_page_config(page_title="Zara Pro Radar", layout="wide")

st.title("🦅 رادار زارا برو - التحليل اللوني")

# وظيفة لتلوين الجدول
def color_score(val):
    color = '#2ecc71' if val > 70 else '#e74c3c' if val < 30 else '#f1c40f'
    return f'background-color: {color}; color: black; font-weight: bold'

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    
    st.subheader("🎯 الفرص المرتبة حسب القوة الشرائية")
    
    # تطبيق التنسيق اللوني
    styled_df = df.sort_values(by="القوة %", ascending=False).style.applymap(
        color_score, subset=['القوة %']
    )
    
    st.table(styled_df)
    
    st.info("""
    💡 **دليل الألوان:**
    - 🟢 **أخضر (فوق 70%):** فرصة ذهبية (السعر قريب جداً من القاع).
    - 🟡 **أصفر (30-70%):** منطقة تجميع أو انتظار.
    - 🔴 **أحمر (تحت 30%):** سهم متضخم (قريب من القمة)، احذر الشراء هنا.
    """)
else:
    st.warning("البيانات غير موجودة، يرجى تشغيل المسح من النسخة السابقة.")

if st.button("🗑️ مسح وإعادة ضبط"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    st.rerun()
