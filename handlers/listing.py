from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from datetime import datetime, timedelta
import json
from config.database import SessionLocal
from models.user import User, Listing
from handlers.start import show_main_menu

# Listing conversation states
TITLE, ROOMS, FLOOR, TOTAL_FLOORS, PRICE, CURRENCY, IMAGES, LOCATION, CONFIRM = range(9)

async def start_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Elon berish\n\nSarlavha Qisqacha\nMasalan Olmazor tumanida Kvartira yoki Xovli Sotiladi..?",
        reply_markup=ReplyKeyboardRemove()
    )
    return TITLE

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    
    # Create room buttons
    rooms_keyboard = [[str(i)] for i in range(1, 11)]
    reply_markup = ReplyKeyboardMarkup(rooms_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Xonalar soni kiriting\n1dan 10tagacha",
        reply_markup=reply_markup
    )
    return ROOMS

async def handle_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rooms'] = int(update.message.text)
    
    # Create floor buttons
    floor_keyboard = [[str(i)] for i in range(1, 23)]
    reply_markup = ReplyKeyboardMarkup(floor_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🏠 Xonadon Joylash qavat\n1dan 22gacha",
        reply_markup=reply_markup
    )
    return FLOOR

async def handle_floor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['floor'] = int(update.message.text)
    
    # Create total floors buttons
    total_floors_keyboard = [[str(i)] for i in range(1, 23)]
    reply_markup = ReplyKeyboardMarkup(total_floors_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🏢 Jami qavatlar 1dan 22gacha",
        reply_markup=reply_markup
    )
    return TOTAL_FLOORS

async def handle_total_floors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['total_floors'] = int(update.message.text)
    
    await update.message.reply_text(
        "💰 Narxni kiriting:\n\n"
        "ℹ️ Faqat raqamlarda kiriting",
        reply_markup=ReplyKeyboardRemove()
    )
    return PRICE

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['price'] = price
        
        currency_keyboard = [["USD", "SO'M"]]
        reply_markup = ReplyKeyboardMarkup(currency_keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "💵 Valyutani tanlang: USD SO'M",
            reply_markup=reply_markup
        )
        return CURRENCY
    except ValueError:
        await update.message.reply_text("❌ Iltimos, faqat raqamlarda kiriting!")
        return PRICE

async def handle_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['currency'] = update.message.text
    context.user_data['images'] = []
    
    await update.message.reply_text(
        "🖼️ Rasm yuklang (maksimum 6 ta)\n\n"
        "ℹ️ Bir nechta rasm yuklash uchun bir vaqtning o'zida bir nechtasini tanlang",
        reply_markup=ReplyKeyboardRemove()
    )
    return IMAGES

async def handle_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1]
        context.user_data['images'].append(photo.file_id)
        
        remaining = 6 - len(context.user_data['images'])
        
        if remaining > 0:
            await update.message.reply_text(
                f"✅ Rasm qo'shildi. Yana {remaining} ta rasm yuklashingiz mumkin."
            )
            return IMAGES
        else:
            await update.message.reply_text("✅ Barcha 6 ta rasm muvaffaqiyatli yuklandi!")
            
            # Request location for listing
            await update.message.reply_text(
                "📍 E'lon joylashuvini yuboring:",
                reply_markup=ReplyKeyboardMarkup(
                    [[{"text": "📍 Joylashuvni yuborish", "request_location": True}]],
                    one_time_keyboard=True,
                    resize_keyboard=True
                )
            )
            return LOCATION
    else:
        await update.message.reply_text("❌ Iltimos, rasm yuboring!")
        return IMAGES

