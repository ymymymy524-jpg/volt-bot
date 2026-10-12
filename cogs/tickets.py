import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio

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
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "ticket_channel": None,
                "active_tickets": {}
            }
        return self.data[guild_id]

    def save(self):
        save_data(self.data)

    # ═══════════════════════════════════════
    # 🎫 !setticket / /setticket
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="setticket",
        aliases=["st", "اعداد-تذاكر"],
        description="🎫 تحديد Category التذاكر"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="الـ Category الخاص بالتذاكر")
    async def setticket(self, ctx: commands.Context, channel: discord.CategoryChannel):
        """تحديد Category التذاكر"""
        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["ticket_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم التذاكر",
            description=f"تم تعيين الـ Category إلى **{channel.name}**\nالتذاكر هتتفتح جواه تلقائياً.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎫 !ticket / /ticket
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ticket",
        aliases=["t", "تذكرة"],
        description="🎫 فتح تذكرة دعم جديدة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(reason="سبب فتح التذكرة (اختياري)")
    async def ticket(self, ctx: commands.Context, *, reason: str = None):
        """فتح تذكرة دعم"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)

        category_id = guild_data.get("ticket_channel")
        if not category_id:
            await ctx.send("❌ لم يتم تعيين روم التذاكر! استخدم `/setticket` أو `!setticket` أولاً")
            return

        category = ctx.guild.get_channel(int(category_id))
        if not category:
            await ctx.send("❌ روم التذاكر غير موجود")
            return

        active_tickets = guild_data.get("active_tickets", {})
        if str(ctx.author.id) in active_tickets.values():
            await ctx.send("❌ لديك تذكرة مفتوحة بالفعل! لا يمكنك فتح أكثر من تذكرة")
            return

        channel_name = f"ticket-{ctx.author.name}"
        channel_name = channel_name.lower().replace(" ", "-")[:90]

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True, embed_links=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            )
        }

        support_role = discord.utils.get(ctx.guild.roles, name="Support")
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            )

        admin_role = discord.utils.get(ctx.guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            )

        try:
            ticket_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"تذكرة دعم من {ctx.author.mention} | الآيدي: {ctx.author.id}"
            )
        except discord.Forbidden:
            await ctx.send("❌ البوت مفيش عنده صلاحية إنشاء رومات")
            return
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {e}")
            return

        active_tickets[str(ticket_channel.id)] = str(ctx.author.id)
        guild_data["active_tickets"] = active_tickets
        self.save()

        reason_text = reason if reason else "لم يتم تحديد سبب"
        embed = discord.Embed(
            title="🎫 تم إنشاء التذكرة",
            description=(
                f"أهلاً {ctx.author.mention}!\n"
                f"فريق الدعم هيرد عليك في أقرب وقت.\n\n"
                f"📝 **السبب:** {reason_text}\n\n"
                f"لإغلاق التذكرة، استخدم `/close` أو `!close`"
            ),
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"آيدي التذكرة: {ticket_channel.id}")

        await ticket_channel.send(
            content=f"👋 {ctx.author.mention} | فريق الدعم",
            embed=embed
        )

        await ctx.send(f"✅ تم إنشاء التذكرة في {ticket_channel.mention}")

    # ═══════════════════════════════════════
    # 🔒 !close / /close
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="close",
        aliases=["cl", "اغلاق"],
        description="🔒 إغلاق التذكرة الحالية"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def close(self, ctx: commands.Context):
        """إغلاق التذكرة الحالية"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة! الأمر ده بيستخدم جوه رومات التذاكر فقط")
            return

        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ فقط صاحب التذكرة أو الإدارة يمكنهم إغلاقها")
            return

        embed = discord.Embed(
            title="🔒 تم إغلاق التذكرة",
            description="شكراً لتواصلك مع الدعم! الروم هيتحذف خلال 5 ثواني...",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

        await asyncio.sleep(5)

        try:
            del active_tickets[channel_id]
            guild_data["active_tickets"] = active_tickets
            self.save()

            await ctx.channel.delete(reason=f"تم إغلاق التذكرة بواسطة {ctx.author}")
        except Exception as e:
            print(f"❌ خطأ في حذف التذكرة: {e}")

    # ═══════════════════════════════════════
    # ➕ !add / /add
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="add",
        aliases=["اضف"],
        description="➕ إضافة عضو للتذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(member="العضو المراد إضافته")
    async def add(self, ctx: commands.Context, member: discord.Member):
        """إضافة عضو للتذكرة"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة!")
            return

        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ مفيش عندك صلاحية!")
            return

        try:
            await ctx.channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            )
            embed = discord.Embed(
                title="✅ تم إضافة العضو",
                description=f"تم إضافة {member.mention} للتذكرة",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ البوت مفيش عنده صلاحية!")

    # ═══════════════════════════════════════
    # ➖ !remove / /remove
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="remove",
        aliases=["rm", "شيل"],
        description="➖ إزالة عضو من التذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(member="العضو المراد إزالته")
    async def remove(self, ctx: commands.Context, member: discord.Member):
        """إزالة عضو من التذكرة"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة!")
            return

        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ مفيش عندك صلاحية!")
            return

        try:
            await ctx.channel.set_permissions(member, overwrite=None)
            embed = discord.Embed(
                title="✅ تم إزالة العضو",
                description=f"تم إزالة {member.mention} من التذكرة",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ البوت مفيش عنده صلاحية!")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات المطلوبة!", delete_after=8)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو ده!", delete_after=8)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة دي!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات المدخلة!", delete_after=8)


async def setup(bot):
    await bot.add_cog(Tickets(bot))