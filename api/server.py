"""
═══════════════════════════════════════════════════════════
🌐 Volt System API Server
═══════════════════════════════════════════════════════════
بيشتغل مع البوت على Railway عشان الـ Dashboard يقدر يتحكم فيه
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
import uvicorn

# ═══════════════════════════════════════
# 🔐 الإعدادات
# ═══════════════════════════════════════
API_SECRET = os.getenv("BOT_API_SECRET", "volt_secret_2024")


# ═══════════════════════════════════════
# 🔐 Authentication
# ═══════════════════════════════════════
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "").strip()
    if token != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


# ═══════════════════════════════════════
# 📦 Models
# ═══════════════════════════════════════
class BulkShortcutsUpdate(BaseModel):
    shortcuts: Dict[str, Dict[str, Any]]


class SingleShortcutUpdate(BaseModel):
    shortcut: str
    enabled: bool = True


# ═══════════════════════════════════════
# 🚀 إنشاء التطبيق
# ═══════════════════════════════════════
def create_app(bot):
    app = FastAPI(title="Volt System API", version="1.0")

    # CORS - عشان الـ Dashboard على Render يقدر يتواصل
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ═══════════════════════════════════════
    # 🏠 Root & Health
    # ═══════════════════════════════════════
    @app.get("/")
    async def root():
        return {
            "status": "online",
            "bot": str(bot.user),
            "guilds": len(bot.guilds)
        }

    @app.get("/api/health")
    async def health():
        return {
            "status": "healthy",
            "bot": str(bot.user),
            "guilds": len(bot.guilds),
            "users": sum(g.member_count or 0 for g in bot.guilds),
            "latency_ms": round(bot.latency * 1000),
        }

    # ═══════════════════════════════════════
    # 📋 Shortcuts Endpoints
    # ═══════════════════════════════════════
    @app.get("/api/shortcuts")
    async def get_shortcuts(auth: bool = Depends(verify_token)):
        """جلب كل الاختصارات"""
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")
        return cog.get_all_shortcuts()

    # ⭐⭐⭐ الأهم - زر Apply ⭐⭐⭐
    @app.post("/api/shortcuts/apply")
    async def apply_shortcuts(
        data: BulkShortcutsUpdate,
        auth: bool = Depends(verify_token)
    ):
        """
        ⭐ زر Apply - بيحفظ الاختصارات + reload فوري

        العملية:
        1. يتحقق من التوكن
        2. ينادي cog.bulk_update() اللي بتحفظ + reload
        3. الاختصارات الجديدة شغالة فوراً ⚡
        """
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")

        try:
            count = cog.bulk_update(data.shortcuts)
            return {
                "status": "ok",
                "message": f"✅ تم تطبيق {count} اختصار، البوت اتحدّث فوراً",
                "count": count,
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"خطأ: {e}")

    @app.put("/api/shortcuts/{command_name}")
    async def update_single(
        command_name: str,
        data: SingleShortcutUpdate,
        auth: bool = Depends(verify_token)
    ):
        """تحديث اختصار واحد"""
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")

        try:
            cog.update_shortcut(command_name, data.shortcut, data.enabled)
            return {"status": "ok", "command": command_name}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/api/shortcuts/{command_name}")
    async def delete_shortcut(
        command_name: str,
        auth: bool = Depends(verify_token)
    ):
        """حذف اختصار"""
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")

        if cog.delete_shortcut(command_name):
            return {"status": "ok", "command": command_name}
        raise HTTPException(status_code=404, detail="الأمر مش موجود")

    # ═══════════════════════════════════════
    # 🔄 Reload يدوي
    # ═══════════════════════════════════════
    @app.post("/api/reload")
    async def reload_all(auth: bool = Depends(verify_token)):
        """إعادة تحميل الاختصارات يدوياً"""
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")

        count = cog.reload_shortcuts()
        return {"status": "ok", "count": count, "message": f"تم reload {count} اختصار"}

    # ═══════════════════════════════════════
    # 📊 Stats
    # ═══════════════════════════════════════
    @app.get("/api/stats")
    async def stats(auth: bool = Depends(verify_token)):
        """إحصائيات البوت"""
        return {
            "bot_name": str(bot.user),
            "bot_id": bot.user.id,
            "guilds": len(bot.guilds),
            "users": sum(g.member_count or 0 for g in bot.guilds),
            "latency_ms": round(bot.latency * 1000),
            "cogs": list(bot.cogs.keys()),
        }

    return app


# ═══════════════════════════════════════
# 🎬 تشغيل الـ API
# ═══════════════════════════════════════
async def run_api(bot, host="0.0.0.0", port=None):
    """تشغيل الـ FastAPI مع البوت"""
    if port is None:
        port = int(os.getenv("PORT", 8080))

    app = create_app(bot)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    print(f"🌐 API شغال على http://{host}:{port}")
    await server.serve()