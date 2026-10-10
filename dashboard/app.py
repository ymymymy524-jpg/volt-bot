from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import random

# تحميل المتغيرات من ملف .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'default_secret_key_change_this')

# =================== دوال مساعدة ===================

def login_required(f):
    """Decorator للتأكد من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
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
    
    # إضافة بيانات Bitcoin
    for user_id, data in bitcoin_data.items():
        if user_id not in users:
            users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
        users[user_id]['balance'] = data.get('balance', 0)
        users[user_id]['total_earned'] = data.get('total_earned', 0)
        users[user_id]['total_spent'] = data.get('total_spent', 0)
    
    # إضافة بيانات المستويات
    for guild_id, guild_data in levels_data.items():
        for user_id, data in guild_data.items():
            if user_id not in users:
                users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
            users[user_id]['level'] = data.get('level', 0)
            users[user_id]['xp'] = data.get('xp', 0)
    
    # إضافة بيانات Fizzy
    for user_id, data in games_data.items():
        if user_id not in users:
            users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
        users[user_id]['fizzy'] = data.get('fizzy', 0)
    
    # إضافة بيانات الدعوات
    for guild_id, guild_data in invites_data.items():
        for user_id, data in guild_data.items():
            if user_id not in users:
                users[user_id] = {'id': user_id, 'name': f'User {user_id}'}
            users[user_id]['invites_real'] = data.get('real', 0)
            users[user_id]['invites_fake'] = data.get('fake', 0)
    
    return users

# =================== Routes - الصفحات ===================

@app.route('/')
@login_required
def index():
    """الصفحة الرئيسية - الإحصائيات"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        password = request.form.get('password')
        dashboard_password = os.getenv('DASHBOARD_PASSWORD', 'admin123')
        
        if password == dashboard_password:
            session['logged_in'] = True
            session['login_time'] = datetime.now().isoformat()
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='كلمة السر غير صحيحة!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/commands')
@login_required
def commands():
    """صفحة الأوامر"""
    return render_template('commands.html')

@app.route('/users')
@login_required
def users():
    """صفحة الأعضاء"""
    return render_template('users.html')

@app.route('/economy')
@login_required
def economy():
    """صفحة الاقتصاد"""
    return render_template('economy.html')

@app.route('/logs')
@login_required
def logs():
    """صفحة السجلات"""
    return render_template('logs.html')

@app.route('/settings')
@login_required
def settings():
    """صفحة الإعدادات"""
    return render_template('settings.html')

# =================== API Endpoints ===================

