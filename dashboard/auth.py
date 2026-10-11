"""
🔐 Discord OAuth2 Authentication
نظام تسجيل الدخول بحساب ديسكورد
"""
import os
import requests
from functools import wraps
from flask import session, redirect, url_for, request
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()

# ═══════════════════════════════════════
# 🔑 إعدادات Discord OAuth2
# ═══════════════════════════════════════
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# ═══════════════════════════════════════
# 🌐 الرابط الأساسي
# ═══════════════════════════════════════
BASE_URL = os.getenv("BASE_URL", "https://volt-bot-ijni.onrender.com")
REDIRECT_URI = f"{BASE_URL}/callback"

# ═══════════════════════════════════════
# 🌐 Discord API Endpoints
# ═══════════════════════════════════════
DISCORD_API = "https://discord.com/api/v10"
OAUTH_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = f"{DISCORD_API}/oauth2/token"
USER_URL = f"{DISCORD_API}/users/@me"
GUILDS_URL = f"{DISCORD_API}/users/@me/guilds"


# ═══════════════════════════════════════
# 🔗 رابط تسجيل الدخول
# ═══════════════════════════════════════
def get_login_url():
    """إنشاء رابط تسجيل الدخول بـ Discord"""
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{OAUTH_URL}?{query}"


# ═══════════════════════════════════════
# 🔄 تبادل الكود بالتوكن
# ═══════════════════════════════════════
def exchange_code(code):
    """تحويل الـ code لـ access token"""
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في تبادل الكود: {e}")
        return None


# ═══════════════════════════════════════
# 👤 جلب معلومات المستخدم
# ═══════════════════════════════════════
def get_user_info(access_token):
    """جلب معلومات المستخدم من Discord API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(USER_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في جلب معلومات المستخدم: {e}")
        return None


# ═══════════════════════════════════════
# 🏰 جلب سيرفرات المستخدم
# ═══════════════════════════════════════
def get_user_guilds(access_token):
    """جلب سيرفرات المستخدم"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(GUILDS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في جلب السيرفرات: {e}")
        return []


# ═══════════════════════════════════════
# ✅ التحقق من صلاحيات المستخدم
# ═══════════════════════════════════════
def is_user_admin(access_token):
    """التحقق إذا كان المستخدم أدمن في أي سيرفر"""
    guilds = get_user_guilds(access_token)
    
    # صلاحيات Discord
    ADMIN_PERMISSION = 0x8        # Administrator
    MANAGE_GUILD = 0x20            # Manage Server
    
    for guild in guilds:
        try:
            permissions = int(guild.get("permissions", 0))
            if permissions & ADMIN_PERMISSION or permissions & MANAGE_GUILD:
                return True
        except (ValueError, TypeError):
            continue
    
    return False


# ═══════════════════════════════════════
# 🎨 دوال مساعدة
# ═══════════════════════════════════════
def get_avatar_url(user_data):
    """جلب رابط صورة المستخدم"""
    user_id = user_data.get("id")
    avatar = user_data.get("avatar")
    
    if avatar:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png"
    else:
        # صورة افتراضية
        discriminator = user_data.get("discriminator", "0")
        try:
            default_index = int(discriminator) % 5
        except ValueError:
            default_index = 0
        return f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"


def get_user_display_name(user_data):
    """اسم المستخدم للعرض"""
    global_name = user_data.get("global_name")
    username = user_data.get("username", "Unknown")
    
    if global_name:
        return global_name
    return username


# ═══════════════════════════════════════
# 🔐 Decorator للحماية
# ═══════════════════════════════════════
def discord_login_required(f):
    """Decorator للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator للتحقق من صلاحيات الأدمن"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        
        if not session.get("is_admin", False):
            return redirect(url_for("index"))
        
        return f(*args, **kwargs)
    return decorated_function