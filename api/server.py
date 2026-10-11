"""
═══════════════════════════════════════════════════════════
🌐 Volt System API Server
═══════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
import uvicorn

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
# 🚀 Create App
# ═══════════════════════════════════════
def create_app(bot):
    app = FastAPI(title="Volt System API", version="1.0")

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
            "guilds": len(bot.guilds),
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
    # 🏰 Guilds Endpoints
    # ═══════════════════════════════════════
    @app.get("/api/guilds")
    async def get_all_guilds(auth: bool = Depends(verify_token)):
        """كل السيرفرات اللي البوت فيها"""
        return {
            "guilds": [
                {
                    "id": str(g.id),
                    "name": g.name,
                    "icon": g.icon.url if g.icon else None,
                    "member_count": g.member_count or 0,
                    "owner_id": str(g.owner_id) if g.owner_id else None,
                }
                for g in bot.guilds
            ]
        }

    @app.get("/api/guilds/{guild_id}")
    async def get_guild_info(guild_id: str):
        """معلومات سيرفر معين"""
        try:
            guild = bot.get_guild(int(guild_id))
            
            if not guild:
                # نحاول نجيبه من Discord
                try:
                    guild = await bot.fetch_guild(int(guild_id))
                except Exception:
                    raise HTTPException(status_code=404, detail="Server not found")
            
            return {
                "guild": {
                    "id": str(guild.id),
                    "name": guild.name,
                    "icon": guild.icon.url if guild.icon else None,
                    "member_count": guild.member_count or 0,
                    "owner_id": str(guild.owner_id) if guild.owner_id else None,
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # 📋 Shortcuts Endpoints
    # ═══════════════════════════════════════
    @app.get("/api/shortcuts")
    async def get_shortcuts(auth: bool = Depends(verify_token)):
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")
        return cog.get_all_shortcuts()

    @app.post("/api/shortcuts/apply")
    async def apply_shortcuts(
        data: BulkShortcutsUpdate,
        auth: bool = Depends(verify_token)
    ):
        """⭐ زر Apply - تحديث الاختصارات + reload فوري"""
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
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")
        if cog.delete_shortcut(command_name):
            return {"status": "ok", "command": command_name}
        raise HTTPException(status_code=404, detail="الأمر مش موجود")

    @app.post("/api/reload")
    async def reload_all(auth: bool = Depends(verify_token)):
        cog = bot.get_cog("Shortcuts")
        if not cog:
            raise HTTPException(status_code=500, detail="Shortcuts cog مش محمّل")
        count = cog.reload_shortcuts()
        return {"status": "ok", "count": count}

    @app.get("/api/stats")
    async def stats(auth: bool = Depends(verify_token)):
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