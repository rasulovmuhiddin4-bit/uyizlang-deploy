from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from config.database import SessionLocal
from models.user import User

# Conversation states
LANGUAGE, PHONE, LOCATION = range(3)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.telegram_id == user.id).first()
        
        if existing_user:
            # User exists, show main menu
            await show_main_menu(update, context)
            return ConversationHandler.END
        else:
            # New user, show language selection
            keyboard = [
                ["UZ 🇺🇿", "RU 🇷🇺", "EN 🇺🇸"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            welcome_text = (
                "🏡 Assalomu Aleykum!\n"
                "🤖 UyizlangBotga Hush kelibsiz!\n\n"
                "Maklersiz 🧾 oson uy toping va soting 🏠\n"
                "Bizning maqsad — sizga ishonchli, tez va qulay uy savdosini ta'minlash 💪\n\n"
                "⚠️ Ogohlantirish:\n"
                "Sizning tajribangiz alohida e'tiborga olinadi!\n\n"
                "📄 1. Hujjatlarni tekshiring:\n"
                "• 📋 Kadastr hujjati mavjudligi\n"
                "• 🆔 Pasportni tekshirish  \n"
                "• 📝 Yozma shartnoma\n\n"
                "💰 2. To'lov masalasida ehtiyot bo'ling:\n"
                "• 👤 Noma'lum shaxslarga pul bermang\n"
                "• 🏦 Bank orqali to'lov\n"
                "• 🧾 Kvitansiyani saqlang\n\n"
                "🏠 3. Uy joylashuvini tekshirish:\n"
                "• 🗺️ Manzilni tekshirish\n"
                "• 👥 Qo'shnilar bilan suhbat\n\n"
                "🤝 4. Ishonchli bitim tuzing:\n"
                "• 📄 Yozma shartnoma\n"
                "• ⚖️ Huquqshunos bilan maslahat\n\n"
                "💡 Eslatma:\n"
                "Bot faqat aloqa va e'lon joylashtirish imkonini beradi.\n"
                "Bitim javobgarligi foydalanuvchida.\n\n"
                "✨ Barokatlik Savdo Tilaymiz!\n\n"
                "🌐 Iltimos, tilni tanlang:"
            )
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            return LANGUAGE
    finally:
        db.close()

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = update.message.text.split()[0].lower()
    context.user_data['language'] = language
    
    # Save user to database
    db = SessionLocal()
    try:
        user = User(
            telegram_id=update.effective_user.id,
            language=language
        )
        db.add(user)
        db.commit()
        
        # Request phone number
        await update.message.reply_text(
            "📞 Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[{"text": "📞 Telefon raqamni yuborish", "request_contact": True}]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return PHONE
    finally:
        db.close()

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
    
    # Update user in database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        user.phone = phone_number
        db.commit()
        
        context.user_data['phone'] = phone_number
        
        # Request location
        await update.message.reply_text(
            "📍 Joylashuvingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[{"text": "📍 Joylashuvni yuborish", "request_location": True}]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return LOCATION
    finally:
        db.close()

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        location = f"{update.message.location.latitude}, {update.message.location.longitude}"
    else:
        location = update.message.text
    
    # Update user in database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        user.location = location
        db.commit()
        
        # Registration complete
        await update.message.reply_text(
            "🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
            "🏡 Asosiy menyu:",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await show_main_menu(update, context)
        return ConversationHandler.END
    finally:
        db.close()

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Elon Berish", "📋 Mening elonlarim"],
        ["🔍 Qidiruv", "🆘 Qo'llab-quvvatlash"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    text = (
        "🏡 Asosiy menyu:\n\n"
        "• 🏠 Elon Berish - Yangi e'lon joylashtirish\n"
        "• 📋 Mening elonlarim - Sizning barcha e'lonlaringiz\n"
        "• 🔍 Qidiruv - Uylarni qidirish\n"
        "• 🆘 Qo'llab-quvvatlash - Yordam va admin bilan aloqa"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

# Start conversation handler
start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start_handler)],
    states={
        LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language)],
        PHONE: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, phone_handler)],
        LOCATION: [MessageHandler(filters.LOCATION | filters.TEXT & ~filters.COMMAND, location_handler)],
    },
    fallbacks=[],
)