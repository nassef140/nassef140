import telebot
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import os

# إعدادات البوت - قراءة التوكن من إعدادات الموقع للأمان
TOKEN = os.getenv("BOT_TOKEN") 
bot = telebot.TeleBot(TOKEN)
[span_1](start_span)CALC_FACTOR = 27 # المعامل الرقمي الجسر[span_1](end_span)

def generate_simple_ai_report(ticker):
    try:
        symbol = f"{ticker.upper().strip()}.CA"
        # [span_2](start_span)جلب البيانات لآخر 150 يوم بفاصل 4 ساعات[span_2](end_span)
        df = yf.download(symbol, period="150d", interval="4h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < CALC_FACTOR: 
            [span_3](start_span)return None[span_3](end_span)

        # 1. [span_4](start_span)كشف بصمة المؤسسات (FVG)[span_4](end_span)
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)

        # 2. [span_5](start_span)قياس الزخم (MACD)[span_5](end_span)
        df.ta.macd(append=True)
        macd_h = [c for c in df.columns if 'MACDh' in c][0]

        # 3. [span_6](start_span)حساب مناطق الخصم (Fibonacci)[span_6](end_span)
        hi, lo = float(df['High'].max()), float(df['Low'].min())
        [span_7](start_span)curr_p = float(df['Close'].iloc[-1])[span_7](end_span)
        fib_618 = hi - (0.618 * (hi - lo))

        # 4. [span_8](start_span)محرك الذكاء الاصطناعي (AI Engine)[span_8](end_span)
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        clean_df = df.dropna()
        model = RandomForestClassifier(n_estimators=CALC_FACTOR, random_state=42)
        X = clean_df[[macd_h, 'FVG']]
        y = clean_df['Target']
        model.fit(X[:-1], y[:-1])
     
        [span_9](start_span)ai_prob = model.predict_proba(X.iloc[[-1]])[0][1][span_9](end_span)
        ai_power = round(ai_prob * 100, 1)

        # 5. [span_10](start_span)اتخاذ القرار بناءً على القوة الفنية[span_10](end_span)
        if ai_power >= 65 and curr_p <= fib_618:
            status = "🟢 فرصة شراء قوية"
            explanation = "الذكاء الاصطناعي يرى دخول سيولة مؤسسية كبيرة والسعر حالياً في منطقة رخيصة (Discount Zone)."
        elif ai_power >= 50:
            status = "🟡 مراقبة وانتظار"
            explanation = "السعر في منطقة حيرة، لا توجد سيولة كافية حالياً لتأكيد الانطلاق."
        else:
            status = "🔴 خطر / بيع"
            explanation = "هناك ضعف واضح في القوة الشرائية، والذكاء الاصطناعي يتوقع ضغطاً بيعياً (Distribution)."

        return {
            "name": symbol, "price": curr_p, "power": ai_power,
            "fib": fib_618, "fvg": "موجودة ✅" if df['FVG'].iloc[-1] == 1 else "غير موجودة",
            "decision": status, "explanation": explanation
        [span_11](start_span)}
    except: 
        return None

@bot.message_handler(func=lambda m: True)
def handle_request(m):
    bot.send_chat_action(m.chat.id, 'typing')
    data = generate_simple_ai_report(m.text)

    if data:
        report = (
            f"🧠 **تقرير الذكاء الاصطناعي المبسط**\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
            f"🏢 السهم: `{data['name']}`\n"
            f"💰 السعر الحالي: **{data['price']:.2f}**\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
            f"📊 **نسبة نجاح الصفقة:** `{data['power']}%`\n"
            f"🎯 السعر المثالي (Fibonacci): `{data['fib']:.2f}`\n"
            f"🌊 سيولة المؤسسات (FVG): `{data['fvg']}`\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
            f"💡 **تفسير الحالة:**\n_{data['explanation']}_\n\n"
            f"🏁 **القرار النهائي:**\n**{data['decision']}**\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
            f"⚠️ *مبني على دورة المعامل الرقمي 27*"
        )[span_11](end_span)
        bot.reply_to(m, report, parse_mode="Markdown")
    else:
        # [span_12](start_span)إصلاح الخطأ النصي هنا بإغلاق علامة الاقتباس والقوس بشكل صحيح[span_12](end_span)
        bot.reply_to(m, "❌ عذراً، لم أتمكن من تحليل هذا السهم. تأكد من كود السهم الصحيح.")

if __name__ == "__main__":
    bot.infinity_polling()
