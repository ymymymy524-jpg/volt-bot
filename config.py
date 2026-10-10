import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env الموجود في نفس المجلد
load_dotenv()

# ==========================================
# ⚙️ إعدادات البوت الأساسية
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ==========================================
# 🌐 إعدادات لوحة التحكم (Dashboard)
# ==========================================
DASHBOARD_SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "super_secret_key_change_me_in_production")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 5000))

# ==========================================
# 🛠️ إعدادات التطوير (مزامنة الأوامر)
# ==========================================
# معرف سيرفر الاختبار (اختياري). 
# إذا تم وضعه، سيتم مزامنة الأوامر فوراً في هذا السيرفر فقط لتسريع التطوير.
# اتركه فارغاً "" في ملف .env لمزامنة الأوامر عالمياً (Global Sync).
TEST_GUILD_ID_STR = os.getenv("TEST_GUILD_ID", "")
TEST_GUILD_ID = int(TEST_GUILD_ID_STR) if TEST_GUILD_ID_STR.isdigit() else None

# ==========================================
# 🎨 ألوان الـ Embeds المستخدمة في البوت
# ==========================================
class Colors:
    FUN = 0x9B59B6      # بنفسجي (للألعاب والمرح)
    SUCCESS = 0x2ECC71  # أخضر زمردي (لعمليات النجاح)
    ERROR = 0xE74C3C    # أحمر (للأخطاء والتحذيرات الحرجة)
    INFO = 0x3498DB     # أزرق فاتح (للمعلومات العامة)
    WARNING = 0xF1C40F  # أصفر (للتحذيرات والتنبيهات)
    GOLD = 0xF39C12     # ذهبي (للاقتصاد، المستويات، والمكافآت)