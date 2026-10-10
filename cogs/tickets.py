import discord
from discord import app_commands
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

    # دالة لجلب بيانات السيرفر (وإنشائها لو مش موجودة)
    def get_guild_data(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "ticket_channel": None,
                "active_tickets": {}
            }
        return self.data[guild_id]

    # دالة مساعدة لحفظ البيانات
    def save(self):
        save_data(self.data)

    # أمر /setticket لتحديد روم (Category) التذاكر
    @app_commands.command(name="setticket", description="تحديد روم (Category) التذاكر في السيرفر")
    @app_commands.describe(channel="الـ Category اللي هتتفتح فيه التذاكر")
    @app_commands.checks.has_permissions(administrator=True)
    async def setticket(self, interaction: discord.Interaction, channel: discord.CategoryChannel):
        guild_data = self.get_guild_data(interaction.guild.id)
        guild_data["ticket_channel"] = channel.id
        self.save()

        embed = discord.Embed(
            title="✅ تم تعيين روم التذاكر",
            description=f"تم تعيين الـ Category إلى **{channel.name}**\nالتذاكر هتتفتح جواه تلقائياً.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /ticket لفتح تذكرة دعم جديدة
    @app_commands.command(name="ticket", description="فتح تذكرة دعم جديدة")
    @app_commands.describe(reason="سبب فتح التذكرة (اختياري)")
    async def ticket(self, interaction: discord.Interaction, reason: str = None):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        guild_data = self.get_guild_data(guild_id)
        
        category_id = guild_data.get("ticket_channel")
        if not category_id:
            embed = discord.Embed(
                title="❌ لم يتم تعيين روم التذاكر",
                description="يجب على الإدارة استخدام `/setticket` أولاً لتحديد الـ Category.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        category = interaction.guild.get_channel(int(category_id))
        if not category:
            embed = discord.Embed(
                title="❌ روم التذاكر غير موجود",
                description="الـ Category المحدد محذوف أو غير موجود.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # التحقق من وجود تذكرة مفتوحة بالفعل للعضو
        active_tickets = guild_data.get("active_tickets", {})
        if str(interaction.user.id) in active_tickets.values():
            embed = discord.Embed(
                title="❌ لديك تذكرة مفتوحة بالفعل",
                description="لا يمكنك فتح أكثر من تذكرة في نفس الوقت.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # إنشاء اسم الروم الجديد
        channel_name = f"ticket-{interaction.user.name}"
        channel_name = channel_name.lower().replace(" ", "-")[:90]  # حد أقصى 100 حرف
        
        # تحديد صلاحيات الروم
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True, embed_links=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            )
        }

        # إضافة صلاحية لفريق الدعم والإدارة لو موجودين
        support_role = discord.utils.get(interaction.guild.roles, name="Support")
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            )
        
        admin_role = discord.utils.get(interaction.guild.roles, name="Admin")
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
            )

        try:
            # إنشاء الروم النصي
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"تذكرة دعم من {interaction.user.mention} | الآيدي: {interaction.user.id}"
            )
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ لا توجد صلاحيات",
                description="البوت مفيش عنده صلاحية إنشاء رومات في الـ Category ده.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء إنشاء التذكرة: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # حفظ التذكرة في البيانات
        active_tickets[str(ticket_channel.id)] = str(interaction.user.id)
        guild_data["active_tickets"] = active_tickets
        self.save()

        # إرسال رسالة الترحيب في التذكرة
        reason_text = reason if reason else "لم يتم تحديد سبب"
        embed = discord.Embed(
            title="🎫 تم إنشاء التذكرة",
            description=(
                f"أهلاً {interaction.user.mention}!\n"
                f"فريق الدعم هيرد عليك في أقرب وقت.\n\n"
                f"📝 **السبب:** {reason_text}\n\n"
                f"لإغلاق التذكرة، استخدم الأمر `/close`"
            ),
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"آيدي التذكرة: {ticket_channel.id}")
        
        await ticket_channel.send(
            content=f"👋 {interaction.user.mention} | فريق الدعم",
            embed=embed
        )

        success_embed = discord.Embed(
            title="✅ تم إنشاء التذكرة",
            description=f"تم إنشاء التذكرة بنجاح في {ticket_channel.mention}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)

    # أمر /close لإغلاق التذكرة الحالية وحذفها
    @app_commands.command(name="close", description="إغلاق التذكرة الحالية وحذفها")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(interaction.channel.id)
        if channel_id not in active_tickets:
            embed = discord.Embed(
                title="❌ هذه ليست تذكرة",
                description="الأمر ده بيستخدم جوه رومات التذاكر فقط.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # التحقق من الصلاحيات (صاحب التذكرة أو عنده صلاحية إدارة الرومات)
        user_id = active_tickets[channel_id]
        is_owner = str(interaction.user.id) == user_id
        has_perms = interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator

        if not is_owner and not has_perms:
            embed = discord.Embed(
                title="❌ لا توجد صلاحية",
                description="فقط صاحب التذكرة أو الإدارة يمكنهم إغلاقها.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # إرسال رسالة الإغلاق
        embed = discord.Embed(
            title="🔒 جاري إغلاق التذكرة",
            description="سيتم حذف الروم خلال 5 ثواني...",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # إرسال رسالة في الروم
        close_embed = discord.Embed(
            title="🔒 تم إغلاق التذكرة",
            description="شكراً لتواصلك مع الدعم! الروم هيتحذف دلوقتي.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.channel.send(embed=close_embed)

        # حذف الروم بعد 5 ثواني
        await asyncio.sleep(5)

        try:
            # إزالة من البيانات
            del active_tickets[channel_id]
            guild_data["active_tickets"] = active_tickets
            self.save()

            await interaction.channel.delete(reason="تم إغلاق التذكرة بواسطة الأمر /close")
        except Exception as e:
            print(f"❌ خطأ في حذف التذكرة: {e}")

    # أمر /add لإضافة عضو للتذكرة
    @app_commands.command(name="add", description="إضافة عضو للتذكرة")
    @app_commands.describe(member="العضو اللي عايز تضيفه")
    async def add(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(interaction.channel.id)
        if channel_id not in active_tickets:
            embed = discord.Embed(
                title="❌ هذه ليست تذكرة",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # التحقق من الصلاحيات
        user_id = active_tickets[channel_id]
        is_owner = str(interaction.user.id) == user_id
        has_perms = interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator

        if not is_owner and not has_perms:
            embed = discord.Embed(
                title="❌ لا توجد صلاحية",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            await interaction.channel.set_permissions(
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
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ لا توجد صلاحيات",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # أمر /remove لإزالة عضو من التذكرة
    @app_commands.command(name="remove", description="إزالة عضو من التذكرة")
    @app_commands.describe(member="العضو اللي عايز تزيله")
    async def remove(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        guild_data = self.get_guild_data(guild_id)
        active_tickets = guild_data.get("active_tickets", {})

        channel_id = str(interaction.channel.id)
        if channel_id not in active_tickets:
            embed = discord.Embed(
                title="❌ هذه ليست تذكرة",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # التحقق من الصلاحيات
        user_id = active_tickets[channel_id]
        is_owner = str(interaction.user.id) == user_id
        has_perms = interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator

        if not is_owner and not has_perms:
            embed = discord.Embed(
                title="❌ لا توجد صلاحية",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            # إزالة الصلاحيات المخصصة للعضو
            await interaction.channel.set_permissions(member, overwrite=None)
            embed = discord.Embed(
                title="✅ تم إزالة العضو",
                description=f"تم إزالة {member.mention} من التذكرة",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ لا توجد صلاحيات",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # معالجة أخطاء الصلاحيات للأوامر الإدارية
    @setticket.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(Tickets(bot))