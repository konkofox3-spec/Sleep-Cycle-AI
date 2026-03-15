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


# -------- TIME EXTRACT --------

def extract_time(text):

    match = re.search(r"(\d{1,2}):(\d{2})", text)

    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"(\d{1,2})\s*h", text)

    if match:
        return int(match.group(1)), 0

    return None


def detect_sleep(text):

    keywords = ["ngủ", "sleep", "bed"]

    for k in keywords:
        if k in text.lower():
            return True

    return False


def detect_wake(text):

    keywords = ["dậy", "wake", "thức"]

    for k in keywords:
        if k in text.lower():
            return True

    return False


# -------- CALCULATE --------

def calculate_sleep_times(wake_time):

    cycles = [6, 5, 4]

    results = []

    for c in cycles:

        sleep_time = wake_time - timedelta(minutes=(90 * c + 15))

        results.append((sleep_time.strftime("%H:%M"), c))

    return results


def calculate_wake_times(sleep_time):

    cycles = [4, 5, 6]

    sleep_start = sleep_time + timedelta(minutes=15)

    results = []

    for c in cycles:

        wake = sleep_start + timedelta(minutes=90 * c)

        results.append((wake.strftime("%H:%M"), c))

    return results


# -------- FORMAT MESSAGE --------

def format_sleep_message(wake_time):

    results = calculate_sleep_times(wake_time)

    msg = f"🌅 Nếu bạn muốn dậy lúc {wake_time.strftime('%H:%M')}, bạn nên ngủ:\n\n"

    for time, cycle in results:

        if cycle == 6:
            msg += f"🛌 {time} → 9h (6 chu kỳ) ⭐ tốt nhất\n"

        elif cycle == 5:
            msg += f"🛌 {time} → 7.5h (5 chu kỳ)\n"

        else:
            msg += f"🛌 {time} → 6h (4 chu kỳ)\n"

    msg += (
        "\n\n💡 Nếu ngủ khoảng 6h:\n"
        "• Ngủ trưa 15–25 phút (12h–14h)\n"
        "• Không ngủ quá 30 phút\n"
        "• Coffee nap ☕ có thể giúp tỉnh táo"
    )

    return msg


def format_wake_message(sleep_time):

    results = calculate_wake_times(sleep_time)

    msg = f"🌙 Nếu bạn ngủ lúc {sleep_time.strftime('%H:%M')}, bạn nên dậy:\n\n"

    for time, cycle in results:

        if cycle == 6:
            msg += f"⏰ {time} → 9h (6 chu kỳ) ⭐ ngủ sâu\n"

        elif cycle == 5:
            msg += f"⏰ {time} → 7.5h (5 chu kỳ)\n"

        else:
            msg += f"⏰ {time} → 6h (4 chu kỳ)\n"

    bed_time = sleep_time - timedelta(minutes=15)

    msg += f"\n🛏 Bạn nên lên giường khoảng {bed_time.strftime('%H:%M')}"
    msg += "\n(vì cần ~15 phút để ngủ thiếp)"

    return msg


# -------- COMMANDS --------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "😴 *Sleep Cycle AI*\n\n"
        "Gửi giờ như:\n"
        "`07:30`\n\n"
        "Hoặc nói tự nhiên:\n"
        "• tôi muốn dậy 7:30\n"
        "• ngủ lúc 23:30\n\n"
        "Bot sẽ tính chu kỳ ngủ tối ưu."
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "📘 *Cách dùng*\n\n"
        "1️⃣ Gửi giờ\n"
        "`07:30`\n\n"
        "2️⃣ Bot sẽ hỏi:\n"
        "🌙 ngủ hay 🌅 dậy\n\n"
        "3️⃣ Ví dụ:\n"
        "`ngủ 23:30`\n"
        "`dậy 7:30`"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


# -------- MESSAGE --------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    time_data = extract_time(text)

    if not time_data:

        await update.message.reply_text(
            "❓ Gửi giờ như `07:30`",
            parse_mode="Markdown"
        )

        return

    hour, minute = time_data

    time_obj = datetime.now().replace(hour=hour, minute=minute, second=0)

    # nếu user nói ngủ
    if detect_sleep(text):

        msg = format_wake_message(time_obj)

        await update.message.reply_text(msg)

        return

    # nếu user nói dậy
    if detect_wake(text):

        msg = format_sleep_message(time_obj)

        await update.message.reply_text(msg)

        return

    # nếu mơ hồ thì dùng button
    context.user_data["time_input"] = (hour, minute)

    keyboard = [
        [
            InlineKeyboardButton("🌙 Ngủ", callback_data="sleep"),
            InlineKeyboardButton("🌅 Dậy", callback_data="wake"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⏰ {hour:02d}:{minute:02d} là:",
        reply_markup=reply_markup
    )


# -------- BUTTON --------

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


# -------- APP --------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