async def handle_location_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        location = f"{update.message.location.latitude}, {update.message.location.longitude}"
    else:
        location = update.message.text
    
    context.user_data['location'] = location
    
    # Get user phone from database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        context.user_data['phone'] = user.phone
        
        # Show confirmation
        description = context.user_data.get('description', "Holati zo'r Hamma sharoitlar bor")
        
        listing_info = "📋 E'lon ma'lumotlari:\n\n"
        listing_info += f"📝 Sarlavha: {context.user_data['title']}\n"
        listing_info += f"📄 Tavsif: {description}\n"
        listing_info += f"🏠 Xonalar: {context.user_data['rooms']} ta\n"
        listing_info += f"🏢 Qavat: {context.user_data['floor']}/{context.user_data['total_floors']}\n"
        listing_info += f"💰 Narx: {context.user_data['price']} {context.user_data['currency']}\n"
        listing_info += f"🖼️ Rasmlar: {len(context.user_data['images'])} ta\n"
        listing_info += f"📞 Telefon raqamingiz {context.user_data['phone']}\n\n"
        listing_info += "⚠️ Ogohlantirish:\n\n"
        listing_info += "E'loningiz 30 kundan keyin avtomatik ravishda nofaol holatga o'tadi\n\n"
        listing_info += "E'loni tasdiqlaysizmi?"
        
        keyboard = [["✅ Tasdiqlash", "❌ Bekor qilish"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(listing_info, reply_markup=reply_markup)
        return CONFIRM
    finally:
        db.close()

async def confirm_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "✅ Tasdiqlash":
        # Save listing to database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
            
            listing = Listing(
                user_id=user.id,
                title=context.user_data['title'],
                description=context.user_data.get('description', "Holati zo'r Hamma sharoitlar bor"),
                rooms=context.user_data['rooms'],
                floor=context.user_data['floor'],
                total_floors=context.user_data['total_floors'],
                price=context.user_data['price'],
                currency=context.user_data['currency'],
                images=json.dumps(context.user_data['images']),
                location=context.user_data['location'],
                phone=context.user_data['phone'],
                expires_at=datetime.now() + timedelta(days=30)
            )
            
            db.add(listing)
            db.commit()
            
            # Send success message
            await update.message.reply_text(
                "🎉 E'loningiz muvaffaqiyatli joylashtirildi!\n\n"
                "⚠️ Ogohlantirish:\n\n"
                "E'loningiz 30 kundan keyin avtomatik ravishda nofaol holatga o'tadi\n\n"
                "📋 E'loningizni 'Mening elonlarim' bo'limida ko'rishingiz mumkin!",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Show listing details with all images in one media group
            listing_details = (
                "🖼️ **E'lon rasmlari bilan**\n\n"
                f"📋 **E'lon #{listing.id}**\n"
                f"👤 **Egasi:** {user.phone}\n"
                f"📞 **Tel:** {listing.phone}\n\n"
                f"📝 **{listing.title}**\n"
                f"📄 **{listing.description}**\n"
                f"🏠 **{listing.rooms} xonali**\n"
                f"🏢 **{listing.floor}/{listing.total_floors} qavat**\n"
                f"💰 **{listing.price} {listing.currency}**\n"
                f"📍 **{listing.location}**\n"
                f"🕒 **Joylangan:** {listing.created_at.strftime('%d.%m.%Y')}\n"
                f"⏳ **Qolgan vaqt:** 30 kun\n\n"
                "🔍 Barcha e'lonlarni ko'rish uchun web sahifamizga kiring:\n"
                "http://uyizlang.uz/"
            )
            
            # Send all images in one media group (bir ramka ichida)
            images = json.loads(listing.images)
            if images:
                try:
                    # Barcha rasmlarni bir media groupda yuboramiz
                    media_group = []
                    for i, image_file_id in enumerate(images[:10]):  # Telegram limiti 10 ta rasm
                        if i == 0:
                            # Birinchi rasmga caption qo'shamiz
                            media_group.append({
                                "type": "photo", 
                                "media": image_file_id,
                                "caption": listing_details,
                                "parse_mode": "Markdown"
                            })
                        else:
                            media_group.append({
                                "type": "photo", 
                                "media": image_file_id
                            })
                    
                    await update.message.reply_media_group(media=media_group)
                except Exception as e:
                    # Agar media group bilan muammo bo'lsa, oddiy tarzda yuboramiz
                    await update.message.reply_text(listing_details, parse_mode="Markdown")
                    for image_file_id in images[:5]:
                        try:
                            await update.message.reply_photo(photo=image_file_id)
                        except:
                            continue
            else:
                await update.message.reply_text(listing_details, parse_mode="Markdown")
            
            await show_main_menu(update, context)
            
        finally:
            db.close()
        
    else:
        await update.message.reply_text(
            "❌ E'lon bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_main_menu(update, context)
    
    return ConversationHandler.END

# Listing conversation handler
listing_conversation = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^🏠 Elon Berish$"), start_listing)],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)],
        ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rooms)],
        FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_floor)],
        TOTAL_FLOORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_total_floors)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
        CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency)],
        IMAGES: [MessageHandler(filters.PHOTO, handle_images)],
        LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, handle_location_listing)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_listing)],
    },
    fallbacks=[],
)