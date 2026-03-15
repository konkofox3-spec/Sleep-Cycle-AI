import os
import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]


def calculate_sleep_times(wake_time):
    cycles = [6, 5, 4]
    results = []

    for c in cycles:
        sleep_time = wake_time - timedelta(minutes=(90 * c + 15))
        results.append((sleep_time.strftime("%H:%M"), c))

    return results


def format_sleep_message(wake_time):
    results = calculate_sleep_times(wake_time)

    msg = f"⏰ Nếu bạn muốn dậy lúc {wake_time.strftime('%H:%M')}, bạn nên đi ngủ vào:\n\n"

    for time, cycle in results:
        if cycle == 6:
            msg += f"🛌 {time} → 6 chu kỳ (9h) — tốt nhất\n"
        elif cycle == 5:
            msg += f"🛌 {time} → 5 chu kỳ (7.5h)\n"
        else:
            msg += f"🛌 {time} → 4 chu kỳ (6h)\n"

    msg += "\n⏳ Hãy lên giường sớm hơn khoảng 15 phút để có thời gian ngủ thiếp đi."

    return msg


def extract_time(text):
    text = text.lower()

    # 07:30
    match = re.search(r"(\d{1,2}):(\d{2})", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return hour, minute

    # 6h hoặc 6 h
    match = re.search(r"(\d{1,2})\s*h", text)
    if match:
        hour = int(match.group(1))
        return hour, 0

    # wake up 08
    match = re.search(r"wake.*?(\d{1,2})", text)
    if match:
        hour = int(match.group(1))
        return hour, 0

    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "😴 *Sleep Cycle AI*\n\n"
        "Tôi giúp bạn tính giờ đi ngủ tối ưu.\n\n"
        "Bạn có thể:\n"
        "• Gửi giờ: `07:30`\n"
        "• Hoặc nói tự nhiên:\n"
        "  - tôi muốn dậy lúc 7:30\n"
        "  - mai dậy 6h\n"
        "  - wake up 08:15\n\n"
        "Commands:\n"
        "/sleep 07:30\n"
        "/now\n"
        "/help"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📘 *Hướng dẫn sử dụng*\n\n"
        "Bạn có thể dùng bot theo các cách sau:\n\n"
        "1️⃣ Nhập giờ thức dậy:\n"
        "`07:30`\n\n"
        "2️⃣ Dùng lệnh:\n"
        "`/sleep 07:30`\n\n"
        "3️⃣ Nói tự nhiên:\n"
        "• tôi muốn dậy lúc 7:30\n"
        "• mai dậy 6h\n"
        "• wake up 08:15\n\n"
        "4️⃣ Nếu ngủ ngay bây giờ:\n"
        "`/now`"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Hãy nhập giờ dạng: /sleep 07:30")
        return

    try:
        wake = datetime.strptime(context.args[0], "%H:%M")
        msg = format_sleep_message(wake)
        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("Giờ không hợp lệ. Ví dụ: /sleep 07:30")



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    time_data = extract_time(text)

    if time_data:
        hour, minute = time_data
        wake = datetime.now().replace(hour=hour, minute=minute, second=0)

        msg = format_sleep_message(wake)

        await update.message.reply_text(msg)
        return

    await update.message.reply_text(
        "❓ Tôi không hiểu.\n\nGửi giờ như `07:30` hoặc dùng `/help`."
    )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("sleep", sleep_command))


app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
