import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import timedelta
from config import Colors

# ==========================================
# 👑 أوامر الإدارة (Moderation) - Prefix + Slash
# ==========================================

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

    # ═══════════════════════════════════════
    # 🔨 !ban / /ban
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ban",
        aliases=["b", "حظر"],
        description="🔨 حظر عضو من السيرفر"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="العضو المراد حظره", reason="سبب الحظر")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "لا يوجد سبب"):
        """حظر عضو من السيرفر"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ لا يمكنك حظر عضو رتبته مساوية أو أعلى من رتبتك!")
            return

        try:
            await member.ban(reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ تم الحظر بنجاح",
                description=f"🔨 **{member.mention}** تم حظره من السيرفر\n\n**السبب:** {reason}\n**بواسطة:** {ctx.author.mention}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الحظر", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔨 !ban-all / /ban-all
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ban-all",
        aliases=["ball", "حظر-الكل"],
        description="🔨 حظر جميع الأعضاء الذين لديهم رتبة معينة"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(role="الرتبة المراد حظر أعضائها", reason="سبب الحظر")
    async def ban_all(self, ctx: commands.Context, role: discord.Role, *, reason: str = "لا يوجد سبب"):
        """حظر جميع أعضاء رتبة معينة"""
        msg = await ctx.send("⏳ جاري تنفيذ الحظر الجماعي...")

        banned = 0
        failed = 0
        for member in role.members:
            if member.top_role < ctx.guild.me.top_role and not member.bot:
                try:
                    await member.ban(reason=f"{ctx.author} | {reason}")
                    banned += 1
                except:
                    failed += 1

        embed = discord.Embed(
            title="✅ تم تنفيذ الحظر الجماعي",
            description=f"🔨 تم حظر أعضاء رتبة **{role.name}**\n\n✅ **نجح:** `{banned}`\n❌ **فشل:** `{failed}`",
            color=Colors.SUCCESS
        )
        await msg.edit(content=None, embed=embed)

    # ═══════════════════════════════════════
    # 🔓 !unban / /unban
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="unban",
        aliases=["ub", "فك-الحظر"],
        description="🔓 إلغاء حظر عضو من السيرفر"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(user_id="آيدي العضو المراد فك حظره", reason="سبب فك الحظر")
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "لا يوجد سبب"):
        """إلغاء حظر عضو"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user, reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ تم إلغاء الحظر",
                description=f"🔓 **{user}** تم إلغاء حظره من السيرفر",
                color=Colors.SUCCESS
            )
        except discord.NotFound:
            embed = discord.Embed(title="❌ فشل", description="العضو غير محظور أو المعرف خاطئ", color=Colors.ERROR)
        except ValueError:
            embed = discord.Embed(title="❌ فشل", description="آيدي غير صحيح!", color=Colors.ERROR)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👢 !kick / /kick
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="kick",
        aliases=["k", "طرد"],
        description="👢 طرد عضو من السيرفر"
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="العضو المراد طرده", reason="سبب الطرد")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "لا يوجد سبب"):
        """طرد عضو من السيرفر"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ لا يمكنك طرد عضو رتبته مساوية أو أعلى من رتبتك!")
            return

        try:
            await member.kick(reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ تم الطرد بنجاح",
                description=f"👢 **{member.mention}** تم طرده من السيرفر\n\n**السبب:** {reason}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الطرد", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⚠️ !warn / /warn (Group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(
        name="warn",
        aliases=["w", "انذار", "تحذير"],
        description="⚠️ أوامر الإنذارات",
        invoke_without_command=True
    )
    @commands.has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    async def warn_group(self, ctx: commands.Context):
        """عرض المساعدة لأوامر الإنذار"""
        embed = discord.Embed(
            title="⚠️ أوامر الإنذارات",
            description=(
                "**Slash:**\n"
                "`/warn add @عضو سبب` - إعطاء إنذار\n"
                "`/warn list @عضو` - عرض الإنذارات\n"
                "`/warn clear @عضو` - مسح الإنذارات\n\n"
                "**Prefix:**\n"
                "`!warn add @عضو سبب`\n"
                "`!warn list @عضو`\n"
                "`!warn clear @عضو`"
            ),
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)

    @warn_group.command(name="add", aliases=["+", "اضف"], description="⚠️ إعطاء إنذار لعضو")
    @app_commands.describe(member="العضو", reason="سبب الإنذار")
    async def warn_add(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """إعطاء إنذار لعضو"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []

        warn_entry = {
            "moderator": str(ctx.author),
            "reason": reason,
            "date": discord.utils.utcnow().isoformat()
        }
        self.warnings[guild_id][user_id].append(warn_entry)
        self._save_warnings()

        total = len(self.warnings[guild_id][user_id])

        embed = discord.Embed(
            title="✅ تم إعطاء الإنذار",
            description=f"⚠️ **{member.mention}** حصل على إنذار\n\n**السبب:** {reason}\n**عدد الإنذارات:** `{total}`",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)

    @warn_group.command(name="list", aliases=["ls", "عرض"], description="📋 عرض إنذارات عضو")
    @app_commands.describe(member="العضو")
    async def warn_list(self, ctx: commands.Context, member: discord.Member):
        """عرض إنذارات عضو"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        warnings = self.warnings.get(guild_id, {}).get(user_id, [])

        if not warnings:
            embed = discord.Embed(
                title="📋 إنذارات العضو",
                description=f"✅ **{member.mention}** ليس لديه أي إنذارات",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"📋 إنذارات {member.display_name}",
            description=f"إجمالي الإنذارات: `{len(warnings)}`",
            color=Colors.WARNING
        )

        for i, w in enumerate(warnings[:25], 1):
            embed.add_field(
                name=f"#{i} - {w['date'][:10]}",
                value=f"**السبب:** {w['reason']}\n**بواسطة:** {w['moderator']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @warn_group.command(name="clear", aliases=["reset", "مسح"], description="🗑️ مسح إنذارات عضو")
    @app_commands.describe(member="العضو")
    async def warn_clear(self, ctx: commands.Context, member: discord.Member):
        """مسح جميع إنذارات عضو"""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in self.warnings and user_id in self.warnings[guild_id]:
            del self.warnings[guild_id][user_id]
            self._save_warnings()

        embed = discord.Embed(
            title="✅ تم المسح",
            description=f"🗑️ تم مسح جميع إنذارات **{member.mention}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔇 !mute / /mute
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="mute",
        aliases=["m", "كتم"],
        description="🔇 كتم عضو (Timeout)"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو", duration="المدة بالدقائق", reason="السبب")
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int = 60, *, reason: str = "لا يوجد سبب"):
        """كتم عضو لمدة محددة بالدقائق"""
        try:
            await member.timeout(timedelta(minutes=duration), reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ تم الكتم",
                description=f"🔇 **{member.mention}** تم كتمه لمدة `{duration}` دقيقة\n\n**السبب:** {reason}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الكتم", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔇 !mute-all / /mute-all
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="mute-all",
        aliases=["mall", "كتم-الكل"],
        description="🔇 كتم جميع أعضاء رتبة معينة"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(role="الرتبة", duration="المدة بالدقائق")
    async def mute_all(self, ctx: commands.Context, role: discord.Role, duration: int = 60):
        """كتم جميع أعضاء رتبة"""
        msg = await ctx.send("⏳ جاري الكتم الجماعي...")
        muted = 0
        for member in role.members:
            if member.top_role < ctx.guild.me.top_role and not member.bot:
                try:
                    await member.timeout(timedelta(minutes=duration), reason=f"كتم جماعي بواسطة {ctx.author}")
                    muted += 1
                except:
                    pass

        embed = discord.Embed(
            title="✅ تم الكتم الجماعي",
            description=f"🔇 تم كتم `{muted}` عضو من رتبة **{role.name}**",
            color=Colors.SUCCESS
        )
        await msg.edit(content=None, embed=embed)

    # ═══════════════════════════════════════
    # 🔊 !unmute / /unmute
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="unmute",
        aliases=["um", "فك-الكتم"],
        description="🔊 إلغاء كتم عضو"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """إلغاء كتم عضو"""
        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="✅ تم إلغاء الكتم",
                description=f"🔊 **{member.mention}** تم إلغاء كتمه",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⏱️ !timeout / /timeout
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="timeout",
        aliases=["to", "توقيت"],
        description="⏱️ تعيين Timeout لعضو (ساعات ودقائق)"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو", hours="الساعات", minutes="الدقائق", reason="السبب")
    async def timeout_set(
        self,
        ctx: commands.Context,
        member: discord.Member,
        hours: int = 0,
        minutes: int = 0,
        *,
        reason: str = "لا يوجد سبب"
    ):
        """تعيين Timeout لعضو"""
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            await ctx.send("❌ يجب تحديد مدة صحيحة!")
            return

        try:
            await member.timeout(timedelta(minutes=total_minutes), reason=f"{ctx.author} | {reason}")
            embed = discord.Embed(
                title="✅ تم التوقيت",
                description=f"⏱️ **{member.mention}** تم توقيته لمدة `{hours}h {minutes}m`",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⏱️ !untimeout / /untimeout
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="untimeout",
        aliases=["uto", "الغاء-التوقيت"],
        description="⏱️ إلغاء Timeout لعضو"
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(member="العضو")
    async def untimeout(self, ctx: commands.Context, member: discord.Member):
        """إلغاء Timeout لعضو"""
        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="✅ تم الإلغاء",
                description=f"⏱️ تم إلغاء Timeout لـ **{member.mention}**",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎤 !voicemute / /voicemute
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="voicemute",
        aliases=["vm", "كتم-صوت"],
        description="🎤 كتم صوت عضو في القناة الصوتية"
    )
    @commands.has_permissions(mute_members=True)
    @commands.bot_has_permissions(mute_members=True)
    @app_commands.default_permissions(mute_members=True)
    @app_commands.describe(member="العضو")
    async def voice_mute(self, ctx: commands.Context, member: discord.Member):
        """كتم صوت عضو"""
        if not member.voice:
            await ctx.send("❌ العضو ليس في قناة صوتية!")
            return

        try:
            await member.edit(mute=True)
            embed = discord.Embed(
                title="✅ تم كتم الصوت",
                description=f"🎤 **{member.mention}** تم كتم صوته في القناة الصوتية",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎧 !voicedeafen / /voicedeafen
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="voicedeafen",
        aliases=["vd", "منع-السماع"],
        description="🎧 منع عضو من سماع الصوت"
    )
    @commands.has_permissions(deafen_members=True)
    @commands.bot_has_permissions(deafen_members=True)
    @app_commands.default_permissions(deafen_members=True)
    @app_commands.describe(member="العضو")
    async def voice_deafen(self, ctx: commands.Context, member: discord.Member):
        """منع عضو من سماع الصوت"""
        if not member.voice:
            await ctx.send("❌ العضو ليس في قناة صوتية!")
            return

        try:
            await member.edit(deafen=True)
            embed = discord.Embed(
                title="✅ تم منع السماع",
                description=f"🎧 **{member.mention}** تم منعه من سماع الصوت",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🧹 !clear / /clear
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="clear",
        aliases=["c", "مسح", "purge"],
        description="🧹 حذف عدد من الرسائل"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="عدد الرسائل (1-1000)", member="حذف رسائل عضو معين فقط (اختياري)")
    async def clear(self, ctx: commands.Context, amount: int, member: discord.Member = None):
        """حذف عدد من الرسائل"""
        if amount < 1 or amount > 1000:
            await ctx.send("❌ العدد لازم يكون بين **1** و **1000**!")
            return

        try:
            # في Slash مش بنقدر نحذف رسالة الأمر
            if ctx.interaction is None:
                await ctx.message.delete()

            if member:
                def check(m): return m.author.id == member.id
                deleted = await ctx.channel.purge(limit=amount, check=check)
            else:
                deleted = await ctx.channel.purge(limit=amount)

            embed = discord.Embed(
                title="✅ تم الحذف",
                description=f"🧹 تم حذف `{len(deleted)}` رسالة",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ فشل: {e}")

    # ═══════════════════════════════════════
    # 🐌 !slowmode / /slowmode
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="slowmode",
        aliases=["sm", "وضع-بطيء"],
        description="🐌 تعيين الوضع البطيء للقناة"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(seconds="عدد الثواني (0-21600)")
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        """تعيين الوضع البطيء"""
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ المدة لازم تكون بين **0** و **21600** ثانية!")
            return

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                msg = "🐌 تم إيقاف الوضع البطيء"
            else:
                msg = f"🐌 تم تعيين الوضع البطيء إلى `{seconds}` ثانية"

            embed = discord.Embed(title="✅ تم", description=msg, color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔒 !lock / /lock
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="lock",
        aliases=["l", "قفل"],
        description="🔒 قفل القناة"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        """قفل القناة"""
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
            embed = discord.Embed(title="✅ تم القفل", description="🔒 تم قفل القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔓 !unlock / /unlock
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="unlock",
        aliases=["ul", "فتح"],
        description="🔓 فتح القناة"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """فتح القناة"""
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
            embed = discord.Embed(title="✅ تم الفتح", description="🔓 تم فتح القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👻 !hide / /hide
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="hide",
        aliases=["اخفاء"],
        description="👻 إخفاء القناة"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def hide(self, ctx: commands.Context):
        """إخفاء القناة"""
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
            embed = discord.Embed(title="✅ تم الإخفاء", description="👻 تم إخفاء القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👁️ !unhide / /unhide
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="unhide",
        aliases=["اظهار"],
        description="👁️ إظهار القناة"
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    async def unhide(self, ctx: commands.Context):
        """إظهار القناة"""
        try:
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=None)
            embed = discord.Embed(title="✅ تم الإظهار", description="👁️ تم إظهار القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔀 !move / /move
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="move",
        aliases=["نقل"],
        description="🔀 نقل عضو لقناة صوتية"
    )
    @commands.has_permissions(move_members=True)
    @commands.bot_has_permissions(move_members=True)
    @app_commands.default_permissions(move_members=True)
    @app_commands.describe(member="العضو", channel="القناة الصوتية")
    async def move(self, ctx: commands.Context, member: discord.Member, channel: discord.VoiceChannel):
        """نقل عضو لقناة صوتية"""
        if not member.voice:
            await ctx.send("❌ العضو ليس في قناة صوتية!")
            return

        try:
            await member.move_to(channel)
            embed = discord.Embed(
                title="✅ تم النقل",
                description=f"🔀 **{member.mention}** تم نقله إلى **{channel.mention}**",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ✏️ !nick / /nick
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="nick",
        aliases=["n", "اسم", "لقب"],
        description="✏️ تغيير اسم عضو في السيرفر"
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.default_permissions(manage_nicknames=True)
    @app_commands.describe(member="العضو", nickname="اللقب الجديد (اتركه فارغ لإعادة الاسم الأصلي)")
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = None):
        """تغيير اسم عضو"""
        try:
            await member.edit(nick=nickname)
            if nickname:
                msg = f"✏️ تم تغيير اسم **{member.mention}** إلى `{nickname}`"
            else:
                msg = f"✏️ تم إعادة اسم **{member.mention}** للافتراضي"
            embed = discord.Embed(title="✅ تم", description=msg, color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)

        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error):
        """معالجة شاملة لكل أخطاء الـ Cog"""
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ مفيش عندك الصلاحيات دي: `{perms}`", delete_after=8)
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ البوت مفيش عنده الصلاحيات دي: `{perms}`", delete_after=8)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو ده في السيرفر!", delete_after=8)
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة دي!", delete_after=8)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة دي!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))