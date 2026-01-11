import telebot
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.ensemble import RandomForestClassifier
import os
import logging

# إعداد نظام تسجيل الأخطاء لسهولة المراقبة على السيرفر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب التوكن من الإعدادات السرية (Secrets)
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("خطأ: لم يتم العثور على BOT_TOKEN في إعدادات البيئة!")

bot = telebot.TeleBot(TOKEN)
CALC_FACTOR = 27 

def generate_ai_report(ticker):
    try:
        symbol = f"{ticker.upper().strip()}.CA"
        # جلب بيانات كافية للتحليل (150 يوم بفاصل 4 ساعات)
        df = yf.download(symbol, period="150d", interval="4h", progress=False)
        
        # تصحيح تنسيق الجداول في حال وجود MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < CALC_FACTOR:
            return {"error": "بيانات غير كافية أو رمز سهم خاطئ."}

        # --- [1] بصمة المؤسسات (Fair Value Gap) ---
        df['FVG'] = np.where(df['Low'] > df['High'].shift(2), 1, 0)

        # --- [2] التحليل الفني الرقمي ---
        df.ta.macd(append=True)
        macd_col = [c for c in df.columns if 'MACDh' in c][0]

        # --- [3] مستويات فيبوناتشي (منطقة الخصم) ---
        hi, lo = float(df['High'].max()), float(df['Low'].min())
        curr_p = float(df['Close'].iloc[-1])
        fib_618 = hi - (0.618 * (hi - lo))

        # --- [4] محرك التنبؤ (Random Forest) ---
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        clean_df = df.dropna()
        
        X = clean_df[[macd_col, 'FVG']]
        y = clean_df['Target']
        
        model = RandomForestClassifier(n_estimators=CALC_FACTOR, random_state=42)
        model.fit(X[:-1], y[:-1])
        
        prob = model.predict_proba(X.iloc[[-1]])[0][1]
        power = round(prob * 100, 1)

        # --- [5] تحديد التوصية النهائية ---
        if power >= 65 and curr_p <= fib_618:
            status, color = "🟢 شراء قوي (Strong Buy)", "دخول سيولة مؤسسية وسعر مغري"
        elif power >= 50:
            status, color = "🟡 مراقبة (Wait/Watch)", "منطقة حيرة، انتظر تأكيد السيولة"
        else:
            status, color = "🔴 تجنب/بيع (Avoid/Sell)", "ضعف في الزخم وضغط بيعي محتمل"

        return {
            "symbol": symbol, "price": curr_p, "power": power,
            "fib": fib_618, "fvg": "نشطة ✅" if df['FVG'].iloc[-1] == 1 else "غير متوفرة",
            "decision": status, "reason": color
        }
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(m):
    bot.reply_to(m, "👋 أهلاً بك في رادار البورصة المصرية الذكي!\nأرسل رمز السهم (مثال: COMI) للحصول على تحليل فوري.")

@bot.message_handler(func=lambda m: True)
def handle_stock(m):
    bot.send_chat_action(m.chat.id, 'typing')
    res = generate_ai_report(m.text)

    if res and "error" not in res:
        msg = (
            f"📊 **تحليل السهم: {res['symbol']}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 السعر الحالي: `{res['price']:.2f}`\n"
            f"🎯 هدف الخصم (0.618): `{res['fib']:.2f}`\n"
            f"🌊 سيولة المؤسسات: `{res['fvg']}`\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **قوة التنبؤ الذكي:** `{res['power']}%`\n"
            f"💡 التفسير: _{res['reason']}_\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏁 **القرار:** {res['decision']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ *مبني على المعامل الرقمي 27*"
        )
        bot.reply_to(m, msg, parse_mode="Markdown")
    else:
        bot.reply_to(m, "❌ تعذر التحليل. تأكد من الكود (مثال: EAST, fawry) أو جرب لاحقاً.")

if __name__ == "__main__":
    logger.info("البوت بدأ العمل الآن...")
    bot.infinity_polling()
