from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import os

TOKEN = os.environ["BOT_TOKEN"]

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        wake = datetime.strptime(text, "%H:%M")
        cycles = [6,5,4]
        msg = "Giờ ngủ gợi ý:\n"

        for c in cycles:
            sleep = wake - timedelta(minutes=90*c+15)
            msg += f"{sleep.strftime('%H:%M')} → {c} chu kỳ\n"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("Nhập giờ dạng HH:MM")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, reply))
app.run_polling()
