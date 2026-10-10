import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random

# مسار ملف التخزين
LEVELS_FILE = "levels.json"

# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cooldowns = {}

    # دالة لحساب الـ XP المطلوب للترقية
    def xp_needed(self, level):
        return 100 + (level * 50)

    # دالة لإنشاء Progress Bar نصي
    def progress_bar(self, current, total, length=10):
        percentage = current / total if total > 0 else 0
        filled = int(length * percentage)
        bar = "▰" * filled + "▱" * (length - filled)
        return f"{bar} {int(percentage * 100)}%"

    # دالة لجلب بيانات عضو
    def get_user_data(self, guild_id, user_id):
        guild_id = str(guild_id)
        user_id = str(user_id)
        if guild_id not in self.data:
            self.data[guild_id] = {}
        if user_id not in self.data[guild_id]:
            self.data[guild_id][user_id] = {"xp": 0, "level": 0}
        return self.data[guild_id][user_id]

    # دالة مساعدة لحفظ البيانات
    def save(self):
        save_data(self.data)

    # حدث استقبال الرسائل لحساب XP
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        await self.bot.process_commands(message)

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        now = discord.utils.utcnow()

        cooldown_key = (guild_id, user_id)
        if cooldown_key in self.cooldowns:
            last_time = self.cooldowns[cooldown_key]
            if (now - last_time).total_seconds() < 60:
                return
        self.cooldowns[cooldown_key] = now

        user_data = self.get_user_data(guild_id, user_id)
        
        xp_gained = random.randint(5, 15)
        user_data["xp"] += xp_gained

        level = user_data["level"]
        needed = self.xp_needed(level)
        leveled_up = False
        
        while user_data["xp"] >= needed:
            user_data["xp"] -= needed
            level += 1
            user_data["level"] = level
            needed = self.xp_needed(level)
            leveled_up = True

        self.save()

        if leveled_up:
            try:
                await message.channel.send(
                    f"🎉 مبروك يا {message.author.mention}! وصلت للمستوى **{level}**!"
                )
            except discord.HTTPException:
                pass

    # أمر /rank
    @app_commands.command(name="rank", description="📊 عرض مستوى ورتبة عضو في السيرفر")
    @app_commands.describe(member="العضو اللي عايز تشوف مستواه (اختياري)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        
        target = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(target.id)

        user_data = self.get_user_data(guild_id, user_id)
        level = user_data["level"]
        xp = user_data["xp"]
        needed = self.xp_needed(level)

        all_users = self.data.get(guild_id, {})
        sorted_users = sorted(
            all_users.items(), 
            key=lambda x: (x[1]["level"], x[1]["xp"]), 
            reverse=True
        )
        rank_pos = 1
        for uid, udata in sorted_users:
            if uid == user_id:
                break
            rank_pos += 1

        embed = discord.Embed(
            title=f"📊 بطاقة مستوى {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 المستوى", value=f"**{level}**", inline=True)
        embed.add_field(name="⭐ XP", value=f"**{xp}/{needed}**", inline=True)
        embed.add_field(name="🥇 الترتيب", value=f"**#{rank_pos}**", inline=True)
        embed.add_field(name="📈 التقدم", value=self.progress_bar(xp, needed), inline=False)
        embed.set_footer(text=f"المطلوب للترقية: {needed - xp} XP")

        await interaction.followup.send(embed=embed)

    # أمر /top
    @app_commands.command(name="top", description="🏆 عرض أفضل 10 أعضاء في المستويات")
    async def top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild_id = str(interaction.guild.id)
        all_users = self.data.get(guild_id, {})
        
        if not all_users:
            await interaction.followup.send("❌ مفيش بيانات مستويات في السيرفر ده!")
            return

        sorted_users = sorted(
            all_users.items(), 
            key=lambda x: (x[1]["level"], x[1]["xp"]), 
            reverse=True
        )[:10]
        
        medals = ["🥇", "🥈", "🥉"]
        description = ""
        
        for i, (user_id, udata) in enumerate(sorted_users):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown User ({user_id})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description += f"{medal} **{name}** — المستوى: **{udata['level']}** | XP: **{udata['xp']}**\n"

        embed = discord.Embed(
            title="🏆 أفضل 10 أعضاء في المستويات",
            description=description,
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)

    # أمر /setlevel
    @app_commands.command(name="setlevel", description="📊 تحديد مستوى عضو (للمشرفين)")
    @app_commands.describe(
        member="العضو اللي عايز تعدل مستواه",
        level="المستوى الجديد (0 - 1000)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setlevel(self, interaction: discord.Interaction, member: discord.Member, level: app_commands.Range[int, 0, 1000]):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        user_data = self.get_user_data(guild_id, user_id)
        user_data["level"] = level
        user_data["xp"] = 0
        self.save()

        embed = discord.Embed(
            title="✅ تم تحديث المستوى",
            description=f"تم تعيين مستوى **{member.mention}** إلى **{level}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # أمر /resetlevel
    @app_commands.command(name="resetlevel", description="📊 تصفير مستوى عضو (للمشرفين)")
    @app_commands.describe(member="العضو اللي عايز تصفر مستواه")
    @app_commands.checks.has_permissions(administrator=True)
    async def resetlevel(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        user_data = self.get_user_data(guild_id, user_id)
        user_data["level"] = 0
        user_data["xp"] = 0
        self.save()

        embed = discord.Embed(
            title="🔄 تم التصفير",
            description=f"تم تصفير مستوى **{member.mention}**",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    # معالجة الأخطاء
    @setlevel.error
    @resetlevel.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Levels(bot))