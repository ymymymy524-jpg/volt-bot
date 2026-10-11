"""
═══════════════════════════════════════════════════════════
🔐 Discord OAuth2 Authentication
═══════════════════════════════════════════════════════════
"""

import os
import requests
from functools import wraps
from flask import session, redirect, url_for
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════
# 🔑 الإعدادات
# ═══════════════════════════════════════
CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:8000/callback')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Discord API endpoints
DISCORD_API = 'https://discord.com/api/v10'
OAUTH_URL = 'https://discord.com/api/oauth2/authorize'
TOKEN_URL = 'https://discord.com/api/oauth2/token'


# ═══════════════════════════════════════
# 🔗 دوال OAuth2
# ═══════════════════════════════════════
def get_login_url():
    """رابط تسجيل الدخول بـ Discord"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify guilds',
    }
    return f"{OAUTH_URL}?{urlencode(params)}"


def exchange_code(code):
    """تبديل الـ code بالـ access token"""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        print(f"❌ فشل exchange_code: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"❌ خطأ في exchange_code: {e}")
        return None


def get_user_info(access_token):
    """جلب معلومات المستخدم من Discord"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(f'{DISCORD_API}/users/@me', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ خطأ في get_user_info: {e}")
        return None


def get_user_guilds(access_token):
    """جلب سيرفرات المستخدم اللي هو أدمن فيها"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(f'{DISCORD_API}/users/@me/guilds', headers=headers, timeout=10)
        if response.status_code == 200:
            guilds = response.json()
            # فلتر: بس السيرفرات اللي المستخدم عنده صلاحية Administrator فيها
            admin_guilds = []
            for guild in guilds:
                permissions = int(guild.get('permissions', 0))
                # 0x8 = ADMINISTRATOR
                if permissions & 0x8:
                    admin_guilds.append(guild)
            return admin_guilds
        return []
    except Exception as e:
        print(f"❌ خطأ في get_user_guilds: {e}")
        return []


def get_guild_info(guild_id):
    """جلب معلومات سيرفر معين من Discord API"""
    if not BOT_TOKEN:
        print("⚠️ DISCORD_BOT_TOKEN مش موجود")
        return None
    
    headers = {'Authorization': f'Bot {BOT_TOKEN}'}
    
    try:
        response = requests.get(
            f'{DISCORD_API}/guilds/{guild_id}?with_counts=true',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # نبني صورة السيرفر
            icon_url = None
            if data.get('icon'):
                icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{data['icon']}.png?size=256"
            
            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'icon': icon_url,
                'member_count': data.get('approximate_member_count', data.get('member_count', 0)),
                'owner_id': data.get('owner_id'),
            }
        return None
    except Exception as e:
        print(f"❌ خطأ في get_guild_info: {e}")
        return None


def get_best_guild_for_user(access_token):
    """اختيار أفضل سيرفر للمستخدم (المستخدم + البوت)"""
    user_guilds = get_user_guilds(access_token)
    
    if not user_guilds:
        return None
    
    # فلتر السيرفرات اللي البوت فيها
    for guild in user_guilds:
        guild_id = guild.get('id')
        # نتأكد إن البوت موجود في السيرفر
        bot_guild = get_guild_info(guild_id)
        if bot_guild:
            return guild
    
    # لو مفيش، رجع أول سيرفر
    return user_guilds[0] if user_guilds else None


def is_user_admin(access_token):
    """التحقق إن المستخدم أدمن في أي سيرفر"""
    guilds = get_user_guilds(access_token)
    return len(guilds) > 0


def get_avatar_url(user_info):
    """بناء رابط صورة المستخدم"""
    if not user_info:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    
    user_id = user_info.get('id')
    avatar = user_info.get('avatar')
    
    if avatar:
        # صورة مخصصة
        ext = 'gif' if avatar.startswith('a_') else 'png'
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=256"
    else:
        # صورة افتراضية
        discriminator = user_info.get('discriminator', '0')
        default_index = int(discriminator) % 5 if discriminator != '0' else 0
        return f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"


def get_user_display_name(user_info):
    """اسم المستخدم للعرض"""
    if not user_info:
        return 'User'
    return user_info.get('global_name') or user_info.get('username', 'User')


def discord_login_required(f):
    """Decorator للصفحات اللي محتاجة تسجيل دخول"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated