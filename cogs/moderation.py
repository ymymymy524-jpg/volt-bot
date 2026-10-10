import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import timedelta
from config import Colors

# ==========================================
# 👑 أوامر الإدارة (Moderation Commands)
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

    # ==========================================
    # 🔨 مجموعة أوامر الحظر (Ban Group)
    # ==========================================
    ban_group = app_commands.Group(
        name="ban",
        description="🔨 أوامر الحظر",
        default_permissions=discord.Permissions(ban_members=True)
    )

    @ban_group.command(name="user", description="🔨 حظر عضو من السيرفر")
    @app_commands.describe(member="العضو المراد حظره", reason="سبب الحظر")
    async def ban_user(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ لا يمكنك حظر عضو رتبته مساوية أو أعلى من رتبتك!", ephemeral=True)
            return
        
        try:
            await member.ban(reason=f"{interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ تم الحظر بنجاح",
                description=f"🔨 **{member.mention}** تم حظره من السيرفر\n\n**السبب:** {reason}\n**بواسطة:** {interaction.user.mention}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الحظر", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @ban_group.command(name="all", description="🔨 حظر جميع الأعضاء الذين لديهم رتبة معينة")
    @app_commands.describe(role="الرتبة التي سيتم حظر أعضائها", reason="سبب الحظر")
    async def ban_all(self, interaction: discord.Interaction, role: discord.Role, reason: str = "لا يوجد سبب"):
        await interaction.response.defer(ephemeral=True)
        
        banned = 0
        failed = 0
        for member in role.members:
            if member.top_role < interaction.guild.me.top_role and not member.bot:
                try:
                    await member.ban(reason=f"{interaction.user} | {reason}")
                    banned += 1
                except:
                    failed += 1
        
        embed = discord.Embed(
            title="✅ تم تنفيذ الحظر الجماعي",
            description=f"🔨 تم حظر أعضاء رتبة **{role.name}**\n\n✅ **نجح:** `{banned}`\n❌ **فشل:** `{failed}`",
            color=Colors.SUCCESS
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unban", description="🔓 إلغاء حظر عضو من السيرفر")
    @app_commands.describe(user_id="معرف العضو المراد إلغاء حظره", reason="سبب إلغاء الحظر")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "لا يوجد سبب"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ تم إلغاء الحظر",
                description=f"🔓 **{user}** تم إلغاء حظره من السيرفر",
                color=Colors.SUCCESS
            )
        except discord.NotFound:
            embed = discord.Embed(title="❌ فشل", description="العضو غير محظور أو المعرف خاطئ", color=Colors.ERROR)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 👢 أمر الطرد
    # ==========================================
    @app_commands.command(name="kick", description="👢 طرد عضو من السيرفر")
    @app_commands.describe(member="العضو المراد طرده", reason="سبب الطرد")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ لا يمكنك طرد عضو رتبته مساوية أو أعلى من رتبتك!", ephemeral=True)
            return
        
        try:
            await member.kick(reason=f"{interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ تم الطرد بنجاح",
                description=f"👢 **{member.mention}** تم طرده من السيرفر\n\n**السبب:** {reason}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الطرد", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # ⚠️ مجموعة أوامر الإنذارات (Warn Group)
    # ==========================================
    warn_group = app_commands.Group(
        name="warn",
        description="⚠️ أوامر الإنذارات",
        default_permissions=discord.Permissions(moderate_members=True)
    )

    @warn_group.command(name="add", description="⚠️ إعطاء إنذار لعضو")
    @app_commands.describe(member="العضو المراد إنذاره", reason="سبب الإنذار")
    async def warn_add(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []
        
        warn_entry = {
            "moderator": str(interaction.user),
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
        await interaction.response.send_message(embed=embed)

    @warn_group.command(name="list", description="📋 عرض إنذارات عضو")
    @app_commands.describe(member="العضو المراد عرض إنذاراته")
    async def warn_list(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        warnings = self.warnings.get(guild_id, {}).get(user_id, [])
        
        if not warnings:
            embed = discord.Embed(
                title="📋 إنذارات العضو",
                description=f"✅ **{member.mention}** ليس لديه أي إنذارات",
                color=Colors.SUCCESS
            )
            await interaction.response.send_message(embed=embed)
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
        
        await interaction.response.send_message(embed=embed)

    @warn_group.command(name="clear", description="🗑️ مسح إنذارات عضو")
    @app_commands.describe(member="العضو المراد مسح إنذاراته")
    async def warn_clear(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.warnings and user_id in self.warnings[guild_id]:
            del self.warnings[guild_id][user_id]
            self._save_warnings()
        
        embed = discord.Embed(
            title="✅ تم المسح",
            description=f"🗑️ تم مسح جميع إنذارات **{member.mention}**",
            color=Colors.SUCCESS
        )
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 🔇 مجموعة أوامر الكتم (Mute Group)
    # ==========================================
    mute_group = app_commands.Group(
        name="mute",
        description="🔇 أوامر الكتم",
        default_permissions=discord.Permissions(moderate_members=True)
    )

    @mute_group.command(name="user", description="🔇 كتم عضو (Timeout)")
    @app_commands.describe(member="العضو المراد كتمه", duration="المدة بالدقائق", reason="سبب الكتم")
    async def mute_user(self, interaction: discord.Interaction, member: discord.Member, duration: int = 60, reason: str = "لا يوجد سبب"):
        try:
            await member.timeout(timedelta(minutes=duration), reason=f"{interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ تم الكتم",
                description=f"🔇 **{member.mention}** تم كتمه لمدة `{duration}` دقيقة\n\n**السبب:** {reason}",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل الكتم", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @mute_group.command(name="all", description="🔇 كتم جميع أعضاء رتبة معينة")
    @app_commands.describe(role="الرتبة المراد كتم أعضائها", duration="المدة بالدقائق")
    async def mute_all(self, interaction: discord.Interaction, role: discord.Role, duration: int = 60):
        await interaction.response.defer(ephemeral=True)
        muted = 0
        for member in role.members:
            if member.top_role < interaction.guild.me.top_role and not member.bot:
                try:
                    await member.timeout(timedelta(minutes=duration), reason=f"كتم جماعي بواسطة {interaction.user}")
                    muted += 1
                except:
                    pass
        
        embed = discord.Embed(
            title="✅ تم الكتم الجماعي",
            description=f"🔇 تم كتم `{muted}` عضو من رتبة **{role.name}**",
            color=Colors.SUCCESS
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unmute", description="🔊 إلغاء كتم عضو")
    @app_commands.describe(member="العضو المراد إلغاء كتمه")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="✅ تم إلغاء الكتم",
                description=f"🔊 **{member.mention}** تم إلغاء كتمه",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # ⏱️ مجموعة أوامر Timeout
    # ==========================================
    timeout_group = app_commands.Group(
        name="timeout",
        description="⏱️ أوامر التوقيت",
        default_permissions=discord.Permissions(moderate_members=True)
    )

    @timeout_group.command(name="set", description="⏱️ تعيين Timeout لعضو")
    @app_commands.describe(member="العضو", hours="الساعات", minutes="الدقائق", reason="السبب")
    async def timeout_set(self, interaction: discord.Interaction, member: discord.Member, hours: int = 0, minutes: int = 0, reason: str = "لا يوجد سبب"):
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            await interaction.response.send_message("❌ يجب تحديد مدة صحيحة!", ephemeral=True)
            return
        
        try:
            await member.timeout(timedelta(minutes=total_minutes), reason=f"{interaction.user} | {reason}")
            embed = discord.Embed(
                title="✅ تم التوقيت",
                description=f"⏱️ **{member.mention}** تم توقيته لمدة `{hours}h {minutes}m`",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="untimeout", description="⏱️ إلغاء Timeout لعضو")
    @app_commands.describe(member="العضو")
    @app_commands.default_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None)
            embed = discord.Embed(
                title="✅ تم الإلغاء",
                description=f"⏱️ تم إلغاء Timeout لـ **{member.mention}**",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 🎤 أوامر كتم الصوت
    # ==========================================
    @app_commands.command(name="voice-mute", description="🎤 كتم صوت عضو في القناة الصوتية")
    @app_commands.describe(member="العضو المراد كتم صوته")
    @app_commands.default_permissions(mute_members=True)
    async def voice_mute(self, interaction: discord.Interaction, member: discord.Member):
        if not member.voice:
            await interaction.response.send_message("❌ العضو ليس في قناة صوتية!", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="voice-deafen", description="🎧 منع عضو من سماع الصوت في القناة")
    @app_commands.describe(member="العضو")
    @app_commands.default_permissions(mute_members=True)
    async def voice_deafen(self, interaction: discord.Interaction, member: discord.Member):
        if not member.voice:
            await interaction.response.send_message("❌ العضو ليس في قناة صوتية!", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 🧹 مجموعة أوامر القنوات
    # ==========================================
    channel_group = app_commands.Group(
        name="channel",
        description="🧹 أوامر إدارة القنوات",
        default_permissions=discord.Permissions(manage_channels=True)
    )

    @channel_group.command(name="clear", description="🧹 حذف عدد من الرسائل من القناة")
    @app_commands.describe(amount="عدد الرسائل (1-1000)", member="حذف رسائل عضو معين فقط")
    async def channel_clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 1000], member: discord.Member = None):
        await interaction.response.defer(ephemeral=True)
        
        try:
            if member:
                def check(m): return m.author.id == member.id
                deleted = await interaction.channel.purge(limit=amount, check=check)
            else:
                deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="✅ تم الحذف",
                description=f"🧹 تم حذف `{len(deleted)}` رسالة",
                color=Colors.SUCCESS
            )
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @channel_group.command(name="slowmode", description="🐌 تعيين الوضع البطيء للقناة")
    @app_commands.describe(seconds="المدة بالثواني (0 لإيقاف)")
    async def channel_slowmode(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600]):
        try:
            await interaction.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                msg = "🐌 تم إيقاف الوضع البطيء"
            else:
                msg = f"🐌 تم تعيين الوضع البطيء إلى `{seconds}` ثانية"
            
            embed = discord.Embed(title="✅ تم", description=msg, color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @channel_group.command(name="lock", description="🔒 قفل القناة")
    async def channel_lock(self, interaction: discord.Interaction):
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
            embed = discord.Embed(title="✅ تم القفل", description="🔒 تم قفل القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @channel_group.command(name="unlock", description="🔓 فتح القناة")
    async def channel_unlock(self, interaction: discord.Interaction):
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
            embed = discord.Embed(title="✅ تم الفتح", description="🔓 تم فتح القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @channel_group.command(name="hide", description="👻 إخفاء القناة")
    async def channel_hide(self, interaction: discord.Interaction):
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
            embed = discord.Embed(title="✅ تم الإخفاء", description="👻 تم إخفاء القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @channel_group.command(name="unhide", description="👁️ إظهار القناة")
    async def channel_unhide(self, interaction: discord.Interaction):
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=None)
            embed = discord.Embed(title="✅ تم الإظهار", description="👁️ تم إظهار القناة", color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)

    @channel_group.command(name="move", description="🔀 نقل عضو لقناة صوتية")
    @app_commands.describe(member="العضو المراد نقله", channel="القناة الصوتية الهدف")
    async def channel_move(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice:
            await interaction.response.send_message("❌ العضو ليس في قناة صوتية!", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 👤 أوامر إدارة الأعضاء
    # ==========================================
    @app_commands.command(name="nick", description="✏️ تغيير اسم عضو في السيرفر")
    @app_commands.describe(member="العضو", nickname="الاسم الجديد (اتركه فارغاً للإعادة)")
    @app_commands.default_permissions(manage_nicknames=True)
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        try:
            await member.edit(nick=nickname)
            if nickname:
                msg = f"✏️ تم تغيير اسم **{member.mention}** إلى `{nickname}`"
            else:
                msg = f"✏️ تم إعادة اسم **{member.mention}** للافتراضي"
            embed = discord.Embed(title="✅ تم", description=msg, color=Colors.SUCCESS)
        except Exception as e:
            embed = discord.Embed(title="❌ فشل", description=f"الخطأ: {e}", color=Colors.ERROR)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))