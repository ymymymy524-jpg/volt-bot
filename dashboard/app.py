from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import random
import requests

from auth import (
    get_login_url, exchange_code, get_user_info, get_user_guilds,
    get_guild_info, get_best_guild_for_user, is_user_admin,
    get_avatar_url, get_user_display_name, discord_login_required,
)
from commands_list import ALL_COMMANDS
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'default_secret_key_change_this')

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.config['SESSION_COOKIE_NAME'] = 'volt_session'

RAILWAY_API_URL = os.getenv("RAILWAY_API_URL", "https://volt-bot-production-840e.up.railway.app")
BOT_API_SECRET = os.getenv("BOT_API_SECRET", "volt_secret_2024")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def load_json_file(filename):
    filepath = os.path.join('..', filename)
    if not os.path.exists(filepath):
        filepath = filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json_file(filename, data):
    filepath = os.path.join('..', filename)
    if not os.path.exists(filepath):
        filepath = filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def auto_apply_shortcuts(config):
    """⭐ Auto-Apply: يبعت الاختصارات للـ Railway تلقائي"""
    try:
        auto_data = {
            key: {
                "enabled": val.get("enabled", True),
                "shortcut": val.get("shortcut", "")
            }
            for key, val in config.items()
        }
        
        response = requests.post(
            f"{RAILWAY_API_URL}/api/shortcuts/apply",
            json={"shortcuts": auto_data},
            headers={
                "Authorization": f"Bearer {BOT_API_SECRET}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.ok:
            result = response.json()
            return result.get("count", 0)
        return None
    except Exception as e:
        print(f"⚠️ Auto-apply error: {e}")
        return None


def get_all_users():
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



    
# =================== Routes ===================

@app.route('/')
def index():
    return render_template('login.html', discord_login_url=get_login_url())


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')


@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html', discord_login_url=get_login_url())


@app.route('/callback')
def callback():
    error = request.args.get('error')
    if error:
        return render_template('login.html', error='تم إلغاء تسجيل الدخول', discord_login_url=get_login_url())
    
    code = request.args.get('code')
    if not code:
        return render_template('login.html', error='لم يتم استلام الكود', discord_login_url=get_login_url())
    
    token_data = exchange_code(code)
    if not token_data:
        return render_template('login.html', error='فشل في تبادل الكود', discord_login_url=get_login_url())
    
    access_token = token_data.get('access_token')
    if not access_token:
        return render_template('login.html', error='لم يتم استلام التوكن', discord_login_url=get_login_url())
    
    user_info = get_user_info(access_token)
    if not user_info:
        return render_template('login.html', error='فشل في جلب معلومات المستخدم', discord_login_url=get_login_url())
    
    selected_guild = get_best_guild_for_user(access_token)
    guild_id = selected_guild.get('id') if selected_guild else None
    
    session['user'] = {
        'id': user_info.get('id'),
        'username': user_info.get('username'),
        'discriminator': user_info.get('discriminator', '0'),
        'avatar': user_info.get('avatar'),
        'avatar_url': get_avatar_url(user_info),
        'display_name': get_user_display_name(user_info),
    }
    session['logged_in'] = True
    session['login_time'] = datetime.now().isoformat()
    session['is_admin'] = is_user_admin(access_token)
    session['guild_id'] = guild_id
    
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


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


@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')


# =================== APIs ===================

@app.route('/api/user')
def api_user():
    if 'user' not in session:
        return jsonify({'success': False, 'user': None})
    return jsonify({
        'success': True,
        'user': session.get('user', {}),
        'is_admin': session.get('is_admin', False),
        'guild_id': session.get('guild_id')
    })


@app.route('/api/guild-info')
def api_guild_info():
    try:
        guild_id = session.get('guild_id')
        if not guild_id:
            return jsonify({'success': False, 'error': 'No guild selected'}), 404
        try:
            response = requests.get(f"{RAILWAY_API_URL}/api/guilds/{guild_id}", timeout=10)
            if response.ok:
                guild_data = response.json().get('guild', {})
                if guild_data.get('name'):
                    return jsonify({'success': True, 'guild': guild_data})
        except Exception as e:
            print(f"⚠️ فشل جلب السيرفر من Railway: {e}")
        guild = get_guild_info(guild_id)
        if guild:
            return jsonify({'success': True, 'guild': guild})
        return jsonify({'success': False, 'error': 'Guild not found'}), 404
    except Exception as e:
        print(f"❌ خطأ في /api/guild-info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/leaderboard')
def api_leaderboard():
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        sorted_users = sorted(bitcoin_data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:10]
        leaderboard = []
        for rank, (user_id, data) in enumerate(sorted_users, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': user_id,
                'balance': data.get('balance', 0)
            })
        return jsonify({'success': True, 'data': leaderboard})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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


# ═══════════════════════════════════════
# 🎯 Commands API
# ═══════════════════════════════════════
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
        
        # ⭐ Auto-Apply
        count = auto_apply_shortcuts(config)
        if count is not None:
            return jsonify({
                'success': True,
                'message': f'✅ تم الحفظ + التطبيق ({count} اختصار)'
            })
        else:
            return jsonify({
                'success': True,
                'message': '⚠️ تم الحفظ — بس البوت مش مستجيب'
            })
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
        
        # ⭐ Auto-Apply
        count = auto_apply_shortcuts(config)
        status = "تفعيل" if enabled else "تعطيل"
        if count is not None:
            return jsonify({
                'success': True,
                'message': f'✅ تم {status} + التطبيق'
            })
        return jsonify({
            'success': True,
            'message': f'⚠️ تم {status} — بس البوت مش مستجيب'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shortcuts/apply', methods=['POST'])
@login_required
def api_apply_shortcuts():
    try:
        data = request.get_json()
        if not data or 'shortcuts' not in data:
            return jsonify({'success': False, 'status': 'error', 'error': '❌ مفيش بيانات'}), 400
        
        print(f"📤 جاري إرسال {len(data['shortcuts'])} اختصار للـ Railway...")
        
        response = requests.post(
            f"{RAILWAY_API_URL}/api/shortcuts/apply",
            json=data,
            headers={
                "Authorization": f"Bearer {BOT_API_SECRET}",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        
        try:
            result = response.json()
        except:
            result = {"detail": response.text}
        
        print(f"📥 رد من Railway: {response.status_code}")
        
        if response.ok:
            return jsonify({
                'success': True,
                'status': 'ok',
                'message': result.get('message', '✅ تم التطبيق'),
                'count': result.get('count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'status': 'error',
                'error': result.get('detail', 'فشل التطبيق')
            }), response.status_code
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'status': 'error', 'error': '❌ البوت مش مستجيب'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'status': 'error', 'error': '❌ مش قادر أوصل للبوت'}), 503
    except Exception as e:
        return jsonify({'success': False, 'status': 'error', 'error': f'❌ خطأ: {str(e)}'}), 500


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
    app.run(host='0.0.0.0', port=port, debug=False)