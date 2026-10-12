import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from config import Colors


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 🏓 !ping / /ping
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="ping",
        aliases=["بنق"],
        description="🏓 عرض سرعة استجابة البوت"
    )
    async def ping(self, ctx: commands.Context):
        """عرض سرعة استجابة البوت"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 بونغ!",
            description=f"**سرعة الاستجابة:** `{latency}ms`",
            color=Colors.SUCCESS
        )
        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🖼️ !avatar / /avatar
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "صورة"],
        description="🖼️ عرض الصورة الشخصية"
    )
    @app_commands.describe(member="العضو المراد عرض صورته (اختياري)")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """عرض صورة عضو"""
        member = member or ctx.author
        embed = discord.Embed(title=f"🖼️ صورة {member.display_name}", color=Colors.INFO)
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="PNG",
            url=str(member.display_avatar.replace(format='png', size=1024)),
            style=discord.ButtonStyle.link
        ))
        view.add_item(discord.ui.Button(
            label="JPG",
            url=str(member.display_avatar.replace(format='jpg', size=1024)),
            style=discord.ButtonStyle.link
        ))
        view.add_item(discord.ui.Button(
            label="WEBP",
            url=str(member.display_avatar.replace(format='webp', size=1024)),
            style=discord.ButtonStyle.link
        ))
        await ctx.send(embed=embed, view=view)

    # ═══════════════════════════════════════
    # 🎨 !banner / /banner
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="banner",
        aliases=["bn", "بانر"],
        description="🎨 عرض بانر عضو"
    )
    @app_commands.describe(member="العضو المراد عرض بانره (اختياري)")
    async def banner(self, ctx: commands.Context, member: discord.Member = None):
        """عرض بانر عضو"""
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            await ctx.send(f"❌ {member.mention} لا يمتلك بانر!")
            return
        embed = discord.Embed(title=f"🎨 بانر {member.display_name}", color=Colors.INFO)
        embed.set_image(url=user.banner.url)
        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👤 !user / /user
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="user",
        aliases=["userinfo", "معلومات"],
        description="👤 عرض معلومات عضو"
    )
    @app_commands.describe(member="العضو المراد عرض معلوماته (اختياري)")
    async def user(self, ctx: commands.Context, member: discord.Member = None):
        """عرض معلومات عضو"""
        member = member or ctx.author

        joined_at = discord.utils.format_dt(member.joined_at, style='R')
        created_at = discord.utils.format_dt(member.created_at, style='R')
        top_role = member.top_role.mention if member.top_role != ctx.guild.default_role else "لا يوجد"

        embed = discord.Embed(
            title=f"👤 معلومات {member.display_name}",
            color=member.color if member.color != discord.Color.default() else Colors.INFO
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 المعرف", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📛 الاسم الكامل", value=f"{member}", inline=True)
        embed.add_field(name="👑 أعلى رتبة", value=top_role, inline=True)
        embed.add_field(name="📅 تاريخ الانضمام", value=joined_at, inline=False)
        embed.add_field(name="🎂 تاريخ إنشاء الحساب", value=created_at, inline=False)

        roles = [role.mention for role in member.roles[1:]]
        if roles:
            roles_text = ", ".join(roles[:20])
            if len(roles) > 20:
                roles_text += f" ... و {len(roles) - 20} رتب أخرى"
            embed.add_field(name=f"🎭 الرتب [{len(roles)}]", value=roles_text, inline=False)

        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🏰 !server / /server
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="server",
        aliases=["serverinfo", "سيرفر"],
        description="🏰 عرض معلومات السيرفر"
    )
    async def server(self, ctx: commands.Context):
        """عرض معلومات السيرفر"""
        guild = ctx.guild

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

        embed = discord.Embed(title=f"🏰 معلومات {guild.name}", color=Colors.INFO)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="🆔 المعرف", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 المالك", value=guild.owner.mention if guild.owner else "غير معروف", inline=True)
        embed.add_field(name="📅 تاريخ الإنشاء", value=created_at, inline=True)
        embed.add_field(
            name="👥 الأعضاء",
            value=f"**الإجمالي:** {total_members}\n**بشر:** {humans}\n**بوتات:** {bots}",
            inline=True
        )
        embed.add_field(
            name="💬 القنوات",
            value=f"**نصية:** {text_channels}\n**صوتية:** {voice_channels}\n**فئات:** {categories}",
            inline=True
        )
        embed.add_field(name="🎭 الرتب", value=f"`{roles_count}` رتبة", inline=True)
        embed.add_field(name="😀 الإيموجيات", value=f"`{emojis_count}` إيموجي", inline=True)
        embed.add_field(name="🔒 مستوى التحقق", value=verification, inline=True)
        embed.add_field(name="🚀 مستوى البوست", value=f"Level {guild.premium_tier.value}", inline=True)

        if guild.description:
            embed.add_field(name="📝 الوصف", value=guild.description, inline=False)

        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💎 !volt / /volt
    # ═══════════════════════════════════════
    @commands.hybrid_command(
        name="volt",
        aliases=["فولت"],
        description="💎 عرض رصيد Crypto لعضو"
    )
    @app_commands.describe(
        member="العضو المراد عرض رصيده (اختياري)",
        amount="المبلغ المراد إضافته أو خصمه (للمشرفين فقط)"
    )
    async def volt(self, ctx: commands.Context, member: discord.Member = None, amount: int = None):
        """عرض أو تعديل رصيد Crypto"""
        member = member or ctx.author
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
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ صلاحية مطلوبة: يجب أن تكون مشرفاً!")
                return

            if user_id not in bitcoin_data:
                bitcoin_data[user_id] = {
                    "balance": 0,
                    "total_earned": 0,
                    "total_spent": 0,
                    "transactions": [],
                    "inventory": []
                }

            bitcoin_data[user_id]["balance"] += amount

            with open(bitcoin_file, "w", encoding="utf-8") as f:
                json.dump(bitcoin_data, f, ensure_ascii=False, indent=2)

            action = "إضافة" if amount > 0 else "خصم"
            embed = discord.Embed(
                title="💎 تم تعديل الرصيد",
                description=(
                    f"✅ تم {action} **{abs(amount)} ₿** إلى حساب {member.mention}\n\n"
                    f"**الرصيد الجديد:** `{bitcoin_data[user_id]['balance']} ₿`"
                ),
                color=Colors.SUCCESS
            )
        else:
            embed = discord.Embed(
                title=f"💎 رصيد {member.display_name}",
                description=f"**الرصيد الحالي:** `{balance} ₿`",
                color=Colors.GOLD
            )
            embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(
            text=f"طلب بواسطة: {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))