import discord
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

    # ==========================================
    # 🔧 دوال مساعدة
    # ==========================================
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

    def save(self):
        save_data(self.data)

    def is_fake_account(self, member: discord.Member):
        """التحقق من إذا كان الحساب وهمي (أقل من 7 أيام)"""
        now = discord.utils.utcnow()
        account_age = now - member.created_at
        return account_age.days < 7

    # ==========================================
    # 🔔 Events
    # ==========================================
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
                self.invite_cache[guild.id] = {}
            except Exception as e:
                print(f"❌ خطأ في تحديث cache الدعوات في {guild.name}: {e}")
                self.invite_cache[guild.id] = {}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        guild_id = member.guild.id
        is_fake = self.is_fake_account(member)

        try:
            current_invites = await member.guild.invites()
            current_uses = {invite.code: invite.uses for invite in current_invites}

            inviter_id = None
            used_invite_code = None

            if guild_id in self.invite_cache:
                for code, uses in current_uses.items():
                    if code in self.invite_cache[guild_id]:
                        if uses > self.invite_cache[guild_id][code]:
                            used_invite_code = code
                            for invite in current_invites:
                                if invite.code == code:
                                    inviter_id = invite.inviter.id
                                    break
                            break

            self.invite_cache[guild_id] = current_uses

            if inviter_id:
                inviter_data = self.get_user_data(guild_id, inviter_id)

                if member.id not in inviter_data["invited_users"]:
                    inviter_data["invited_users"].append(member.id)

                if is_fake:
                    inviter_data["fake"] += 1
                else:
                    inviter_data["real"] += 1

                self.save()

                try:
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

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return

        guild_id = member.guild.id

        for user_id, user_data in self.data.get(str(guild_id), {}).items():
            if member.id in user_data.get("invited_users", []):
                user_data["invited_users"].remove(member.id)

                if user_data["real"] > 0:
                    user_data["real"] -= 1
                elif user_data["fake"] > 0:
                    user_data["fake"] -= 1

                self.save()
                break

    # ==========================================
    # 📨 أمر !invites - عرض عدد الدعوات
    # ==========================================
    @commands.command(
        name="invites",
        aliases=["inv", "دعوات", "دعوة"],
        description="عرض عدد دعوات عضو في السيرفر"
    )
    async def invites_prefix(self, ctx: commands.Context, member: discord.Member = None):
        """عرض عدد دعوات عضو"""
        target = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(target.id)

        user_data = self.get_user_data(guild_id, user_id)
        real = user_data["real"]
        fake = user_data["fake"]
        total = real + fake
        invited_count = len(user_data["invited_users"])

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
        await ctx.send(embed=embed)

    # ==========================================
    # 📨 أمر !inviter - مين دعاك؟
    # ==========================================
    @commands.command(
        name="inviter",
        aliases=["دعاني", "مين-دعاني"],
        description="معرفة مين دعاك للسيرفر"
    )
    async def inviter_prefix(self, ctx: commands.Context):
        """معرفة مين دعاك للسيرفر"""
        guild_id = str(ctx.guild.id)

        inviter_id = None
        for uid, user_data in self.data.get(guild_id, {}).items():
            if ctx.author.id in user_data.get("invited_users", []):
                inviter_id = int(uid)
                break

        if not inviter_id:
            embed = discord.Embed(
                title="❌ لم يتم العثور على الداعي",
                description="لم أتمكن من معرفة مين دعاك للسيرفر",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        inviter = ctx.guild.get_member(inviter_id)

        if inviter:
            embed = discord.Embed(
                title="🎟️ الداعي",
                description=f"**{inviter.mention}** هو اللي دعاك للسيرفر!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=inviter.display_avatar.url)
            embed.set_footer(text=f"آيدي الداعي: {inviter.id}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ الداعي غادر السيرفر",
                description="العضو اللي دعاك غادر السيرفر",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    # ==========================================
    # 🏆 أمر !invitetop - أفضل 10 داعين
    # ==========================================
    @commands.command(
        name="invitetop",
        aliases=["itop", "توب-الدعوات", "افضل-الداعين"],
        description="عرض أفضل 10 داعين في السيرفر"
    )
    async def invitetop_prefix(self, ctx: commands.Context):
        """عرض أفضل 10 داعين"""
        guild_id = str(ctx.guild.id)
        all_users = self.data.get(guild_id, {})

        if not all_users:
            await ctx.send("❌ مفيش بيانات دعوات في السيرفر ده!")
            return

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

            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown User ({user_id})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description += f"{medal} **{name}** — ✅ {udata['real']} | ⚠️ {udata['fake']}\n"

        if not description:
            await ctx.send("❌ مفيش أعضاء عندهم دعوات حقيقية!")
            return

        embed = discord.Embed(
            title="🏆 أفضل 10 داعين في السيرفر",
            description=description,
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

    # ==========================================
    # 🔄 أمر !resetinvites - تصفير الدعوات (للمشرفين)
    # ==========================================
    @commands.command(
        name="resetinvites",
        aliases=["rinv", "تصفير-الدعوات", "صفر-الدعوات"],
        description="تصفير دعوات عضو (للمشرفين)"
    )
    @commands.has_permissions(administrator=True)
    async def resetinvites_prefix(self, ctx: commands.Context, member: discord.Member):
        """تصفير دعوات عضو - يتطلب صلاحية Administrator"""
        guild_id = str(ctx.guild.id)
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
        await ctx.send(embed=embed)

    # ==========================================
    # ⚠️ معالجة الأخطاء
    # ==========================================
    @resetinvites_prefix.error
    async def resetinvites_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator** لاستخدام الأمر ده!", delete_after=8)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو ده في السيرفر!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ لازم تحدد العضو!\n"
                "**مثال:** `!resetinvites @عضو`",
                delete_after=8
            )


async def setup(bot):
    await bot.add_cog(Invites(bot))