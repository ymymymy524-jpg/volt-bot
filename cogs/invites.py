import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

# مسار ملف التخزين
INVITES_FILE = "invites.json"

# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(INVITES_FILE):
        try:
            with open(INVITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(INVITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        # Cache للدعوات عشان نقدر نحدد مين دعا العضو الجديد
        self.invite_cache = {}

    # دالة لجلب بيانات عضو (وإنشائها لو مش موجودة)
    def get_user_data(self, guild_id, user_id):
        guild_id = str(guild_id)
        user_id = str(user_id)
        if guild_id not in self.data:
            self.data[guild_id] = {}
        if user_id not in self.data[guild_id]:
            self.data[guild_id][user_id] = {
                "real": 0,
                "fake": 0,
                "invited_users": []
            }
        return self.data[guild_id][user_id]

    # دالة مساعدة لحفظ البيانات
    def save(self):
        save_data(self.data)

    # دالة لحساب عدد الأيام من إنشاء الحساب
    def is_fake_account(self, member: discord.Member):
        """التحقق من إذا كان الحساب وهمي (أقل من 7 أيام)"""
        now = discord.utils.utcnow()
        account_age = now - member.created_at
        return account_age.days < 7

    # حدث تحميل البوت لتحديث cache الدعوات
    @commands.Cog.listener()
    async def on_ready(self):
        """تحديث cache الدعوات عند تشغيل البوت"""
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = {
                    invite.code: invite.uses for invite in invites
                }
            except discord.Forbidden:
                # لو البوت مفيش عنده صلاحية جلب الدعوات
                self.invite_cache[guild.id] = {}
            except Exception as e:
                print(f"❌ خطأ في تحديث cache الدعوات في {guild.name}: {e}")
                self.invite_cache[guild.id] = {}

    # حدث انضمام عضو للسيرفر
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # نتجاهل لو العضو بوت
        if member.bot:
            return

        guild_id = member.guild.id
        
        # التحقق من إذا كان الحساب وهمي
        is_fake = self.is_fake_account(member)

        try:
            # جلب الدعوات الحالية
            current_invites = await member.guild.invites()
            current_uses = {invite.code: invite.uses for invite in current_invites}
            
            # مقارنة مع الـ cache لتحديد الدعوة المستخدمة
            inviter_id = None
            used_invite_code = None
            
            if guild_id in self.invite_cache:
                for code, uses in current_uses.items():
                    if code in self.invite_cache[guild_id]:
                        if uses > self.invite_cache[guild_id][code]:
                            # وجدنا الدعوة المستخدمة
                            used_invite_code = code
                            # جلب معلومات الدعوة
                            for invite in current_invites:
                                if invite.code == code:
                                    inviter_id = invite.inviter.id
                                    break
                            break
            
            # تحديث cache
            self.invite_cache[guild_id] = current_uses

            # إذا وجدنا الداعي
            if inviter_id:
                inviter_data = self.get_user_data(guild_id, inviter_id)
                
                # إضافة العضو الجديد لقائمة المدعوين
                if member.id not in inviter_data["invited_users"]:
                    inviter_data["invited_users"].append(member.id)
                
                # زيادة العدد حسب نوع الحساب
                if is_fake:
                    inviter_data["fake"] += 1
                else:
                    inviter_data["real"] += 1
                
                self.save()
                
                # إرسال رسالة ترحيبية مع معلومات الداعي
                try:
                    # البحث عن روم الترحيب
                    welcome_data = self.bot.get_cog("Welcome")
                    if welcome_data:
                        guild_data = welcome_data.get_guild_data(guild_id)
                        welcome_channel_id = guild_data.get("welcome_channel")
                        if welcome_channel_id:
                            channel = member.guild.get_channel(int(welcome_channel_id))
                            if channel:
                                inviter = member.guild.get_member(inviter_id)
                                inviter_name = inviter.display_name if inviter else "Unknown"
                                account_type = "⚠️ وهمي" if is_fake else "✅ حقيقي"
                                
                                embed = discord.Embed(
                                    title="🎟️ معلومات الدعوة",
                                    description=(
                                        f"**{member.mention}** انضم للسيرفر!\n\n"
                                        f"👤 **الداعي:** {inviter.mention if inviter else inviter_name}\n"
                                        f"📊 **نوع الحساب:** {account_type}\n"
                                        f"📅 **تاريخ إنشاء الحساب:** <t:{int(member.created_at.timestamp())}:R>"
                                    ),
                                    color=discord.Color.orange() if is_fake else discord.Color.green(),
                                    timestamp=discord.utils.utcnow()
                                )
                                await channel.send(embed=embed)
                except Exception as e:
                    print(f"❌ خطأ في إرسال رسالة معلومات الدعوة: {e}")
        
        except discord.Forbidden:
            print(f"⚠️ البوت مفيش عنده صلاحية جلب الدعوات في {member.guild.name}")
        except Exception as e:
            print(f"❌ خطأ في تتبع الدعوة: {e}")

    # حدث مغادرة عضو للسيرفر
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # نتجاهل لو العضو بوت
        if member.bot:
            return

        guild_id = member.guild.id
        
        # البحث عن الداعي
        for user_id, user_data in self.data.get(str(guild_id), {}).items():
            if member.id in user_data.get("invited_users", []):
                # إزالة العضو من قائمة المدعوين
                user_data["invited_users"].remove(member.id)
                
                # تقليل العدد
                if user_data["real"] > 0:
                    user_data["real"] -= 1
                elif user_data["fake"] > 0:
                    user_data["fake"] -= 1
                
                self.save()
                break

    # أمر /invites لعرض عدد دعوات عضو
    @app_commands.command(name="invites", description="عرض عدد دعوات عضو في السيرفر")
    @app_commands.describe(member="العضو اللي عايز تشوف دعواته (اختياري)")
    async def invites(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        
        target = member or interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(target.id)

        # جلب بيانات العضو
        user_data = self.get_user_data(guild_id, user_id)
        real = user_data["real"]
        fake = user_data["fake"]
        total = real + fake
        invited_count = len(user_data["invited_users"])

        # إنشاء Embed
        embed = discord.Embed(
            title=f"🎟️ دعوات {target.display_name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="✅ حقيقية", value=f"**{real}**", inline=True)
        embed.add_field(name="⚠️ وهمية", value=f"**{fake}**", inline=True)
        embed.add_field(name="📊 الإجمالي", value=f"**{total}**", inline=True)
        embed.add_field(name="👥 أعضاء مدعوين", value=f"**{invited_count}**", inline=False)
        
        embed.set_footer(text=f"آيدي العضو: {target.id}")

        await interaction.followup.send(embed=embed)

    # أمر /inviter لمعرفة مين دعاك
    @app_commands.command(name="inviter", description="معرفة مين دعاك للسيرفر")
    async def inviter(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # البحث عن الداعي
        inviter_id = None
        for uid, user_data in self.data.get(guild_id, {}).items():
            if interaction.user.id in user_data.get("invited_users", []):
                inviter_id = int(uid)
                break

        if not inviter_id:
            embed = discord.Embed(
                title="❌ لم يتم العثور على الداعي",
                description="لم أتمكن من معرفة مين دعاك للسيرفر",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return

        inviter = interaction.guild.get_member(inviter_id)
        
        if inviter:
            embed = discord.Embed(
                title="🎟️ الداعي",
                description=f"**{inviter.mention}** هو اللي دعاك للسيرفر!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=inviter.display_avatar.url)
            embed.set_footer(text=f"آيدي الداعي: {inviter.id}")
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ الداعي غادر السيرفر",
                description="العضو اللي دعاك غادر السيرفر",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)

    # أمر /invitetop لعرض أفضل 10 داعين
    @app_commands.command(name="invitetop", description="عرض أفضل 10 داعين في السيرفر")
    async def invitetop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild_id = str(interaction.guild.id)
        all_users = self.data.get(guild_id, {})
        
        if not all_users:
            await interaction.followup.send("❌ مفيش بيانات دعوات في السيرفر ده!")
            return

        # ترتيب الأعضاء حسب عدد الدعوات الحقيقية
        sorted_users = sorted(
            all_users.items(),
            key=lambda x: x[1]["real"],
            reverse=True
        )[:10]
        
        medals = ["🥇", "🥈", "🥉"]
        description = ""
        
        for i, (user_id, udata) in enumerate(sorted_users):
            if udata["real"] == 0:
                continue
                
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown User ({user_id})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description += f"{medal} **{name}** — ✅ {udata['real']} | ⚠️ {udata['fake']}\n"

        if not description:
            await interaction.followup.send("❌ مفيش أعضاء عندهم دعوات حقيقية!")
            return

        embed = discord.Embed(
            title="🏆 أفضل 10 داعين في السيرفر",
            description=description,
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed)

    # أمر /resetinvites لتصفير دعوات عضو (للمشرفين)
    @app_commands.command(name="resetinvites", description="تصفير دعوات عضو (للمشرفين)")
    @app_commands.describe(member="العضو اللي عايز تصفر دعواته")
    @app_commands.checks.has_permissions(administrator=True)
    async def resetinvites(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)
        
        user_data = self.get_user_data(guild_id, user_id)
        user_data["real"] = 0
        user_data["fake"] = 0
        user_data["invited_users"] = []
        self.save()

        embed = discord.Embed(
            title="🔄 تم التصفير",
            description=f"تم تصفير دعوات **{member.mention}**",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    # معالجة أخطاء الصلاحيات للأوامر الإدارية
    @resetinvites.error
    async def on_admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(Invites(bot))