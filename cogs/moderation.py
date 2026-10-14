import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import timedelta
from config import Colors


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"
        self._load_warnings()

    def _load_warnings(self):
        if os.path.exists(self.warnings_file):
            with open(self.warnings_file, "r", encoding="utf-8") as f:
                self.warnings = json.load(f)
        else:
            self.warnings = {}

    def _save_warnings(self):
        with open(self.warnings_file, "w", encoding="utf-8") as f:
            json.dump(self.warnings, f, ensure_ascii=False, indent=2)

    @commands.hybrid_command(name="ban", aliases=["حظر"], description="🔨 حظر عضو")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="العضو", reason="السبب")
    async def ban(self, ctx, member: discord.Member, *, reason: str = "لا يوجد سبب"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ لا يمكنك حظر عضو رتبته مساوية أو أعلى من رتبتك!")
            return
        try:
            await member.ban(reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(title="✅ تم الحظر", description=f"🔨 **{member.mention}** تم حظره\n**السبب:** {reason}", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ban-all", aliases=["ball", "حظر-الكل"], description="🔨 حظر جماعي")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(role="الرتبة", reason="السبب")
    async def ban_all(self, ctx, role: discord.Role, *, reason: str = "لا يوجد سبب"):
        msg = await ctx.send("⏳ جاري الحظر الجماعي...")
        banned = failed = 0
        for member in role.members:
            if member.top_role < ctx.guild.me.top_role and not member.bot:
                try:
                    await member.ban(reason=f"{ctx.author} | {reason}")
                    banned += 1
                except:
                    failed += 1
        embed = discord.Embed(title="✅ تم", description=f"🔨 رتبة **{role.name}**\n✅ نجح: `{banned}`\n❌ فشل: `{failed}`", color=Colors.SUCCESS)
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="unban", aliases=["فك-الحظر"], description="🔓 فك حظر")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="آيدي العضو", reason="السبب")
    async def unban(self, ctx, user_id: str, *, reason: str = "لا يوجد سبب"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user, reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(title="✅ تم", description=f"🔓 **{user}** تم فك حظره", color=Colors.SUCCESS)
        except discord.NotFound:
            embed = discord.Embed(title="❌ فشل", description="العضو غير محظور", color=Colors.ERROR)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kick", aliases=["طرد"], description="👢 طرد عضو")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="العضو", reason="السبب")
    async def kick(self, ctx, member: discord.Member, *, reason: str = "لا يوجد سبب"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ لا يمكنك طرد عضو رتبته أعلى منك!")
            return
        try:
            await member.kick(reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(title="✅ تم الطرد", description=f"👢 **{member.mention}** تم طرده\n**السبب:** {reason}", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_group(name="warn", aliases=["انذار", "تحذير"], description="⚠️ أوامر الإنذارات", invoke_without_command=True)
    @commands.has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    async def warn_group(self, ctx):
        embed = discord.Embed(title="⚠️ أوامر الإنذارات", description="`!warn add @عضو سبب`\n`!warn list @عضو`\n`!warn clear @عضو`", color=Colors.WARNING)
        await ctx.send(embed=embed)

    @warn_group.command(name="add", aliases=["+"], description="⚠️ إضافة إنذار")
    @app_commands.describe(member="العضو", reason="السبب")
    async def warn_add(self, ctx, member: discord.Member, *, reason: str):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        self.warnings.setdefault(guild_id, {}).setdefault(user_id, [])
        self.warnings[guild_id][user_id].append({"moderator": str(ctx.author), "reason": reason, "date": discord.utils.utcnow().isoformat()})
        self._save_warnings()
        total = len(self.warnings[guild_id][user_id])
        embed = discord.Embed(title="✅ تم الإنذار", description=f"⚠️ **{member.mention}** حصل على إنذار\n**السبب:** {reason}\n**العدد:** `{total}`", color=Colors.WARNING)
        await ctx.send(embed=embed)

    @warn_group.command(name="list", aliases=["ls"], description="📋 عرض الإنذارات")
    @app_commands.describe(member="العضو")
    async def warn_list(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        warnings = self.warnings.get(guild_id, {}).get(user_id, [])
        if not warnings:
            embed = discord.Embed(title="📋 الإنذارات", description=f"✅ **{member.mention}** ليس لديه إنذارات", color=Colors.SUCCESS)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title=f"📋 إنذارات {member.display_name}", description=f"إجمالي: `{len(warnings)}`", color=Colors.WARNING)
        for i, w in enumerate(warnings[:25], 1):
            embed.add_field(name=f"#{i} - {w['date'][:10]}", value=f"**السبب:** {w['reason']}\n**بواسطة:** {w['moderator']}", inline=False)
        await ctx.send(embed=embed)

    @warn_group.command(name="clear", aliases=["reset"], description="🗑️ مسح الإنذارات")
    @app_commands.describe(member="العضو")
    async def warn_clear(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        if guild_id in self.warnings and user_id in self.warnings[guild_id]:
            del self.warnings[guild_id][user_id]
            self._save_warnings()
        embed = discord.Embed(title="✅ تم المسح", description=f"🗑️ تم مسح إنذارات **{member.mention}**", color=Colors.SUCCESS)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="mute", aliases=["كتم"], description="🔇 كتم عضو")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو", duration="المدة بالدقائق", reason="السبب")
    async def mute(self, ctx, member: discord.Member, duration: int = 60, *, reason: str = "لا يوجد سبب"):
        try:
            await member.timeout(timedelta(minutes=duration), reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(title="✅ تم الكتم", description=f"🔇 **{member.mention}** لمدة `{duration}` دقيقة\n**السبب:** {reason}", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unmute", aliases=["فك-الكتم"], description="🔊 فك الكتم")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو")
    async def unmute(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            embed = discord.Embed(title="✅ تم", description=f"🔊 **{member.mention}** تم فك كتمه", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="timeout", aliases=["توقيت"], description="⏱️ توقيت عضو")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو", hours="ساعات", minutes="دقائق", reason="السبب")
    async def timeout_set(self, ctx, member: discord.Member, hours: int = 0, minutes: int = 0, *, reason: str = "لا يوجد سبب"):
        total = hours * 60 + minutes
        if total <= 0:
            await ctx.send("❌ حدد مدة صحيحة!")
            return
        try:
            await member.timeout(timedelta(minutes=total), reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(title="✅ تم التوقيت", description=f"⏱️ **{member.mention}** لمدة `{hours}h {minutes}m`", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="untimeout", aliases=["الغاء-التوقيت"], description="⏱️ إلغاء التوقيت")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو")
    async def untimeout(self, ctx, member: discord.Member):
        try:
            await member.timeout(None)
            embed = discord.Embed(title="✅ تم", description=f"⏱️ تم إلغاء توقيت **{member.mention}**", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clear", aliases=["مسح", "purge"], description="🧹 مسح رسائل")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="العدد (1-1000)", member="عضو معين (اختياري)")
    async def clear(self, ctx, amount: int, member: discord.Member = None):
        if amount < 1 or amount > 1000:
            await ctx.send("❌ العدد من 1 لـ 1000!")
            return
        try:
            if ctx.interaction is None:
                await ctx.message.delete()
            if member:
                deleted = await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == member.id)
            else:
                deleted = await ctx.channel.purge(limit=amount)
            embed = discord.Embed(title="✅ تم الحذف", description=f"🧹 تم حذف `{len(deleted)}` رسالة", color=Colors.SUCCESS)
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ فشل: {e}")

    @commands.hybrid_command(name="slowmode", aliases=["وضع-بطيء"], description="🐌 الوضع البطيء")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(seconds="الثواني (0-21600)")
    async def slowmode(self, ctx, seconds: int = 0):
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ من 0 لـ 21600!")
            return
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            msg = "تم إيقاف الوضع البطيء" if seconds == 0 else f"تم التعيين لـ `{seconds}` ثانية"
            embed = discord.Embed(title="✅ تم", description=f"🐌 {msg}", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lock", aliases=["قفل"], description="🔒 قفل القناة")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            embed = discord.Embed(title="✅ تم", description="🔒 تم قفل القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unlock", aliases=["فتح"], description="🔓 فتح القناة")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, ctx):
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
            embed = discord.Embed(title="✅ تم", description="🔓 تم فتح القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nick", aliases=["اسم", "لقب"], description="✏️ تغيير اللقب")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.default_permissions(manage_nicknames=True)
    @app_commands.describe(member="العضو", nickname="اللقب الجديد")
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        try:
            await member.edit(nick=nickname)
            msg = f"تم تغيير اسم **{member.mention}**" + (f" لـ `{nickname}`" if nickname else " للافتراضي")
            embed = discord.Embed(title="✅ تم", description=f"✏️ {msg}", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"{e}", color=Colors.ERROR)
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Moderation(bot))