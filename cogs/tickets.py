import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
from config import Colors

TICKETS_FILE = "tickets.json"


def load_data():
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_guild_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.data:
            self.data[gid] = {
                "ticket_channel": None,
                "ticket_category": None,
                "ticket_logs": None,
                "ticket_role": None,
                "counter": 0,
                "active_tickets": {}
            }
        # ترقية البيانات
        gd = self.data[gid]
        gd.setdefault("ticket_category", gd.get("ticket_channel"))
        gd.setdefault("ticket_logs", None)
        gd.setdefault("ticket_role", None)
        gd.setdefault("counter", 0)
        return gd

    def save(self):
        save_data(self.data)

    def is_staff(self, member, guild_data):
        if member.guild_permissions.manage_messages:
            return True
        role_id = guild_data.get("ticket_role")
        if role_id and any(r.id == int(role_id) for r in member.roles):
            return True
        return False

    # ═══════════════════════════════════════
    # 🎫 setticket
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="setticket",
        aliases=["اعداد-تذاكر", "تذكرة_اعداد"],
        description="🎫 تحديد Category التذاكر"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الـ Category")
    async def setticket(self, ctx: commands.Context, channel: discord.CategoryChannel):
        gd = self.get_guild_data(ctx.guild.id)
        gd["ticket_category"] = channel.id
        gd["ticket_channel"] = channel.id
        self.save()
        embed = discord.Embed(
            title="✅ تم",
            description=f"تم تعيين الـ Category إلى **{channel.name}**",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎫 ticketrole
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ticketrole",
        aliases=["تذكرة_رتبة", "رتبة_الدعم"],
        description="🎫 تحديد رتبة فريق الدعم"
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(role="الرتبة")
    async def ticketrole(self, ctx: commands.Context, role: discord.Role):
        gd = self.get_guild_data(ctx.guild.id)
        gd["ticket_role"] = role.id
        self.save()
        await ctx.send(f"✅ رتبة الدعم الآن {role.mention}")

    # ═══════════════════════════════════════
    # 🎫 ticketcategory
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ticketcategory",
        aliases=["تذكرة_تصنيف", "كاتجوري_التذاكر"],
        description="🎫 تحديد تصنيف التذاكر"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(category="التصنيف")
    async def ticketcategory(self, ctx: commands.Context, category: discord.CategoryChannel):
        gd = self.get_guild_data(ctx.guild.id)
        gd["ticket_category"] = category.id
        gd["ticket_channel"] = category.id
        self.save()
        await ctx.send(f"✅ التذاكر تنفتح داخل **{category.name}**")

    # ═══════════════════════════════════════
    # 🎫 ticketlogs
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ticketlogs",
        aliases=["تذكرة_لوق", "لوق_التذاكر"],
        description="🎫 تحديد روم سجلات التذاكر"
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الروم")
    async def ticketlogs(self, ctx: commands.Context, channel: discord.TextChannel):
        gd = self.get_guild_data(ctx.guild.id)
        gd["ticket_logs"] = channel.id
        self.save()
        await ctx.send(f"✅ سجلات التذاكر هتروح إلى {channel.mention}")

    # ═══════════════════════════════════════
    # 🎫 ticket — فتح تذكرة
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ticket",
        aliases=["تذكرة", "فتح_تذكرة"],
        description="🎫 فتح تذكرة دعم"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(reason="سبب التذكرة (اختياري)")
    async def ticket(self, ctx: commands.Context, *, reason: str = None):
        gd = self.get_guild_data(ctx.guild.id)
        category_id = gd.get("ticket_category") or gd.get("ticket_channel")
        if not category_id:
            await ctx.send("❌ استخدم `!setticket` أولاً!")
            return
        category = ctx.guild.get_channel(int(category_id))
        if not category:
            await ctx.send("❌ الـ Category غير موجود!")
            return
        active = gd.get("active_tickets", {})
        if str(ctx.author.id) in active.values():
            await ctx.send("❌ لديك تذكرة مفتوحة!")
            return
        gd["counter"] = gd.get("counter", 0) + 1
        ticket_num = gd["counter"]
        channel_name = f"ticket-{ticket_num:04d}"
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        role_id = gd.get("ticket_role")
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        try:
            ticket_ch = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"تذكرة #{ticket_num} | {ctx.author} | {ctx.author.id}"
            )
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أنشئ التذكرة: `{e}`")
            return
        active[str(ticket_ch.id)] = str(ctx.author.id)
        gd["active_tickets"] = active
        self.save()
        embed = discord.Embed(
            title=f"🎫 تذكرة #{ticket_num}",
            description=(
                f"أهلاً {ctx.author.mention}!\n"
                f"فريق الدعم هيرد قريب.\n\n"
                f"📝 **السبب:** {reason or 'غير محدد'}\n\n"
                f"`!close` لإغلاق التذكرة\n"
                f"`!claim` لاستلام التذكرة"
            ),
            color=Colors.INFO,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Ticket #{ticket_num}")
        ping = f"👋 {ctx.author.mention}"
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                ping += f" | {role.mention}"
        await ticket_ch.send(content=ping, embed=embed)
        await ctx.send(f"✅ تم إنشاء التذكرة في {ticket_ch.mention}")

    # ═══════════════════════════════════════
    # 🎫 close
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="close",
        aliases=["اغلاق", "سكر_تذكرة"],
        description="🔒 إغلاق التذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def close(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        cid = str(ctx.channel.id)
        if cid not in active:
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        owner_id = active[cid]
        is_owner = str(ctx.author.id) == owner_id
        is_staff = self.is_staff(ctx.author, gd)
        if not is_owner and not is_staff:
            await ctx.send("❌ مفيش عندك صلاحية!")
            return
        embed = discord.Embed(
            title="🔒 تم الإغلاق",
            description="التذكرة هتتحذف خلال 5 ثواني...",
            color=Colors.ERROR
        )
        await ctx.send(embed=embed)
        # إرسال لوج
        logs_id = gd.get("ticket_logs")
        if logs_id:
            logs_ch = ctx.guild.get_channel(int(logs_id))
            if logs_ch:
                log_embed = discord.Embed(
                    title="🔒 تذكرة مغلقة",
                    description=f"**الروم:** `{ctx.channel.name}`\n**بواسطة:** {ctx.author.mention}",
                    color=Colors.WARNING,
                    timestamp=discord.utils.utcnow()
                )
                try:
                    await logs_ch.send(embed=log_embed)
                except:
                    pass
        await asyncio.sleep(5)
        try:
            del active[cid]
            gd["active_tickets"] = active
            self.save()
            await ctx.channel.delete(reason=f"إغلاق بواسطة {ctx.author}")
        except Exception as e:
            print(f"❌ خطأ: {e}")

    # ═══════════════════════════════════════
    # ✋ claim
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="claim",
        aliases=["استلام", "استلم"],
        description="✋ استلام التذكرة"
    )
    async def claim(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        cid = str(ctx.channel.id)
        if cid not in active:
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        if not self.is_staff(ctx.author, gd):
            await ctx.send("❌ الأمر لفريق الدعم فقط!")
            return
        embed = discord.Embed(
            title="✋ تم الاستلام",
            description=f"{ctx.author.mention} استلم التذكرة",
            color=Colors.SUCCESS
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ➕ add
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="add",
        aliases=["اضف", "ضيف_للتذكرة"],
        description="➕ إضافة عضو للتذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(member="العضو")
    async def add(self, ctx: commands.Context, member: discord.Member):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        cid = str(ctx.channel.id)
        if cid not in active:
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        if not self.is_staff(ctx.author, gd):
            await ctx.send("❌ الأمر لفريق الدعم فقط!")
            return
        try:
            await ctx.channel.set_permissions(
                member,
                read_messages=True, send_messages=True,
                attach_files=True, embed_links=True
            )
            await ctx.send(f"✅ تم إضافة {member.mention}")
        except Exception as e:
            await ctx.send(f"❌ فشل: `{e}`")

    # ═══════════════════════════════════════
    # ➖ remove
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="remove",
        aliases=["شيل", "ازالة"],
        description="➖ إزالة عضو من التذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(member="العضو")
    async def remove(self, ctx: commands.Context, member: discord.Member):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        cid = str(ctx.channel.id)
        if cid not in active:
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        if not self.is_staff(ctx.author, gd):
            await ctx.send("❌ الأمر لفريق الدعم فقط!")
            return
        try:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"✅ تم إزالة {member.mention}")
        except Exception as e:
            await ctx.send(f"❌ فشل: `{e}`")

    # ═══════════════════════════════════════
    # ✏️ rename
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="rename",
        aliases=["تسمية", "غير_اسم_التذكرة"],
        description="✏️ تغيير اسم التذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(name="الاسم الجديد")
    async def rename(self, ctx: commands.Context, *, name: str):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        if str(ctx.channel.id) not in active:
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        if not self.is_staff(ctx.author, gd):
            await ctx.send("❌ الأمر لفريق الدعم فقط!")
            return
        name = name.replace(" ", "-")[:90]
        try:
            await ctx.channel.edit(name=name)
            await ctx.send(f"✅ تم التسمية: **{name}**")
        except Exception as e:
            await ctx.send(f"❌ فشل: `{e}`")

    # ═══════════════════════════════════════
    # 📄 transcript
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="transcript",
        aliases=["نسخة", "حفظ_التذكرة"],
        description="📄 نسخة نصية من التذكرة"
    )
    @commands.bot_has_permissions(attach_files=True)
    async def transcript(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        if str(ctx.channel.id) not in gd.get("active_tickets", {}):
            await ctx.send("❌ هذه ليست تذكرة!")
            return
        if not self.is_staff(ctx.author, gd):
            await ctx.send("❌ الأمر لفريق الدعم فقط!")
            return
        msgs = []
        async for msg in ctx.channel.history(limit=500, oldest_first=True):
            msgs.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}")
        content = "\n".join(msgs) or "لا توجد رسائل"
        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(content)
        await ctx.send(
            embed=discord.Embed(title="📄 نسخة التذكرة", color=Colors.SUCCESS),
            file=discord.File("transcript.txt")
        )
        try:
            os.remove("transcript.txt")
        except:
            pass

    # ═══════════════════════════════════════
    # 📋 tickets — التذاكر المفتوحة
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="tickets",
        aliases=["التذاكر", "التذاكر_المفتوحة"],
        description="📋 عرض التذاكر المفتوحة"
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    async def tickets(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        active = gd.get("active_tickets", {})
        if not active:
            await ctx.send("📭 مفيش تذاكر مفتوحة!")
            return
        lines = []
        for cid, owner_id in active.items():
            ch = ctx.guild.get_channel(int(cid))
            owner = ctx.guild.get_member(int(owner_id))
            ch_name = ch.mention if ch else f"`{cid}`"
            owner_name = owner.mention if owner else f"<@{owner_id}>"
            lines.append(f"{ch_name} • {owner_name}")
        text = "\n".join(lines[:30])
        embed = discord.Embed(
            title=f"🎫 التذاكر المفتوحة ({len(active)})",
            description=text,
            color=Colors.INFO
        )
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Tickets(bot))