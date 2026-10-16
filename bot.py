
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from supabase import create_client

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OWNER_ID = 1716120370

db = create_client(SUPABASE_URL, SUPABASE_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    name = user.full_name or "Фойдаланувчи"

    if telegram_id == OWNER_ID:
        try:
            db.table("bot_users").upsert({
                "telegram_id": telegram_id,
                "name": name,
                "role": "owner",
                "approved": True,
            }, on_conflict="telegram_id").execute()
        except Exception:
            logging.exception("Owner registration failed")

        await update.message.reply_text(
            "🎮 C1 ZONA Manager\n\n"
            "Салом, бошлиқ!\n"
            "/rooms — хоналарни кўриш"
        )
        return

    try:
        result = db.table("bot_users").select(
            "approved"
        ).eq("telegram_id", telegram_id).execute()

        if result.data and result.data[0].get("approved"):
            await update.message.reply_text(
                "🎮 C1 ZONA Manager\n\n"
                "Рухсат берилган.\n"
                "/rooms — хоналарни кўриш"
            )
        else:
            db.table("bot_users").upsert({
                "telegram_id": telegram_id,
                "name": name,
                "role": "employee",
                "approved": False,
            }, on_conflict="telegram_id").execute()

            await update.message.reply_text(
                "⏳ Кириш сўровингиз сақланди.\n"
                "Бошлиқ рухсат бериши керак."
            )
    except Exception:
        logging.exception("Start failed")
        await update.message.reply_text(
            "Базага уланишда хатолик юз берди. "
            "Созламаларни текшириш керак."
        )


async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        if user_id != OWNER_ID:
            result = db.table("bot_users").select(
                "approved"
            ).eq("telegram_id", user_id).execute()

            if not result.data or not result.data[0].get("approved"):
                await update.message.reply_text(
                    "Аввал бошлиқдан рухсат олинг."
                )
                return

        result = db.table("rooms").select(
            "name,console_type,hourly_rate,active"
        ).eq("active", True).order("name").execute()

        if not result.data:
            await update.message.reply_text("Ҳозирча хоналар йўқ.")
            return

        lines = ["🎮 C1 ZONA — Хоналар", ""]
        for room in result.data:
            lines.append(
                f"🏠 {room['name']}\n"
                f"🎮 {room['console_type']}\n"
                f"💰 {room['hourly_rate']:,} сўм/соат"
            )

        await update.message.reply_text("\n\n".join(lines))

    except Exception:
        logging.exception("Rooms failed")
        await update.message.reply_text(
            "Хоналарни олишда хатолик юз берди."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rooms", rooms))
    app.run_polling()


if __name__ == "__main__":
    main()
