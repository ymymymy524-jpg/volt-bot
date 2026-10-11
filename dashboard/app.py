from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import random

# 🔐 Discord OAuth2
from auth import (
    get_login_url, 
    exchange_code, 
    get_user_info, 
    get_user_guilds,
    is_user_admin,
    get_avatar_url,
    get_user_display_name,
    discord_login_required,
)

# تحميل المتغيرات
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'default_secret_key_change_this')

# =================== دوال مساعدة ===================

def login_required(f):
    """Decorator للتحقق من تسجيل الدخول عبر Discord"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def load_json_file(filename):
    """تحميل بيانات من ملف JSON"""
    filepath = os.path.join('..', filename)
    if not os.path.exists(filepath):
        filepath = filename
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_json_file(filename, data):
    """حفظ بيانات في ملف JSON"""
    filepath = os.path.join('..', filename)
    if not os.path.exists(filepath):
        filepath = filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_all_users():
    """جلب جميع المستخدمين من كل الملفات"""
    bitcoin_data = load_json_file('bitcoin.json')
    levels_data = load_json_file('levels.json')
    games_data = load_json_file('games.json')
    invites_data = load_json_file('invites.json')
    
    users = {}
    
    for user_id, data in bitcoin_data.items():
        if user_id not in users:
            users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
        users[user_id]['balance'] = data.get('balance', 0)
        users[user_id]['total_earned'] = data.get('total_earned', 0)
        users[user_id]['total_spent'] = data.get('total_spent', 0)
    
    for guild_id, guild_data in levels_data.items():
        for user_id, data in guild_data.items():
            if user_id not in users:
                users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
            users[user_id]['level'] = data.get('level', 0)
            users[user_id]['xp'] = data.get('xp', 0)
    
    for user_id, data in games_data.items():
        if user_id not in users:
            users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
        users[user_id]['fizzy'] = data.get('fizzy', 0)
    
    for guild_id, guild_data in invites_data.items():
        for user_id, data in guild_data.items():
            if user_id not in users:
                users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
            users[user_id]['invites_real'] = data.get('real', 0)
            users[user_id]['invites_fake'] = data.get('fake', 0)
    
    return users


# ═══════════════════════════════════════
# 📋 قائمة الأوامر الكاملة
# ═══════════════════════════════════════
ALL_COMMANDS = [
    # 👑 الإدارة
    {"name": "ban", "description": "حظر عضو", "category": "الإدارة"},
    {"name": "kick", "description": "طرد عضو", "category": "الإدارة"},
    {"name": "unban", "description": "فك حظر عضو", "category": "الإدارة"},
    {"name": "ban-all", "description": "فك حظر الكل", "category": "الإدارة"},
    {"name": "warn", "description": "إنذار عضو", "category": "الإدارة"},
    {"name": "warnings", "description": "عرض الإنذارات", "category": "الإدارة"},
    {"name": "warnings-all", "description": "كل الإنذارات", "category": "الإدارة"},
    {"name": "warnings-settings", "description": "إعدادات الإنذارات", "category": "الإدارة"},
    {"name": "mute", "description": "كتم عضو", "category": "الإدارة"},
    {"name": "unmute", "description": "فك الكتم", "category": "الإدارة"},
    {"name": "timeout", "description": "تايم أوت", "category": "الإدارة"},
    {"name": "untimeout", "description": "فك التايم أوت", "category": "الإدارة"},
    {"name": "voice-mute", "description": "كتم صوتي", "category": "الإدارة"},
    {"name": "voice-deafen", "description": "منع سماع", "category": "الإدارة"},
    {"name": "clear", "description": "مسح رسائل", "category": "الإدارة"},
    {"name": "slowmode", "description": "الوضع البطيء", "category": "الإدارة"},
    {"name": "lock", "description": "قفل الروم", "category": "الإدارة"},
    {"name": "unlock", "description": "فتح الروم", "category": "الإدارة"},
    {"name": "hide", "description": "إخفاء الروم", "category": "الإدارة"},
    {"name": "unhide", "description": "إظهار الروم", "category": "الإدارة"},
    {"name": "move", "description": "نقل عضو", "category": "الإدارة"},
    {"name": "nick", "description": "تغيير الاسم", "category": "الإدارة"},
    {"name": "role-all", "description": "رتبة للكل", "category": "الإدارة"},
    {"name": "role", "description": "رتبة لعضو", "category": "الإدارة"},
    {"name": "prefix", "description": "تغيير البادئة", "category": "الإدارة"},
    
    # 🛡️ الحماية
    {"name": "protection auto", "description": "حماية تلقائية", "category": "الحماية"},
    {"name": "protection spam", "description": "حماية السبام", "category": "الحماية"},
    {"name": "protection link", "description": "حماية الروابط", "category": "الحماية"},
    {"name": "protection join", "description": "حماية الانضمام", "category": "الحماية"},
    {"name": "protection hacked", "description": "حماية الاختراق", "category": "الحماية"},
    {"name": "protection bans", "description": "حماية الحظر", "category": "الحماية"},
    {"name": "protection kicks", "description": "حماية الطرد", "category": "الحماية"},
    {"name": "protection channels", "description": "حماية الرومات", "category": "الحماية"},
    {"name": "protection roles", "description": "حماية الرتب", "category": "الحماية"},
    {"name": "protection bots", "description": "حماية البوتات", "category": "الحماية"},
    
    # 📊 المستويات
    {"name": "rank", "description": "مستواك", "category": "المستويات"},
    {"name": "top", "description": "أفضل الأعضاء", "category": "المستويات"},
    {"name": "setlevel", "description": "تحديد مستوى", "category": "المستويات"},
    {"name": "resetlevel", "description": "تصفير مستوى", "category": "المستويات"},
    
    # 🎵 الموسيقى
    {"name": "play", "description": "تشغيل أغنية", "category": "الموسيقى"},
    {"name": "pause", "description": "إيقاف مؤقت", "category": "الموسيقى"},
    {"name": "resume", "description": "استكمال", "category": "الموسيقى"},
    {"name": "skip", "description": "تخطي", "category": "الموسيقى"},
    {"name": "stop", "description": "إيقاف", "category": "الموسيقى"},
    {"name": "queue", "description": "قائمة التشغيل", "category": "الموسيقى"},
    {"name": "volume", "description": "تعديل الصوت", "category": "الموسيقى"},
    {"name": "nowplaying", "description": "الأغنية الحالية", "category": "الموسيقى"},
    
    # 📨 الدعوات
    {"name": "invites", "description": "عدد الدعوات", "category": "الدعوات"},
    {"name": "inviter", "description": "مين دعاك", "category": "الدعوات"},
    {"name": "invitetop", "description": "أفضل الداعين", "category": "الدعوات"},
    {"name": "resetinvites", "description": "تصفير الدعوات", "category": "الدعوات"},
    
    # 🎫 التذاكر
    {"name": "ticket", "description": "فتح تذكرة", "category": "التذاكر"},
    {"name": "close", "description": "إغلاق التذكرة", "category": "التذاكر"},
    {"name": "add", "description": "إضافة عضو", "category": "التذاكر"},
    {"name": "remove", "description": "إزالة عضو", "category": "التذاكر"},
    {"name": "setticket", "description": "تحديد الروم", "category": "التذاكر"},
    
    # 👋 الترحيب
    {"name": "setwelcome", "description": "روم الترحيب", "category": "الترحيب"},
    {"name": "setgoodbye", "description": "روم الوداع", "category": "الترحيب"},
    {"name": "testwelcome", "description": "تجربة الترحيب", "category": "الترحيب"},
    {"name": "welcome-set-status", "description": "حالة الترحيب", "category": "الترحيب"},
    
    # 🎮 الألعاب
    {"name": "game", "description": "الألعاب", "category": "الألعاب"},
    {"name": "bomb", "description": "القنبلة", "category": "الألعاب"},
    {"name": "button", "description": "زر الحظ", "category": "الألعاب"},
    {"name": "chairs", "description": "الكراسي", "category": "الألعاب"},
    {"name": "colors", "description": "الألوان", "category": "الألعاب"},
    {"name": "faster", "description": "الأسرع", "category": "الألعاب"},
    {"name": "flags", "description": "الأعلام", "category": "الألعاب"},
    {"name": "mafia", "description": "المافيا", "category": "الألعاب"},
    {"name": "roulette", "description": "الروليت", "category": "الألعاب"},
    {"name": "fizzy", "description": "رصيد Fizzy", "category": "الألعاب"},
    
    # 💎 الاقتصاد
    {"name": "balance", "description": "الرصيد", "category": "الاقتصاد"},
    {"name": "daily", "description": "المكافأة اليومية", "category": "الاقتصاد"},
    {"name": "work", "description": "العمل", "category": "الاقتصاد"},
    {"name": "transfer", "description": "تحويل", "category": "الاقتصاد"},
    {"name": "bitcoin-top", "description": "أغنى الأعضاء", "category": "الاقتصاد"},
    {"name": "bitcoin-history", "description": "السجل", "category": "الاقتصاد"},
    {"name": "shop", "description": "المتجر", "category": "الاقتصاد"},
    {"name": "buy", "description": "شراء", "category": "الاقتصاد"},
    {"name": "bitcoin-admin", "description": "إدارة", "category": "الاقتصاد"},
    
    # 🤖 الذكاء الاصطناعي
    {"name": "ai ask", "description": "سؤال", "category": "الذكاء الاصطناعي"},
    {"name": "ai imagine", "description": "توليد صورة", "category": "الذكاء الاصطناعي"},
    {"name": "ai translate", "description": "ترجمة", "category": "الذكاء الاصطناعي"},
    {"name": "ai summarize", "description": "تلخيص", "category": "الذكاء الاصطناعي"},
    {"name": "ai code", "description": "كتابة كود", "category": "الذكاء الاصطناعي"},
    {"name": "ai story", "description": "قصة", "category": "الذكاء الاصطناعي"},
    {"name": "ai analyze", "description": "تحليل", "category": "الذكاء الاصطناعي"},
    
    # ⚙️ الإعدادات
    {"name": "add-emoji", "description": "إضافة إيموجي", "category": "الإعدادات"},
    {"name": "auto-message", "description": "رسالة تلقائية", "category": "الإعدادات"},
    {"name": "auto-reply", "description": "رد تلقائي", "category": "الإعدادات"},
    {"name": "automod", "description": "كلمات ممنوعة", "category": "الإعدادات"},
    {"name": "autorole", "description": "رتبة تلقائية", "category": "الإعدادات"},
    {"name": "change-log", "description": "السجل", "category": "الإعدادات"},
    {"name": "command-disable", "description": "تعطيل أمر", "category": "الإعدادات"},
    {"name": "level-up-msg", "description": "رسالة الترقية", "category": "الإعدادات"},
    {"name": "level", "description": "إعدادات المستوى", "category": "الإعدادات"},
    {"name": "log", "description": "اللوجات", "category": "الإعدادات"},
    {"name": "perms", "description": "الصلاحيات", "category": "الإعدادات"},
    {"name": "role-icon", "description": "أيقونة الرتبة", "category": "الإعدادات"},
    {"name": "role-info", "description": "معلومات الرتبة", "category": "الإعدادات"},
    {"name": "role-move", "description": "نقل الرتبة", "category": "الإعدادات"},
    {"name": "self-roles", "description": "الرتب الذاتية", "category": "الإعدادات"},
    {"name": "embed", "description": "Embed", "category": "الإعدادات"},
    {"name": "settings", "description": "الإعدادات", "category": "الإعدادات"},
    {"name": "setup", "description": "ضبط تلقائي", "category": "الإعدادات"},
    {"name": "shorts", "description": "اختصارات", "category": "الإعدادات"},
    {"name": "end-premium", "description": "إلغاء بريميوم", "category": "الإعدادات"},
    
    # 🛠️ عام
    {"name": "ping", "description": "سرعة البوت", "category": "عام"},
    {"name": "help", "description": "المساعدة", "category": "عام"},
    {"name": "avatar", "description": "الصورة", "category": "عام"},
    {"name": "banner", "description": "البانر", "category": "عام"},
    {"name": "user", "description": "معلومات عضو", "category": "عام"},
    {"name": "server", "description": "معلومات السيرفر", "category": "عام"},
    {"name": "volt", "description": "رصيد Volt", "category": "عام"},
    {"name": "crypto-top", "description": "أغنى الأعضاء", "category": "عام"},
]


# =================== Routes ===================

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    """صفحة تسجيل الدخول بـ Discord"""
    if 'user' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html', discord_login_url=get_login_url())


@app.route('/callback')
def callback():
    """Callback من Discord OAuth2"""
    error = request.args.get('error')
    if error:
        return render_template('login.html', 
                             error='تم إلغاء تسجيل الدخول',
                             discord_login_url=get_login_url())
    
    code = request.args.get('code')
    if not code:
        return render_template('login.html', 
                             error='لم يتم استلام الكود',
                             discord_login_url=get_login_url())
    
    token_data = exchange_code(code)
    if not token_data:
        return render_template('login.html', 
                             error='فشل في تبادل الكود',
                             discord_login_url=get_login_url())
    
    access_token = token_data.get('access_token')
    if not access_token:
        return render_template('login.html', 
                             error='لم يتم استلام التوكن',
                             discord_login_url=get_login_url())
    
    user_info = get_user_info(access_token)
    if not user_info:
        return render_template('login.html', 
                             error='فشل في جلب معلومات المستخدم',
                             discord_login_url=get_login_url())
    
    user_guilds = get_user_guilds(access_token)
    
    session['user'] = {
        'id': user_info.get('id'),
        'username': user_info.get('username'),
        'discriminator': user_info.get('discriminator', '0'),
        'avatar': user_info.get('avatar'),
        'avatar_url': get_avatar_url(user_info),
        'display_name': get_user_display_name(user_info),
        'access_token': access_token,
    }
    session['logged_in'] = True
    session['login_time'] = datetime.now().isoformat()
    session['guilds'] = user_guilds
    session['is_admin'] = is_user_admin(access_token)
    
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/commands')
@login_required
def commands():
    return render_template('commands.html')


@app.route('/users')
@login_required
def users():
    return render_template('users.html')


@app.route('/economy')
@login_required
def economy():
    return render_template('economy.html')


@app.route('/logs')
@login_required
def logs():
    return render_template('logs.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


# =================== APIs ===================

@app.route('/api/user')
@login_required
def api_user():
    return jsonify({
        'success': True,
        'user': session.get('user', {}),
        'is_admin': session.get('is_admin', False)
    })


@app.route('/api/stats')
@login_required
def api_stats():
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        levels_data = load_json_file('levels.json')
        games_data = load_json_file('games.json')
        
        total_users = len(bitcoin_data)
        total_balance = sum(user.get('balance', 0) for user in bitcoin_data.values())
        total_levels = sum(len(guild) for guild in levels_data.values())
        total_fizzy = sum(user.get('fizzy', 0) for user in games_data.values())
        
        chart_data = {
            'labels': ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'],
            'datasets': [{
                'label': 'النشاط اليومي',
                'data': [random.randint(50, 200) for _ in range(7)],
                'backgroundColor': 'rgba(139, 92, 246, 0.5)',
                'borderColor': 'rgba(139, 92, 246, 1)',
                'borderWidth': 2
            }]
        }
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'total_balance': total_balance,
                'total_levels': total_levels,
                'total_fizzy': total_fizzy,
                'chart_data': chart_data,
                'uptime': '24 ساعة'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users')
@login_required
def api_users():
    try:
        users = get_all_users()
        users_list = []
        for user_id, data in users.items():
            users_list.append({
                'id': user_id,
                'name': data.get('name', f'User {user_id}'),
                'balance': data.get('balance', 0),
                'level': data.get('level', 0),
                'xp': data.get('xp', 0),
                'fizzy': data.get('fizzy', 0),
                'invites_real': data.get('invites_real', 0),
                'invites_fake': data.get('invites_fake', 0)
            })
        return jsonify({'success': True, 'data': users_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/economy')
@login_required
def api_economy():
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        total_balance = sum(user.get('balance', 0) for user in bitcoin_data.values())
        total_earned = sum(user.get('total_earned', 0) for user in bitcoin_data.values())
        total_spent = sum(user.get('total_spent', 0) for user in bitcoin_data.values())
        
        recent_transactions = []
        for user_id, data in bitcoin_data.items():
            for tx in data.get('transactions', [])[-5:]:
                recent_transactions.append({
                    'user_id': user_id,
                    'type': tx.get('type'),
                    'amount': tx.get('amount'),
                    'description': tx.get('description'),
                    'timestamp': tx.get('timestamp')
                })
        
        recent_transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent_transactions = recent_transactions[:20]
        
        return jsonify({
            'success': True,
            'data': {
                'total_balance': total_balance,
                'total_earned': total_earned,
                'total_spent': total_spent,
                'total_users': len(bitcoin_data),
                'recent_transactions': recent_transactions,
                'settings': {
                    'daily_min': 100,
                    'daily_max': 500,
                    'work_min': 50,
                    'work_max': 200,
                    'transfer_fee': 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/commands')
@login_required
def api_commands():
    try:
        config = load_json_file('commands_config.json')
        commands_list = []
        for cmd in ALL_COMMANDS:
            cmd_name = cmd['name']
            cmd_config = config.get(cmd_name, {})
            commands_list.append({
                'name': cmd_name,
                'description': cmd_config.get('description', cmd['description']),
                'category': cmd['category'],
                'enabled': cmd_config.get('enabled', True),
                'shortcut': cmd_config.get('shortcut', '')
            })
        return jsonify({'success': True, 'data': commands_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/commands/save', methods=['POST'])
@login_required
def api_save_command():
    try:
        data = request.get_json()
        cmd_name = data.get('name')
        shortcut = data.get('shortcut', '').strip()
        description = data.get('description')
        enabled = data.get('enabled', True)
        
        config = load_json_file('commands_config.json')
        if cmd_name not in config:
            config[cmd_name] = {}
        
        config[cmd_name]['shortcut'] = shortcut
        config[cmd_name]['enabled'] = enabled
        if description:
            config[cmd_name]['description'] = description
        
        save_json_file('commands_config.json', config)
        return jsonify({'success': True, 'message': f'تم حفظ الأمر {cmd_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/commands/toggle', methods=['POST'])
@login_required
def api_toggle_command():
    try:
        data = request.get_json()
        command_name = data.get('command')
        enabled = data.get('enabled')
        
        config = load_json_file('commands_config.json')
        if command_name not in config:
            config[command_name] = {}
        
        config[command_name]['enabled'] = enabled
        save_json_file('commands_config.json', config)
        
        return jsonify({
            'success': True,
            'message': f'تم {"تفعيل" if enabled else "تعطيل"} الأمر'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/commands/reload', methods=['POST'])
@login_required
def api_reload_commands():
    """محاكاة إعادة تحميل (البوت يعمل reload كل 60 ثانية)"""
    try:
        # نلمس الملف عشان البوت يلاحظ التغيير
        config_file = os.path.join('..', 'commands_config.json')
        if not os.path.exists(config_file):
            config_file = 'commands_config.json'
        
        if os.path.exists(config_file):
            os.utime(config_file, None)
        
        return jsonify({
            'success': True,
            'message': '✅ تم الحفظ - البوت هيعمل reload خلال 60 ثانية'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<user_id>/balance', methods=['POST'])
@login_required
def api_update_balance(user_id):
    try:
        data = request.get_json()
        new_balance = int(data.get('balance', 0))
        
        bitcoin_data = load_json_file('bitcoin.json')
        
        if user_id not in bitcoin_data:
            bitcoin_data[user_id] = {
                'balance': 0, 'total_earned': 0, 'total_spent': 0,
                'last_daily': None, 'last_work': None,
                'transactions': [], 'inventory': []
            }
        
        old_balance = bitcoin_data[user_id].get('balance', 0)
        bitcoin_data[user_id]['balance'] = new_balance
        
        transaction = {
            'type': 'admin',
            'amount': new_balance - old_balance,
            'description': 'تعديل من Dashboard',
            'timestamp': datetime.now().isoformat()
        }
        bitcoin_data[user_id]['transactions'].append(transaction)
        
        save_json_file('bitcoin.json', bitcoin_data)
        return jsonify({'success': True, 'message': f'تم تحديث رصيد {user_id}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/logs')
@login_required
def api_logs():
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        all_logs = []
        
        for user_id, data in bitcoin_data.items():
            for tx in data.get('transactions', []):
                all_logs.append({
                    'user_id': user_id,
                    'type': 'bitcoin',
                    'action': tx.get('type'),
                    'details': tx.get('description'),
                    'amount': tx.get('amount'),
                    'timestamp': tx.get('timestamp')
                })
        
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify({'success': True, 'data': all_logs[:100]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    try:
        if request.method == 'POST':
            data = request.get_json()
            settings_data = load_json_file('settings.json')
            settings_data.update(data)
            save_json_file('settings.json', settings_data)
            return jsonify({'success': True, 'message': 'تم الحفظ'})
        else:
            settings_data = load_json_file('settings.json')
            return jsonify({'success': True, 'data': settings_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =================== تشغيل ===================

if __name__ == '__main__':
    port = int(os.getenv('DASHBOARD_PORT', 8000))
    print(f"🚀 Dashboard يعمل على: http://localhost:{port}")
    print(f"🔐 تسجيل الدخول عبر Discord OAuth2")
    app.run(host='0.0.0.0', port=port, debug=False)