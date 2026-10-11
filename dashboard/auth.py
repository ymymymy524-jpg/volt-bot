"""
🔐 Discord OAuth2 Authentication + Guild Info
"""
import os
import requests
from functools import wraps
from flask import session, redirect, url_for, request
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════
# 🔑 إعدادات Discord OAuth2
# ═══════════════════════════════════════
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

BASE_URL = os.getenv("BASE_URL", "https://volt-bot-ijni.onrender.com")
REDIRECT_URI = f"{BASE_URL}/callback"

DISCORD_API = "https://discord.com/api/v10"
OAUTH_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = f"{DISCORD_API}/oauth2/token"
USER_URL = f"{DISCORD_API}/users/@me"
GUILDS_URL = f"{DISCORD_API}/users/@me/guilds"


# ═══════════════════════════════════════
# 🔗 رابط تسجيل الدخول
# ═══════════════════════════════════════
def get_login_url():
    """رابط تسجيل الدخول بـ Discord"""
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
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(GUILDS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في جلب السيرفرات: {e}")
        return []


# ═══════════════════════════════════════
# 🏰 جلب معلومات سيرفر محدد (بـ Bot Token)
# ═══════════════════════════════════════
def get_guild_info(guild_id):
    """جلب معلومات السيرفر باستخدام Bot Token"""
    if not DISCORD_TOKEN:
        print("⚠️ DISCORD_TOKEN مش موجود")
        return None
    
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    
    try:
        response = requests.get(
            f"{DISCORD_API}/guilds/{guild_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        icon_url = None
        if data.get("icon"):
            icon_url = f"https://cdn.discordapp.com/icons/{data['id']}/{data['icon']}.png?size=256"
        
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "icon": icon_url,
            "member_count": data.get("member_count", 0),
            "owner_id": data.get("owner_id"),
        }
    except requests.exceptions.HTTPError as e:
        print(f"❌ خطأ في جلب السيرفر {guild_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None


# ═══════════════════════════════════════
# 🎯 اختيار أفضل سيرفر للمستخدم
# ═══════════════════════════════════════
def get_best_guild_for_user(access_token):
    """جلب أفضل سيرفر للمستخدم (اللي فيه البوت)"""
    user_guilds = get_user_guilds(access_token)
    
    if not user_guilds:
        return None
    
    # فلترة السيرفرات اللي المستخدم أدمن فيها
    admin_guilds = []
    for guild in user_guilds:
        try:
            permissions = int(guild.get("permissions", 0))
            # Administrator (0x8) أو Manage Server (0x20)
            if permissions & 0x8 or permissions & 0x20:
                admin_guilds.append(guild)
        except (ValueError, TypeError):
            continue
    
    # لو فيه سيرفرات أدمن → ناخد أول واحد
    if admin_guilds:
        return admin_guilds[0]
    
    # fallback: أول سيرفر في القايمة
    return user_guilds[0]


# ═══════════════════════════════════════
# ✅ التحقق من صلاحيات المستخدم
# ═══════════════════════════════════════
def is_user_admin(access_token):
    guilds = get_user_guilds(access_token)
    ADMIN_PERMISSION = 0x8
    MANAGE_GUILD = 0x20
    
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
    user_id = user_data.get("id")
    avatar = user_data.get("avatar")
    
    if avatar:
        return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png?size=256"
    else:
        discriminator = user_data.get("discriminator", "0")
        try:
            default_index = int(discriminator) % 5
        except ValueError:
            default_index = 0
        return f"https://cdn.discordapp.com/embed/avatars/{default_index}.png"


def get_user_display_name(user_data):
    global_name = user_data.get("global_name")
    username = user_data.get("username", "Unknown")
    
    if global_name:
        return global_name
    return username


# ═══════════════════════════════════════
# 🔐 Decorators
# ═══════════════════════════════════════
def discord_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        
        if not session.get("is_admin", False):
            return redirect(url_for("index"))
        
        return f(*args, **kwargs)
    return decorated_function