@app.route('/api/stats')
@login_required
def api_stats():
    """إحصائيات عامة"""
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        levels_data = load_json_file('levels.json')
        games_data = load_json_file('games.json')
        settings_data = load_json_file('settings.json')
        
        # حساب الإحصائيات
        total_users = len(bitcoin_data)
        total_balance = sum(user.get('balance', 0) for user in bitcoin_data.values())
        total_levels = sum(len(guild) for guild in levels_data.values())
        total_fizzy = sum(user.get('fizzy', 0) for user in games_data.values())
        
        # بيانات للرسم البياني (محاكاة)
        chart_data = {
            'labels': ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'],
            'datasets': [{
                'label': 'النشاط اليومي',
                'data': [random.randint(50, 200) for _ in range(7)],
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgba(54, 162, 235, 1)',
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
    """قائمة المستخدمين"""
    try:
        users = get_all_users()
        
        # تحويل إلى قائمة
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
        
        return jsonify({
            'success': True,
            'data': users_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/economy')
@login_required
def api_economy():
    """بيانات الاقتصاد"""
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        
        # حساب الإحصائيات
        total_balance = sum(user.get('balance', 0) for user in bitcoin_data.values())
        total_earned = sum(user.get('total_earned', 0) for user in bitcoin_data.values())
        total_spent = sum(user.get('total_spent', 0) for user in bitcoin_data.values())
        
        # آخر المعاملات
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
        
        # ترتيب حسب الوقت
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

@app.route('/api/commands/toggle', methods=['POST'])
@login_required
def api_toggle_command():
    """تفعيل/تعطيل أمر"""
    try:
        data = request.get_json()
        command_name = data.get('command')
        enabled = data.get('enabled')
        
        settings_data = load_json_file('settings.json')
        
        # تحديث الإعدادات
        if 'disabled_commands' not in settings_data:
            settings_data['disabled_commands'] = []
        
        if enabled:
            # تفعيل الأمر
            if command_name in settings_data['disabled_commands']:
                settings_data['disabled_commands'].remove(command_name)
        else:
            # تعطيل الأمر
            if command_name not in settings_data['disabled_commands']:
                settings_data['disabled_commands'].append(command_name)
        
        save_json_file('settings.json', settings_data)
        
        return jsonify({
            'success': True,
            'message': f'تم {"تفعيل" if enabled else "تعطيل"} الأمر {command_name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>/balance', methods=['POST'])
@login_required
def api_update_balance(user_id):
    """تعديل رصيد Bitcoin لعضو"""
    try:
        data = request.get_json()
        new_balance = int(data.get('balance', 0))
        
        bitcoin_data = load_json_file('bitcoin.json')
        
        if user_id not in bitcoin_data:
            bitcoin_data[user_id] = {
                'balance': 0,
                'total_earned': 0,
                'total_spent': 0,
                'last_daily': None,
                'last_work': None,
                'transactions': [],
                'inventory': []
            }
        
        old_balance = bitcoin_data[user_id].get('balance', 0)
        bitcoin_data[user_id]['balance'] = new_balance
        
        # إضافة معاملة
        transaction = {
            'type': 'admin',
            'amount': new_balance - old_balance,
            'description': 'تعديل من Dashboard',
            'timestamp': datetime.now().isoformat()
        }
        bitcoin_data[user_id]['transactions'].append(transaction)
        
        save_json_file('bitcoin.json', bitcoin_data)
        
        return jsonify({
            'success': True,
            'message': f'تم تحديث رصيد المستخدم {user_id} إلى {new_balance}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
@login_required
def api_logs():
    """جلب السجلات"""
    try:
        bitcoin_data = load_json_file('bitcoin.json')
        
        # تجميع كل المعاملات
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
        
        # ترتيب حسب الوقت
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': all_logs[:100]  # آخر 100 سجل
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    """جلب/تحديث الإعدادات"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            settings_data = load_json_file('settings.json')
            
            # تحديث الإعدادات
            settings_data.update(data)
            save_json_file('settings.json', settings_data)
            
            return jsonify({
                'success': True,
                'message': 'تم حفظ الإعدادات بنجاح'
            })
        else:
            settings_data = load_json_file('settings.json')
            return jsonify({
                'success': True,
                'data': settings_data
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/commands')
@login_required
def api_commands():
    """قائمة الأوامر"""
    try:
        # قائمة الأوامر المتاحة
        commands_list = [
            {'name': 'rank', 'description': 'عرض المستوى', 'category': 'levels', 'enabled': True},
            {'name': 'top', 'description': 'أفضل 10 أعضاء', 'category': 'levels', 'enabled': True},
            {'name': 'balance', 'description': 'عرض الرصيد', 'category': 'economy', 'enabled': True},
            {'name': 'daily', 'description': 'المكافأة اليومية', 'category': 'economy', 'enabled': True},
            {'name': 'work', 'description': 'العمل', 'category': 'economy', 'enabled': True},
            {'name': 'transfer', 'description': 'تحويل Bitcoin', 'category': 'economy', 'enabled': True},
            {'name': 'game', 'description': 'الألعاب', 'category': 'games', 'enabled': True},
            {'name': 'fizzy', 'description': 'رصيد Fizzy', 'category': 'games', 'enabled': True},
            {'name': 'play', 'description': 'تشغيل موسيقى', 'category': 'music', 'enabled': True},
            {'name': 'pause', 'description': 'إيقاف مؤقت', 'category': 'music', 'enabled': True},
            {'name': 'skip', 'description': 'تخطي', 'category': 'music', 'enabled': True},
            {'name': 'ticket', 'description': 'فتح تذكرة', 'category': 'tickets', 'enabled': True},
            {'name': 'close', 'description': 'إغلاق التذكرة', 'category': 'tickets', 'enabled': True},
            {'name': 'invites', 'description': 'عدد الدعوات', 'category': 'invites', 'enabled': True},
            {'name': 'ai ask', 'description': 'سؤال للذكاء الاصطناعي', 'category': 'ai', 'enabled': True},
            {'name': 'ai imagine', 'description': 'توليد صورة', 'category': 'ai', 'enabled': True},
        ]
        
        # التحقق من الأوامر المعطلة
        settings_data = load_json_file('settings.json')
        disabled = settings_data.get('disabled_commands', [])
        
        for cmd in commands_list:
            cmd['enabled'] = cmd['name'] not in disabled
        
        return jsonify({
            'success': True,
            'data': commands_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =================== تشغيل التطبيق ===================

if __name__ == '__main__':
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    print(f"🚀 Dashboard يعمل على: http://localhost:{port}")
    print(f"🔐 كلمة السر: {os.getenv('DASHBOARD_PASSWORD', 'admin123')}")
    app.run(host='0.0.0.0', port=port, debug=True)