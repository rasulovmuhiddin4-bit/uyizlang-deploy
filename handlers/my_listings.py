import json
from telegram import Update
from telegram.ext import ContextTypes
from config.database import get_db
from models.user import User, Listing
from handlers.start import show_main_menu
from utils.cache import cache
from utils.rate_limiter import rate_limit
from utils.error_handler import error_handler
from utils.monitoring import monitor_performance
import logging

logger = logging.getLogger(__name__)

@cache(ttl=60)  # 1 daqiqa cache
def get_user_listings(user_id):
    """Cache bilan user listings"""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return []
        
        listings = db.query(Listing).filter(
            Listing.user_id == user.id, 
            Listing.is_active == True
        ).order_by(Listing.created_at.desc()).all()
        
        return listings
    except Exception as e:
        logger.error(f"Error in get_user_listings: {e}")
        return []
    finally:
        db.close()

@error_handler
@monitor_performance
async def show_my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Rate limit tekshirish
    if not rate_limit(update.effective_user.id):
        await update.message.reply_text("🚫 Juda ko'p so'rov! Iltimos, biroz kuting.")
        return
    
    try:
        # Cache'dan foydalanib e'lonlarni olamiz
        listings = get_user_listings(update.effective_user.id)
        
        if not listings:
            await update.message.reply_text("📭 Sizda hali e'lonlar mavjud emas.")
            await show_main_menu(update, context)
            return
        
        await update.message.reply_text(f"📋 Sizning e'lonlaringiz ({len(listings)} ta):")
        
        # Batch processing - 3 tadan bo'lib yuborish
        batch_size = 3
        for i in range(0, len(listings), batch_size):
            batch = listings[i:i + batch_size]
            
            for listing in batch:
                # Rasmlarni olamiz
                images = json.loads(listing.images) if listing.images else []
                
                # E'lon ma'lumotlari
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
                
                # Agar rasmlar mavjud bo'lsa, ularni yuboramiz
                if images:
                    try:
                        # Birinchi 5 ta rasmni yuboramiz (Telegram limiti)
                        media_group = []
                        for i, image_file_id in enumerate(images[:5]):
                            if i == 0:
                                # Birinchi rasmga caption qo'shamiz
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
                        
                        # Agar rasmlar 5 tadan ko'p bo'lsa
                        if len(images) > 5:
                            await update.message.reply_text(f"🖼️ ...va yana {len(images) - 5} ta rasm")
                            
                    except Exception as e:
                        logger.warning(f"Media group error, falling back to simple method: {e}")
                        # Agar media group bilan muammo bo'lsa, oddiy tarzda yuboramiz
                        await update.message.reply_text(listing_info, parse_mode="Markdown")
                        for image_file_id in images[:3]:  # Faqat birinchi 3 ta rasm
                            try:
                                await update.message.reply_photo(photo=image_file_id)
                            except Exception as photo_error:
                                logger.warning(f"Photo send error: {photo_error}")
                                continue
                else:
                    # Rasmlar bo'lmasa, faqat matnni yuboramiz
                    await update.message.reply_text(listing_info, parse_mode="Markdown")
                
                # Har bir e'lon orasida bo'sh joy (faqat birinchi batchda)
                if i == 0:
                    await update.message.reply_text("─" * 30)
            
            # Batchlar orasida kichik kutish (flood prevention)
            if i + batch_size < len(listings):
                import asyncio
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Error in show_my_listings: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    
    finally:
        # Yakuniy xabar
        await update.message.reply_text(
            "🔍 Barcha e'lonlarni ko'rish uchun web sahifamizga kiring:\n"
            "http://uyizlang.uz/\n\n"
            "🏡 Asosiy menyuga qaytish uchun /start ni bosing"
        )