import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Database va models
from config.database import get_db, engine, Base
from models.user import User, Listing

# Handlers
from handlers.start import start_handler, show_main_menu
from handlers.listing import listing_conversation

# Utils
from utils.error_handler import error_handler
from utils.monitoring import monitor_performance
from utils.rate_limiter import rate_limit
from utils.cache import cache

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

async def post_init(application):
    logger.info("🤖 UyizlangBot ishga tushdi!")
    
    admin_id = int(os.getenv('ADMIN_ID'))
    await application.bot.send_message(
        chat_id=admin_id, 
        text="🎉 Bot ishga tushdi! /start buyrug'i orqali statistikani ko'rishingiz mumkin."
    )

@error_handler
@monitor_performance
async def show_my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Rate limit tekshirish
    if not rate_limit(update.effective_user.id):
        await update.message.reply_text("🚫 Juda ko'p so'rov! Iltimos, biroz kuting.")
        return
    
    db = next(get_db())
    
    try:
        # Foydalanuvchini topamiz
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz!")
            await show_main_menu(update, context)
            return
        
        # Foydalanuvchining e'lonlarini olamiz
        listings = db.query(Listing).filter(Listing.user_id == user.id).order_by(Listing.created_at.desc()).all()
        
        if not listings:
            await update.message.reply_text("📭 Sizda hali e'lonlar mavjud emas.")
            await show_main_menu(update, context)
            return
        
        await update.message.reply_text(f"📋 Sizning e'lonlaringiz ({len(listings)} ta):")
        
        # Har bir e'lonni alohida ko'rsatamiz
        for listing in listings:
            images = json.loads(listing.images) if listing.images else []
            
            listing_info = (
                f"📋 **E'lon #{listing.id}**\n\n"
                f"👤 **Egasi:** {listing.phone}\n"
                f"📞 **Tel:** {listing.phone}\n\n"
                f"📝 **{listing.title}**\n"
                f"📄 **{listing.description}**\n"
                f"🏠 **{listing.rooms} xonali**\n"
                f"🏢 **{listing.floor}/{listing.total_floors} qavat**\n"
                f"💰 **{listing.price} {listing.currency}**\n"
                f"📍 **{listing.location}**\n"
                f"🕒 **Joylangan:** {listing.created_at.strftime('%d.%m.%Y')}\n"
                f"⏳ **Qolgan vaqt:** {(listing.expires_at - listing.created_at).days} kun\n"
                f"✅ **Holati:** {'Aktiv' if listing.is_active else 'Nofaol'}"
            )
            
            if images:
                try:
                    media_group = []
                    for i, image_file_id in enumerate(images[:5]):
                        if i == 0:
                            media_group.append({
                                "type": "photo", 
                                "media": image_file_id,
                                "caption": listing_info,
                                "parse_mode": "Markdown"
                            })
                        else:
                            media_group.append({
                                "type": "photo", 
                                "media": image_file_id
                            })
                    
                    await update.message.reply_media_group(media=media_group)
                    
                except Exception as e:
                    await update.message.reply_text(listing_info, parse_mode="Markdown")
                    for image_file_id in images[:3]:
                        try:
                            await update.message.reply_photo(photo=image_file_id)
                        except:
                            continue
            else:
                await update.message.reply_text(listing_info, parse_mode="Markdown")
            
            await update.message.reply_text("─" * 30)
    
    except Exception as e:
        logger.error(f"Error in show_my_listings: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    
    finally:
        db.close()
    
    await update.message.reply_text(
        "🔍 Barcha e'lonlarni ko'rish uchun web sahifamizga kiring:\n"
        "http://uyizlang.uz/\n\n"
        "🏡 Asosiy menyuga qaytish uchun /start ni bosing"
    )

@error_handler
@monitor_performance
async def show_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not rate_limit(update.effective_user.id):
        await update.message.reply_text("🚫 Juda ko'p so'rov! Iltimos, biroz kuting.")
        return
    
    search_text = (
        "🔍 **Uylarni Xaritada Ko'ring**\n\n"
        "Quyidagi havola orqali barcha uylarni interaktiv xaritada ko'rishingiz mumkin:\n\n"
        "**Xarita xususiyatlar:**\n"
        "• 🗺️ Barcha uylarni ko'rish\n"
        "• 📍 Joylashuvingizni aniqlash\n"
        "• 🔴 Yangi e'lonlar (24 soat)\n"
        "• 🔵 Eski e'lonlar\n"
        "• 🟡 Yaqin atrofdagilar\n"
        "• 📞 To'g'ridan-to'g'ri bog'lanish\n"
        "• 🖼️ Uy rasmlarini ko'rish\n\n"
        "Xaritadan foydalanish uchun quyidagi tugmani bosing!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗺️ Xaritani Ochish", 
         url="https://rasulovmuhiddin4-bit.github.io/uyizlang-map/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        search_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

@error_handler
async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_text = (
        "🆘 Qo'llab-quvvatlash\n\n"
        "Agar sizda savollar bo'lsa yoki yordam kerak bo'lsa, "
        "quyidagi ma'lumotlar orqali admin bilan bog'lanishingiz mumkin:\n\n"
        "💳 Bank karta: 8600 1104 7759 4067\n"
        "📞 Telefon: +998(88)0445550\n"
        "👤 Telegram: @Uyizlang_admin1985\n\n"
        "⏰ Ish vaqti: 09:00 - 18:00\n"
        "📧 E-mail: info@uyizlang.uz\n\n"
        "Biz sizga yordam berishdan mamnunmiz! 😊"
    )
    await update.message.reply_text(support_text)

@error_handler
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != int(os.getenv('ADMIN_ID')):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    db = next(get_db())
    try:
        total_users = db.query(User).count()
        total_listings = db.query(Listing).count()
        active_listings = db.query(Listing).filter(Listing.is_active == True).count()
        
        stats_text = (
            "📊 Bot Statistikasi:\n\n"
            f"👥 Jami foydalanuvchilar: {total_users}\n"
            f"🏠 Jami e'lonlar: {total_listings}\n"
            f"✅ Faol e'lonlar: {active_listings}"
        )
        
        await update.message.reply_text(stats_text)
    finally:
        db.close()

def main():
    load_dotenv()
    
    application = Application.builder().token(os.getenv('BOT_TOKEN')).post_init(post_init).build()

    # Add handlers
    application.add_handler(start_handler)
    application.add_handler(listing_conversation)
    
    # Menu handlers
    application.add_handler(MessageHandler(filters.Regex("^📋 Mening elonlarim$"), show_my_listings))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Qidiruv$"), show_search))
    application.add_handler(MessageHandler(filters.Regex("^🆘 Qo'llab-quvvatlash$"), show_support))
    
    # Admin command
    application.add_handler(CommandHandler("stats", admin_stats))
    
    # Global error handler
    application.add_error_handler(error_handler)
    
    # Start bot with optimizations
    application.run_polling(
        poll_interval=1.0,
        timeout=30,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()