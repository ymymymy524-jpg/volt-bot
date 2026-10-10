import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from config import Colors

# ==========================================
# 🛠️ الأوامر العامة (General Commands)
# ==========================================

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # 🏓 أمر Ping - سرعة البوت
    # ==========================================
    @app_commands.command(name="ping", description="🏓 عرض سرعة استجابة البوت")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 بونغ!",
            description=f"**سرعة الاستجابة:** `{latency}ms`",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 🖼️ أمر Avatar - صورة العضو أو السيرفر
    # ==========================================
    avatar_group = app_commands.Group(name="avatar", description="🖼️ عرض الصور الشخصية")

    @avatar_group.command(name="user", description="👤 عرض صورة عضو")
    async def avatar_user(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ صورة {member.display_name}",
            color=Colors.INFO
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="PNG", url=str(member.display_avatar.replace(format='png', size=1024)), style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="JPG", url=str(member.display_avatar.replace(format='jpg', size=1024)), style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="WEBP", url=str(member.display_avatar.replace(format='webp', size=1024)), style=discord.ButtonStyle.link))
        
        await interaction.response.send_message(embed=embed, view=view)

    @avatar_group.command(name="server", description="🏰 عرض صورة السيرفر")
    async def avatar_server(self, interaction: discord.Interaction):
        if not interaction.guild.icon:
            await interaction.response.send_message("❌ هذا السيرفر لا يحتوي على صورة!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🖼️ صورة {interaction.guild.name}",
            color=Colors.INFO
        )
        embed.set_image(url=interaction.guild.icon.url)
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="PNG", url=str(interaction.guild.icon.replace(format='png', size=1024)), style=discord.ButtonStyle.link))
        view.add_item(discord.ui.Button(label="JPG", url=str(interaction.guild.icon.replace(format='jpg', size=1024)), style=discord.ButtonStyle.link))
        
        await interaction.response.send_message(embed=embed, view=view)

    # ==========================================
    # 🎨 أمر Banner - بانر العضو أو السيرفر
    # ==========================================
    banner_group = app_commands.Group(name="banner", description="🎨 عرض البانرات")

    @banner_group.command(name="user", description="👤 عرض بانر عضو")
    async def banner_user(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        user = await self.bot.fetch_user(member.id)
        
        if not user.banner:
            await interaction.response.send_message(f"❌ {member.mention} لا يمتلك بانر!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎨 بانر {member.display_name}",
            color=Colors.INFO
        )
        embed.set_image(url=user.banner.url)
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @banner_group.command(name="server", description="🏰 عرض بانر السيرفر")
    async def banner_server(self, interaction: discord.Interaction):
        if not interaction.guild.banner:
            await interaction.response.send_message("❌ هذا السيرفر لا يحتوي على بانر!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎨 بانر {interaction.guild.name}",
            color=Colors.INFO
        )
        embed.set_image(url=interaction.guild.banner.url)
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 👤 أمر User - معلومات عضو
    # ==========================================
    @app_commands.command(name="user", description="👤 عرض معلومات عضو")
    async def user(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        joined_at = discord.utils.format_dt(member.joined_at, style='R')
        created_at = discord.utils.format_dt(member.created_at, style='R')
        
        top_role = member.top_role.mention if member.top_role != interaction.guild.default_role else "لا يوجد"
        
        embed = discord.Embed(
            title=f"👤 معلومات {member.display_name}",
            color=member.color if member.color != discord.Color.default() else Colors.INFO
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="🆔 المعرف", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📛 الاسم الكامل", value=f"{member}", inline=True)
        embed.add_field(name="👑 أعلى رتبة", value=top_role, inline=True)
        embed.add_field(name="📅 تاريخ الانضمام للسيرفر", value=joined_at, inline=False)
        embed.add_field(name="🎂 تاريخ إنشاء الحساب", value=created_at, inline=False)
        
        roles = [role.mention for role in member.roles[1:]]
        if roles:
            roles_text = ", ".join(roles[:20])
            if len(roles) > 20:
                roles_text += f" ... و {len(roles) - 20} رتب أخرى"
            embed.add_field(name=f"🎭 الرتب [{len(roles)}]", value=roles_text, inline=False)
        
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 🏰 أمر Server - معلومات السيرفر
    # ==========================================
    @app_commands.command(name="server", description="🏰 عرض معلومات السيرفر")
    async def server(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        total_members = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        roles_count = len(guild.roles) - 1
        emojis_count = len(guild.emojis)
        
        verification_levels = {
            discord.VerificationLevel.none: "❌ لا يوجد",
            discord.VerificationLevel.low: "🟢 منخفض",
            discord.VerificationLevel.medium: "🟡 متوسط",
            discord.VerificationLevel.high: "🔴 عالي",
            discord.VerificationLevel.highest: "⚫ عالي جداً"
        }
        verification = verification_levels.get(guild.verification_level, "غير معروف")
        
        created_at = discord.utils.format_dt(guild.created_at, style='R')
        
        embed = discord.Embed(
            title=f"🏰 معلومات {guild.name}",
            color=Colors.INFO
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="🆔 المعرف", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 المالك", value=guild.owner.mention, inline=True)
        embed.add_field(name="📅 تاريخ الإنشاء", value=created_at, inline=True)
        
        embed.add_field(name="👥 الأعضاء", value=f"**الإجمالي:** {total_members}\n**بشر:** {humans}\n**بوتات:** {bots}", inline=True)
        embed.add_field(name="💬 القنوات", value=f"**نصية:** {text_channels}\n**صوتية:** {voice_channels}\n**فئات:** {categories}", inline=True)
        embed.add_field(name="🎭 الرتب", value=f"`{roles_count}` رتبة", inline=True)
        
        embed.add_field(name="😀 الإيموجيات", value=f"`{emojis_count}` إيموجي", inline=True)
        embed.add_field(name="🔒 مستوى التحقق", value=verification, inline=True)
        embed.add_field(name="🚀 مستوى البوست", value=f"Level {guild.premium_tier.value}", inline=True)
        
        if guild.description:
            embed.add_field(name="📝 الوصف", value=guild.description, inline=False)
        
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # 💎 أمر Volt - رصيد Bitcoin
    # ==========================================
    @app_commands.command(name="volt", description="💎 عرض رصيد Bitcoin لعضو")
    async def volt(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = None):
        member = member or interaction.user
        
        # ⚠️ نفس المسار اللي economy.py بيستخدمه
        bitcoin_file = "bitcoin.json"
        if os.path.exists(bitcoin_file):
            with open(bitcoin_file, "r", encoding="utf-8") as f:
                bitcoin_data = json.load(f)
        else:
            bitcoin_data = {}
        
        user_id = str(member.id)
        
        if user_id not in bitcoin_data:
            balance = 0
        else:
            balance = bitcoin_data[user_id].get("balance", 0)
        
        if amount is not None:
            if not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="❌ صلاحية مطلوبة",
                    description="يجب أن تكون مشرفاً لاستخدام هذا الخيار!",
                    color=Colors.ERROR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if user_id not in bitcoin_data:
                bitcoin_data[user_id] = {"balance": 0, "total_earned": 0, "total_spent": 0, "transactions": [], "inventory": []}
            
            bitcoin_data[user_id]["balance"] += amount
            
            with open(bitcoin_file, "w", encoding="utf-8") as f:
                json.dump(bitcoin_data, f, ensure_ascii=False, indent=2)
            
            action = "إضافة" if amount > 0 else "خصم"
            embed = discord.Embed(
                title="💎 تم تعديل الرصيد",
                description=f"✅ تم {action} **{abs(amount)} ₿** إلى حساب {member.mention}\n\n**الرصيد الجديد:** `{bitcoin_data[user_id]['balance']} ₿`",
                color=Colors.SUCCESS
            )
        else:
            embed = discord.Embed(
                title=f"💎 رصيد {member.display_name}",
                description=f"**الرصيد الحالي:** `{balance} ₿`",
                color=Colors.GOLD
            )
            embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.set_footer(text=f"طلب بواسطة: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))