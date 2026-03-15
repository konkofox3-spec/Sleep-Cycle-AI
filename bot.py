import os
import re
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]


# --------- TIME EXTRACTION ---------

def extract_time(text):

    text = text.lower()

    match = re.search(r"(\d{1,2}):(\d{2})", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"(\d{1,2})\s*h", text)
    if match:
        return int(match.group(1)), 0

    return None


# --------- CALCULATE SLEEP ---------

def calculate_sleep_times(wake_time):

    cycles = [6, 5, 4]
    results = []

    for c in cycles:

        sleep_time = wake_time - timedelta(minutes=(90 * c + 15))

        results.append((sleep_time.strftime("%H:%M"), c))

    return results


def calculate_wake_times(sleep_time):

    cycles = [4, 5, 6]
    results = []

    sleep_start = sleep_time + timedelta(minutes=15)

    for c in cycles:

        wake = sleep_start + timedelta(minutes=90 * c)

        results.append((wake.strftime("%H:%M"), c))

    return results


# --------- FORMAT MESSAGE ---------

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

    bed_time = wake_time - timedelta(minutes=15)

    msg += f"\n🛏 Nên lên giường lúc khoảng {bed_time.strftime('%H:%M')}"
    msg += "\n(vì cơ thể cần ~15 phút để ngủ thiếp)"

    msg += (
        "\n\n💡 Nếu bạn chỉ ngủ khoảng 6 tiếng:\n"
        "• Ngủ trưa 15–25 phút vào khoảng 12h–14h\n"
        "• Tránh ngủ trưa quá 30 phút\n"
        "• Có thể thử coffee nap ☕"
    )

    return msg


def format_wake_message(sleep_time):

    results = calculate_wake_times(sleep_time)

    msg = f"🛌 Nếu bạn ngủ lúc {sleep_time.strftime('%H:%M')}, bạn nên dậy lúc:\n\n"

    for time, cycle in results:

        if cycle == 6:
            msg += f"⏰ {time} → 6 chu kỳ (9h) — ngủ sâu\n"

        elif cycle == 5:
            msg += f"⏰ {time} → 5 chu kỳ (7.5h)\n"

        else:
            msg += f"⏰ {time} → 4 chu kỳ (6h)\n"

    msg += "\n⏳ Đã tính thêm ~15 phút để ngủ thiếp."

    return msg


# --------- COMMANDS ---------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "😴 *Sleep Cycle AI*\n\n"
        "Tôi giúp bạn tối ưu thời gian ngủ.\n\n"
        "Bạn có thể:\n"
        "• Gửi giờ như `07:30`\n"
        "• Hoặc nói tự nhiên:\n"
        "  - tôi muốn dậy lúc 7:30\n"
        "  - mai dậy 6h\n"
        "  - ngủ lúc 23:30\n\n"
        "Bot sẽ hỏi đó là:\n"
        "🌅 giờ thức dậy hay 🌙 giờ đi ngủ\n\n"
        "Commands:\n"
        "/sleep 07:30\n"
        "/help"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "📘 *Hướng dẫn*\n\n"
        "1️⃣ Gửi giờ:\n"
        "`07:30`\n\n"
        "2️⃣ Bot sẽ hỏi:\n"
        "🌅 giờ thức dậy\n"
        "🌙 giờ đi ngủ\n\n"
        "3️⃣ Hoặc dùng:\n"
        "`/sleep 07:30`"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Ví dụ: /sleep 07:30")

        return

    try:

        wake = datetime.strptime(context.args[0], "%H:%M")

        msg = format_sleep_message(wake)

        await update.message.reply_text(msg)

    except:

        await update.message.reply_text("Giờ không hợp lệ. Ví dụ: /sleep 07:30")


# --------- HANDLE MESSAGE ---------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    time_data = extract_time(text)

    if not time_data:

        await update.message.reply_text(
            "❓ Tôi không hiểu.\n\nGửi giờ như `07:30` hoặc dùng `/help`.",
            parse_mode="Markdown"
        )

        return

    hour, minute = time_data

    context.user_data["time_input"] = (hour, minute)

    keyboard = [
        [
            InlineKeyboardButton("🌅 Giờ thức dậy", callback_data="wake"),
            InlineKeyboardButton("🌙 Giờ đi ngủ", callback_data="sleep"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⏰ *{hour:02d}:{minute:02d}* là:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# --------- BUTTON HANDLER ---------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    hour, minute = context.user_data["time_input"]

    time_obj = datetime.now().replace(hour=hour, minute=minute, second=0)

    if query.data == "wake":

        msg = format_sleep_message(time_obj)

    else:

        msg = format_wake_message(time_obj)

    await query.edit_message_text(msg)


# --------- APP ---------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("sleep", sleep_command))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
