import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from config import Colors

AUTOMATION_FILE = "automation.json"


def load_data():
    if os.path.exists(AUTOMATION_FILE):
        try:
            with open(AUTOMATION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(AUTOMATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_amount(text):
    """يحول 5k = 5000، 1m = 1000000"""
    if not text:
        return None
    t = text.lower().strip().replace(",", "")
    try:
        if t.endswith("k"):
            return int(float(t[:-1]) * 1000)
        if t.endswith("m"):
            return int(float(t[:-1]) * 1000000)
        return int(float(t))
    except:
        return None


def with_tax(amount):
    """حساب المبلغ مع ضريبة بروبوت"""
    # ضريبة بروبوت: المبلغ + 5% + 1% (تقريب)
    return int(amount / 0.95) + 1


class Automation(commands.Cog):
    """⚡ أوامر الأتمتة"""

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_guild_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.data:
            self.data[gid] = {
                "tax_channels": [],
                "tax_line": None,
                "image_channels": [],
                "youtube_channels": [],
                "react_channels": {},  # {channel_id: [emojis]}
                "feelings_channel": None,
                "feelings_anon": False,
                "boost_channel": None,
                "boost_message": "شكراً {user} على البوست 💜",
                "boost_embed": False
            }
        gd = self.data[gid]
        gd.setdefault("tax_channels", [])
        gd.setdefault("tax_line", None)
        gd.setdefault("image_channels", [])
        gd.setdefault("youtube_channels", [])
        gd.setdefault("react_channels", {})
        gd.setdefault("feelings_channel", None)
        gd.setdefault("feelings_anon", False)
        gd.setdefault("boost_channel", None)
        gd.setdefault("boost_message", "شكراً {user} على البوست 💜")
        gd.setdefault("boost_embed", False)
        return gd

    def save(self):
        save_data(self.data)

    # ═══════════════════════════════════════
    # 💳 tax
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="tax", aliases=["ضريبة"], description="💳 حساب ضريبة بروبوت")
    @app_commands.describe(amount="المبلغ (مثل 5000 أو 2.5k أو 1m)")
    async def tax(self, ctx: commands.Context, *, amount: str):
        amt = parse_amount(amount)
        if not amt or amt < 1:
            await ctx.send("❌ اكتب مبلغ صحيح (مثل `5000` أو `2.5k` أو `1m`)")
            return
        total = with_tax(amt)
        tax = total - amt
        embed = discord.Embed(title="💳 حساب الضريبة", color=Colors.GOLD)
        embed.add_field(name="💰 المبلغ اللي يوصل", value=f"`{amt:,}`", inline=True)
        embed.add_field(name="📤 المبلغ اللي تحوله", value=f"`{total:,}`", inline=True)
        embed.add_field(name="💸 الضريبة", value=f"`{tax:,}`", inline=True)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💳 autotax
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="autotax", aliases=["ضريبة_تلقائية"], description="💳 تفعيل الضريبة في روم")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="الروم (اختياري)")
    async def autotax(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        channels = gd["tax_channels"]
        if channel.id in channels:
            channels.remove(channel.id)
            msg = f"❌ تم إلغاء الضريبة من {channel.mention}"
        else:
            channels.append(channel.id)
            msg = f"✅ تم تفعيل الضريبة في {channel.mention}"
        gd["tax_channels"] = channels
        self.save()
        await ctx.send(msg)

    # ═══════════════════════════════════════
    # 💳 taxline
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="taxline", aliases=["ضريبة_خط"], description="💳 خط الضريبة")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(url="رابط أو نص أو 'حذف'")
    async def taxline(self, ctx: commands.Context, *, url: str = None):
        gd = self.get_guild_data(ctx.guild.id)
        if not url and ctx.message.attachments:
            url = ctx.message.attachments[0].url
        if url and url.lower() in ["حذف", "الغاء"]:
            gd["tax_line"] = None
            self.save()
            await ctx.send("✅ تم حذف خط الضريبة")
            return
        if not url:
            await ctx.send("❌ اكتب رابط أو نص أو `حذف`")
            return
        gd["tax_line"] = url[:500]
        self.save()
        await ctx.send("✅ تم حفظ خط الضريبة")

    # ═══════════════════════════════════════
    # 🖼️ imagesonly
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="imagesonly", aliases=["روم_صور", "صور_فقط"], description="🖼️ روم صور فقط")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="الروم (اختياري)")
    async def imagesonly(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        channels = gd["image_channels"]
        if channel.id in channels:
            channels.remove(channel.id)
            msg = f"❌ تم إلغاء وضع الصور من {channel.mention}"
        else:
            channels.append(channel.id)
            msg = f"✅ {channel.mention} روم صور فقط الآن"
        gd["image_channels"] = channels
        self.save()
        await ctx.send(msg)

    # ═══════════════════════════════════════
    # ▶️ youtubeonly
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="youtubeonly", aliases=["روم_يوتيوب", "يوتيوب_فقط"], description="▶️ روم يوتيوب فقط")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="الروم (اختياري)")
    async def youtubeonly(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        channels = gd["youtube_channels"]
        if channel.id in channels:
            channels.remove(channel.id)
            msg = f"❌ تم إلغاء وضع اليوتيوب من {channel.mention}"
        else:
            channels.append(channel.id)
            msg = f"✅ {channel.mention} روم يوتيوب فقط الآن"
        gd["youtube_channels"] = channels
        self.save()
        await ctx.send(msg)

    # ═══════════════════════════════════════
    # 😀 autoreact
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="autoreact", aliases=["تفاعل_تلقائي", "اوتو_رياكت"], description="😀 تفاعل تلقائي")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(add_reactions=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(emoji="الايموجي أو 'حذف'", channel="الروم (اختياري)")
    async def autoreact(self, ctx: commands.Context, emoji: str, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        reacts = gd["react_channels"]
        cid = str(channel.id)
        if emoji.lower() in ["حذف", "الغاء"]:
            if cid in reacts:
                del reacts[cid]
                gd["react_channels"] = reacts
                self.save()
                await ctx.send(f"✅ تم حذف التفاعلات من {channel.mention}")
            else:
                await ctx.send("❌ مفيش تفاعلات في هذا الروم!")
            return
        emojis = reacts.get(cid, [])
        if len(emojis) >= 5:
            await ctx.send("❌ الحد الأقصى 5 تفاعلات لكل روم!")
            return
        if emoji not in emojis:
            emojis.append(emoji)
        reacts[cid] = emojis
        gd["react_channels"] = reacts
        self.save()
        await ctx.send(f"✅ كل رسالة في {channel.mention} هتاخد تفاعل {' '.join(emojis)}")

    # ═══════════════════════════════════════
    # 💭 feelings
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="feelings", aliases=["مشاعر", "روم_مشاعر"], description="💭 روم المشاعر")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="الروم (اختياري)")
    async def feelings(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gd = self.get_guild_data(ctx.guild.id)
        if gd["feelings_channel"] == channel.id:
            gd["feelings_channel"] = None
            self.save()
            await ctx.send(f"❌ تم إلغاء روم المشاعر")
            return
        gd["feelings_channel"] = channel.id
        self.save()
        anon = " (مجهول)" if gd["feelings_anon"] else ""
        await ctx.send(f"✅ {channel.mention} روم مشاعر الآن{anon}")

    # ═══════════════════════════════════════
    # 🕶️ feelingsanon
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="feelingsanon", aliases=["مشاعر_مجهول", "مشاعر_سرية"], description="🕶️ مشاعر مجهولة")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def feelingsanon(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        gd["feelings_anon"] = not gd["feelings_anon"]
        self.save()
        if gd["feelings_anon"]:
            await ctx.send("✅ الكتابة في روم المشاعر صارت مجهولة 🕶️")
        else:
            await ctx.send("✅ يظهر اسم الكاتب في روم المشاعر")

    # ═══════════════════════════════════════
    # 💜 boostmsg
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="boostmsg", aliases=["بوست_اعداد", "شكر_البوست"], description="💜 رسالة شكر البوست")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="الروم أو 'حذف'", message="الرسالة (اختياري)")
    async def boostmsg(self, ctx: commands.Context, channel: str, *, message: str = None):
        gd = self.get_guild_data(ctx.guild.id)
        if channel.lower() in ["حذف", "الغاء"]:
            gd["boost_channel"] = None
            self.save()
            await ctx.send("✅ تم إلغاء رسالة شكر البوست")
            return
        ch = None
        if ctx.message.channel_mentions:
            ch = ctx.message.channel_mentions[0]
        elif channel.isdigit():
            ch = ctx.guild.get_channel(int(channel))
        if not ch:
            await ctx.send("❌ منشن الروم!")
            return
        gd["boost_channel"] = ch.id
        if message:
            gd["boost_message"] = message[:1500]
        self.save()
        await ctx.send(f"✅ رسالة الشكر هتروح إلى {ch.mention}")

    # ═══════════════════════════════════════
    # ⚡ automation
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="automation", aliases=["اتمتة", "الاتمتة"], description="⚡ عرض إعدادات الأتمتة")
    @commands.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
    async def automation(self, ctx: commands.Context):
        gd = self.get_guild_data(ctx.guild.id)
        channels = lambda ids: " ".join(f"<#{i}>" for i in ids) if ids else "لا يوجد"
        reacts = "\n".join(f"<#{cid}> {' '.join(ems)}" for cid, ems in gd["react_channels"].items()) or "لا يوجد"
        embed = discord.Embed(title="⚡ إعدادات الأتمتة", color=Colors.INFO)
        embed.add_field(name="💳 الضريبة التلقائية", value=channels(gd["tax_channels"]), inline=False)
        embed.add_field(name="🖼️ رومات الصور", value=channels(gd["image_channels"]), inline=False)
        embed.add_field(name="▶️ رومات اليوتيوب", value=channels(gd["youtube_channels"]), inline=False)
        embed.add_field(name="😀 التفاعل التلقائي", value=reacts[:1024], inline=False)
        embed.add_field(name="💭 روم المشاعر", value=f"<#{gd['feelings_channel']}>" if gd["feelings_channel"] else "لا يوجد", inline=True)
        embed.add_field(name="💜 شكر البوست", value=f"<#{gd['boost_channel']}>" if gd["boost_channel"] else "لا يوجد", inline=True)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📨 on_message — الأتمتة
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        gd = self.get_guild_data(message.guild.id)
        cid = str(message.channel.id)
        
        # ضريبة تلقائية
        if message.channel.id in gd["tax_channels"]:
            amt = parse_amount(message.content)
            if amt and amt >= 1:
                total = with_tax(amt)
                tax = total - amt
                embed = discord.Embed(color=Colors.GOLD)
                embed.add_field(name="💰 يوصل", value=f"`{amt:,}`", inline=True)
                embed.add_field(name="📤 يحول", value=f"`{total:,}`", inline=True)
                embed.add_field(name="💸 الضريبة", value=f"`{tax:,}`", inline=True)
                await message.reply(embed=embed, mention_author=False)
                if gd["tax_line"]:
                    if gd["tax_line"].startswith("http"):
                        line_embed = discord.Embed(color=Colors.GOLD)
                        line_embed.set_image(url=gd["tax_line"])
                        await message.channel.send(embed=line_embed)
                    else:
                        await message.channel.send(gd["tax_line"])
        
        # روم صور فقط
        if message.channel.id in gd["image_channels"]:
            has_image = any(a.content_type and a.content_type.startswith("image/") for a in message.attachments)
            has_embed_image = any(e.image or e.thumbnail for e in message.embeds)
            if not (has_image or has_embed_image):
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} روم صور فقط!", delete_after=5)
                except:
                    pass
        
        # روم يوتيوب فقط
        if message.channel.id in gd["youtube_channels"]:
            content = message.content.lower()
            is_yt = "youtube.com" in content or "youtu.be" in content
            if not is_yt:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} روم يوتيوب فقط!", delete_after=5)
                except:
                    pass
        
        # تفاعل تلقائي
        if cid in gd["react_channels"]:
            for emoji in gd["react_channels"][cid]:
                try:
                    await message.add_reaction(emoji)
                except:
                    pass
        
        # روم مشاعر
        if message.channel.id == gd["feelings_channel"]:
            content = message.content
            try:
                await message.delete()
            except:
                pass
            embed = discord.Embed(description=content, color=0x9B59B6, timestamp=discord.utils.utcnow())
            if not gd["feelings_anon"]:
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            else:
                embed.set_author(name="مجهول", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
            await message.channel.send(embed=embed)

    # ═══════════════════════════════════════
    # 💜 Boost event
    # ═══════════════════════════════════════
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # لما عضو يعمل boost
        if before.premium_since is None and after.premium_since is not None:
            gd = self.get_guild_data(after.guild.id)
            if gd["boost_channel"]:
                ch = after.guild.get_channel(int(gd["boost_channel"]))
                if ch:
                    msg = gd["boost_message"].replace("{user}", after.mention).replace("{server}", after.guild.name)
                    try:
                        if gd["boost_embed"]:
                            embed = discord.Embed(description=msg, color=0x9B59B6)
                            await ch.send(embed=embed)
                        else:
                            await ch.send(msg)
                    except:
                        pass

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده الصلاحيات!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ مش لاقي القناة!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Automation(bot))