import discord
from discord.ext import commands
import json
import os
import asyncio

# مسار ملف التخزين
TICKETS_FILE = "tickets.json"


# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # ═══════════════════════════════════════
    # 🔧 دوال مساعدة
    # ═══════════════════════════════════════
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
    # 🎫 أمر !setticket - إعداد نظام التذاكر
    # ═══════════════════════════════════════
    @commands.command(
        name="setticket",
        aliases=["st", "اعداد-تذاكر"],
        description="🎫 تحديد Category التذاكر في السيرفر"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
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
    # 🎫 أمر !ticket - فتح تذكرة جديدة
    # ═══════════════════════════════════════
    @commands.command(
        name="ticket",
        aliases=["t", "تذكرة"],
        description="🎫 فتح تذكرة دعم جديدة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def ticket(self, ctx: commands.Context, *, reason: str = None):
        """فتح تذكرة دعم"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)

        category_id = guild_data.get("ticket_channel")
        if not category_id:
            await ctx.send("❌ لم يتم تعيين روم التذاكر! استخدم `!setticket` أولاً", delete_after=8)
            return

        category = ctx.guild.get_channel(int(category_id))
        if not category:
            await ctx.send("❌ روم التذاكر غير موجود", delete_after=8)
            return

        # التحقق من وجود تذكرة مفتوحة بالفعل للعضو
        active_tickets = guild_data.get("active_tickets", {})
        if str(ctx.author.id) in active_tickets.values():
            await ctx.send("❌ لديك تذكرة مفتوحة بالفعل! لا يمكنك فتح أكثر من تذكرة", delete_after=8)
            return

        # إنشاء اسم الروم الجديد
        channel_name = f"ticket-{ctx.author.name}"
        channel_name = channel_name.lower().replace(" ", "-")[:90]

        # تحديد صلاحيات الروم
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True, embed_links=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            )
        }

        # إضافة صلاحية لفريق الدعم والإدارة لو موجودين
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
            await ctx.send("❌ البوت مفيش عنده صلاحية إنشاء رومات", delete_after=8)
            return
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {e}", delete_after=8)
            return

        # حفظ التذكرة في البيانات
        active_tickets[str(ticket_channel.id)] = str(ctx.author.id)
        guild_data["active_tickets"] = active_tickets
        self.save()

        # إرسال رسالة الترحيب في التذكرة
        reason_text = reason if reason else "لم يتم تحديد سبب"
        embed = discord.Embed(
            title="🎫 تم إنشاء التذكرة",
            description=(
                f"أهلاً {ctx.author.mention}!\n"
                f"فريق الدعم هيرد عليك في أقرب وقت.\n\n"
                f"📝 **السبب:** {reason_text}\n\n"
                f"لإغلاق التذكرة، استخدم الأمر `!close`"
            ),
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"آيدي التذكرة: {ticket_channel.id}")

        await ticket_channel.send(
            content=f"👋 {ctx.author.mention} | فريق الدعم",
            embed=embed
        )

        await ctx.send(f"✅ تم إنشاء التذكرة في {ticket_channel.mention}", delete_after=8)

    # ═══════════════════════════════════════
    # 🔒 أمر !close - إغلاق التذكرة
    # ═══════════════════════════════════════
    @commands.command(
        name="close",
        aliases=["cl", "اغلاق"],
        description="🔒 إغلاق التذكرة الحالية وحذفها"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def close(self, ctx: commands.Context):
        """إغلاق التذكرة الحالية"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة! الأمر ده بيستخدم جوه رومات التذاكر فقط", delete_after=8)
            return

        # التحقق من الصلاحيات
        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ فقط صاحب التذكرة أو الإدارة يمكنهم إغلاقها", delete_after=8)
            return

        # إرسال رسالة الإغلاق
        embed = discord.Embed(
            title="🔒 تم إغلاق التذكرة",
            description="شكراً لتواصلك مع الدعم! الروم هيتحذف خلال 5 ثواني...",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

        # حذف الروم بعد 5 ثواني
        await asyncio.sleep(5)

        try:
            del active_tickets[channel_id]
            guild_data["active_tickets"] = active_tickets
            self.save()

            await ctx.channel.delete(reason=f"تم إغلاق التذكرة بواسطة {ctx.author}")
        except Exception as e:
            print(f"❌ خطأ في حذف التذكرة: {e}")

    # ═══════════════════════════════════════
    # ➕ أمر !add - إضافة عضو للتذكرة
    # ═══════════════════════════════════════
    @commands.command(
        name="add",
        aliases=["اضف"],
        description="➕ إضافة عضو للتذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def add(self, ctx: commands.Context, member: discord.Member):
        """إضافة عضو للتذكرة"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة!", delete_after=8)
            return

        # التحقق من الصلاحيات
        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ مفيش عندك صلاحية!", delete_after=8)
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
            await ctx.send("❌ البوت مفيش عنده صلاحية!", delete_after=8)

    # ═══════════════════════════════════════
    # ➖ أمر !remove - إزالة عضو من التذكرة
    # ═══════════════════════════════════════
    @commands.command(
        name="remove",
        aliases=["rm", "شيل"],
        description="➖ إزالة عضو من التذكرة"
    )
    @commands.bot_has_permissions(manage_channels=True)
    async def remove(self, ctx: commands.Context, member: discord.Member):
        """إزالة عضو من التذكرة"""
        guild_id = str(ctx.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(ctx.channel.id)
        if channel_id not in active_tickets:
            await ctx.send("❌ هذه ليست تذكرة!", delete_after=8)
            return

        # التحقق من الصلاحيات
        user_id = active_tickets[channel_id]
        is_owner = str(ctx.author.id) == user_id
        has_perms = (
            ctx.author.guild_permissions.manage_channels or
            ctx.author.guild_permissions.administrator
        )

        if not is_owner and not has_perms:
            await ctx.send("❌ مفيش عندك صلاحية!", delete_after=8)
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
            await ctx.send("❌ البوت مفيش عنده صلاحية!", delete_after=8)

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx: commands.Context, error):
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
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


async def setup(bot):
    await bot.add_cog(Tickets(bot))