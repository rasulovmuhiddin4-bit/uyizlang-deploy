from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from config.database import SessionLocal
from models.user import Listing

app = Flask(__name__)
CORS(app)  # Barcha domainlar uchun ruxsat

# Konfiguratsiya
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# HTML faylni serve qilish
@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/map')
def serve_map():
    return send_file('index.html')

# Namuna ma'lumotlar
def get_sample_listings():
    """Namuna ma'lumotlar"""
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    
    return [
        {
            'id': 1,
            'title': "Olmazor tumanida Kvartira",
            'description': "Holati zo'r, hamma sharoitlar bor, yangi ta'mir, metro yaqinida",
            'price': "95,000 USD",
            'rooms': 3,
            'floor': "5/12",
            'location': [41.311081, 69.240562],
            'phone': "+998901234567",
            'images': [
                'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=400&h=300&fit=crop'
            ],
            'created_at': now.isoformat(),
            'is_new': True,
            'is_active': True
        },
        {
            'id': 2,
            'title': "Yunusobod tumanida Xovli",
            'description': "Yangi ta'mir, 6 sotix, hovli, bog' bor",
            'price': "120,000 USD",
            'rooms': 4,
            'floor': "1/1",
            'location': [41.351081, 69.280562],
            'phone': "+998901234568",
            'images': [
                'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=400&h=300&fit=crop',
                'https://images.unsplash.com/photo-1494526585095-c41746248156?w=400&h=300&fit=crop'
            ],
            'created_at': two_days_ago.isoformat(),
            'is_new': False,
            'is_active': True
        }
    ]

def get_listings_from_db():
    """Ma'lumotlar bazasidan e'lonlarni olish"""
    try:
        # Database dan e'lonlarni olish
        db = SessionLocal()
        listings = db.query(Listing).filter(Listing.is_active == True).order_by(Listing.created_at.desc()).all()
        
        result = []
        for listing in listings:
            # Rasmlarni JSON dan o'qish
            images = json.loads(listing.images) if listing.images else []
            
            # Telegram file_id larni to'g'ri URL larga o'zgartirish
            formatted_images = []
            for img in images:
                if img.startswith('AgACAgI'):  # Telegram file_id
                    # Fallback rasmlar
                    fallback_images = [
                        'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop',
                        'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=400&h=300&fit=crop',
                        'https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=400&h=300&fit=crop',
                        'https://images.unsplash.com/photo-1494526585095-c41746248156?w=400&h=300&fit=crop',
                        'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=400&h=300&fit=crop'
                    ]
                    # Har bir e'lon uchun turli fallback rasm
                    fallback_img = fallback_images[listing.id % len(fallback_images)]
                    formatted_images.append(fallback_img)
                else:
                    formatted_images.append(img)
            
            # Agar rasmlar bo'lmasa, fallback qo'shish
            if not formatted_images:
                formatted_images = [
                    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop'
                ]
            
            # E'lon yangiligini aniqlash (24 soat)
            is_new = (datetime.now() - listing.created_at) < timedelta(hours=24)
            
            # Location ni to'g'ri formatlash
            location = [41.311081, 69.240562]  # Default Toshkent
            if listing.location:
                try:
                    if ',' in listing.location:
                        coords = listing.location.split(',')
                        location = [float(coords[0].strip()), float(coords[1].strip())]
                except:
                    pass
            
            listing_data = {
                'id': listing.id,
                'title': listing.title,
                'description': listing.description,
                'price': f"{listing.price:,} {listing.currency}",
                'rooms': listing.rooms,
                'floor': f"{listing.floor}/{listing.total_floors}",
                'location': location,
                'phone': listing.phone,
                'images': formatted_images,  # To'g'ri URL lar
                'created_at': listing.created_at.isoformat(),
                'is_new': is_new,
                'is_active': listing.is_active
            }
            result.append(listing_data)
        
        return result
    except Exception as e:
        print(f"Database xatosi: {e}")
        # Agar database bilan muammo bo'lsa, namuna ma'lumotlarni qaytaramiz
        return get_sample_listings()
    finally:
        db.close()

@app.route('/api/listings', methods=['GET'])
def get_listings():
    """Barcha e'lonlarni qaytarish"""
    try:
        listings = get_listings_from_db()
        return jsonify({
            'success': True,
            'data': listings,
            'count': len(listings),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    """Bitta e'lonni qaytarish"""
    try:
        listings = get_listings_from_db()
        listing = next((l for l in listings if l['id'] == listing_id), None)
        
        if not listing:
            return jsonify({
                'success': False,
                'error': 'E\'lon topilmadi'
            }), 404
        
        return jsonify({
            'success': True,
            'data': listing
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Server holatini tekshirish"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Uyizlang API'
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistika ma'lumotlari"""
    try:
        listings = get_listings_from_db()
        total_listings = len(listings)
        active_listings = len([l for l in listings if l['is_active']])
        new_listings = len([l for l in listings if l['is_new']])
        
        return jsonify({
            'success': True,
            'data': {
                'total_listings': total_listings,
                'active_listings': active_listings,
                'new_listings_24h': new_listings,
                'updated_at': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Uyizlang API serveri {port}-portda ishga tushdi!")
    print(f"📊 API endpoints:")
    print(f"   GET / - Xarita (HTML)")
    print(f"   GET /api/listings - Barcha e'lonlar")
    print(f"   GET /api/listings/<id> - Bitta e'lon")
    print(f"   GET /api/stats - Statistika")
    print(f"   GET /api/health - Server holati")
    print(f"🌐 Xarita: http://localhost:{port}/")
    
    app.run(host='0.0.0.0', port=port, debug=True)