import discord
from discord.ext import commands
from discord import app_commands
import os
from config import Colors

# قايمة مالكي البوت — تقدر تضيف IDs هنا
OWNERS = [int(x) for x in os.getenv("OWNERS", "").split(",") if x.strip().isdigit()]


def is_owner(user_id: int) -> bool:
    return user_id in OWNERS


class Admin(commands.Cog):
    """👑 أوامر الإدارة العامة"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 💬 say
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="say", aliases=["قل", "كرر"], description="💬 البوت يرسل رسالتك")
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(text="النص")
    async def say(self, ctx: commands.Context, *, text: str):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    # ═══════════════════════════════════════
    # 🧱 embed
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="embed", aliases=["امبد"], description="🧱 إرسال embed")
    @commands.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(title="العنوان", description="النص (افصل بـ | للعنوان والنص)")
    async def embed(self, ctx: commands.Context, title: str, *, description: str = None):
        if description is None and "|" in title:
            title, description = [x.strip() for x in title.split("|", 1)]
        embed = discord.Embed(
            title=title,
            description=description or title,
            color=Colors.INFO
        )
        if ctx.message.attachments:
            embed.set_image(url=ctx.message.attachments[0].url)
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📢 announce
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="announce", aliases=["اعلان", "اعلن"], description="📢 إعلان")
    @commands.has_permissions(mention_everyone=True)
    @app_commands.default_permissions(mention_everyone=True)
    @app_commands.describe(text="نص الإعلان")
    async def announce(self, ctx: commands.Context, *, text: str):
        try:
            await ctx.message.delete()
        except:
            pass
        embed = discord.Embed(
            title="📢 إعلان",
            description=text,
            color=Colors.GOLD
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))

    # ═══════════════════════════════════════
    # 📨 dm
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="dm", aliases=["خاص", "رسالة_خاصة"], description="📨 رسالة خاصة")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(member="العضو", message="الرسالة")
    async def dm(self, ctx: commands.Context, member: discord.Member, *, message: str):
        embed = discord.Embed(
            title=f"📨 رسالة من {ctx.guild.name}",
            description=message,
            color=Colors.INFO
        )
        try:
            await member.send(embed=embed)
            await ctx.send(f"✅ تم إرسال الرسالة لـ {member.mention}")
        except discord.Forbidden:
            await ctx.send("❌ العضو مقفل الخاص!")

    # ═══════════════════════════════════════
    # ➕ createrole
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="createrole", aliases=["انشاء_رتبة", "رتبة_جديدة"], description="➕ إنشاء رتبة")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(name="اسم الرتبة", color="اللون (مثل #FF0000)")
    async def createrole(self, ctx: commands.Context, name: str, color: str = None):
        color_value = discord.Color.default()
        if color:
            color = color.strip()
            if color.startswith("#"):
                color = color[1:]
            try:
                color_value = discord.Color(int(color, 16))
            except:
                pass
        try:
            role = await ctx.guild.create_role(name=name, color=color_value)
            embed = discord.Embed(
                title="✅ تم إنشاء الرتبة",
                description=f"{role.mention}",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أنشئ: `{e}`")

    # ═══════════════════════════════════════
    # 🗑️ deleterole
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="deleterole", aliases=["حذف_رتبة", "امسح_رتبة"], description="🗑️ حذف رتبة")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(role="الرتبة")
    async def deleterole(self, ctx: commands.Context, role: discord.Role):
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ الرتبة أعلى من رتبة البوت!")
            return
        name = role.name
        try:
            await role.delete()
            await ctx.send(f"✅ تم حذف الرتبة **{name}**")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أحذف: `{e}`")

    # ═══════════════════════════════════════
    # ➕ createchannel
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="createchannel", aliases=["انشاء_روم", "روم_جديد"], description="➕ إنشاء روم")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(name="اسم الروم", channel_type="نوع الروم (text/voice)")
    async def createchannel(self, ctx: commands.Context, name: str, channel_type: str = "text"):
        name = name.replace(" ", "-")[:90]
        try:
            if channel_type.lower() in ["voice", "صوتي"]:
                channel = await ctx.guild.create_voice_channel(name=name)
            else:
                channel = await ctx.guild.create_text_channel(name=name)
            await ctx.send(f"✅ تم إنشاء {channel.mention}")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أنشئ: `{e}`")

    # ═══════════════════════════════════════
    # 🗑️ deletechannel
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="deletechannel", aliases=["حذف_روم", "امسح_روم"], description="🗑️ حذف روم")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="الروم")
    async def deletechannel(self, ctx: commands.Context, channel: discord.TextChannel):
        name = channel.name
        try:
            await channel.delete()
            await ctx.send(f"✅ تم حذف الروم **{name}**")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أحذف: `{e}`")

    # ═══════════════════════════════════════
    # 🏷️ botname
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="botname", aliases=["اسم_البوت", "غير_اسم_البوت"], description="🏷️ تغيير اسم البوت")
    @app_commands.describe(name="الاسم الجديد")
    async def botname(self, ctx: commands.Context, *, name: str):
        if not is_owner(ctx.author.id):
            await ctx.send("❌ هذا الأمر لمالك البوت فقط!\nأضف ID في `OWNERS` في `.env`")
            return
        name = name[:32]
        try:
            await self.bot.user.edit(username=name)
            await ctx.send(f"✅ تم تغيير اسم البوت إلى **{name}**")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أغير: `{e}`")

    # ═══════════════════════════════════════
    # 🖼️ botavatar
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="botavatar", aliases=["صورة_البوت"], description="🖼️ تغيير صورة البوت")
    @app_commands.describe(url="رابط الصورة")
    async def botavatar(self, ctx: commands.Context, url: str = None):
        if not is_owner(ctx.author.id):
            await ctx.send("❌ هذا الأمر لمالك البوت فقط!\nأضف ID في `OWNERS` في `.env`")
            return
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if not url:
            await ctx.send("❌ اكتب رابط صورة أو أرفق صورة!")
            return
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await ctx.send("❌ ما قدرت أجيب الصورة!")
                        return
                    data = await resp.read()
            await self.bot.user.edit(avatar=data)
            await ctx.send("✅ تم تغيير صورة البوت")
        except Exception as e:
            await ctx.send(f"❌ ما قدرت أغير: `{e}`")

    # ═══════════════════════════════════════
    # 🛑 shutdown
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="shutdown", aliases=["اطفاء", "ايقاف_البوت"], description="🛑 إيقاف البوت")
    async def shutdown(self, ctx: commands.Context):
        if not is_owner(ctx.author.id):
            await ctx.send("❌ هذا الأمر لمالك البوت فقط!")
            return
        embed = discord.Embed(
            title="🛑 إيقاف البوت",
            description="جاري إيقاف البوت...",
            color=Colors.ERROR
        )
        await ctx.send(embed=embed)
        await self.bot.close()

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي الروم!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ مش لاقي الرتبة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Admin(bot))