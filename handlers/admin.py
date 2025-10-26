from telegram import Update
from telegram.ext import ContextTypes
from config.database import SessionLocal
from models.user import User, Listing
import os

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user is admin
    if update.effective_user.id != int(os.getenv('ADMIN_ID')):
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    
    db = SessionLocal()
    try:
        # Get statistics
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