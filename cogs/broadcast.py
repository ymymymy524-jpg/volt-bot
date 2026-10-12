import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime

BROADCAST_FILE = "broadcasts.json"


def load_data():
    if os.path.exists(BROADCAST_FILE):
        try:
            with open(BROADCAST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(BROADCAST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Broadcast(commands.Cog):
    """📢 نظام البرودكاست — إرسال رسائل في الخاص لكل الأعضاء"""

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.active_broadcasts = {}

    # ═══════════════════════════════════════
    # 📢 !broadcast — إرسال رسالة نصية
    # ═══════════════════════════════════════
    @commands.command(
        name="broadcast",
        aliases=["bc", "برودكاست", "اعلان"],
        description="📢 إرسال رسالة في الخاص لكل الأعضاء"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def broadcast(self, ctx: commands.Context, *, message: str = None):
        """إرسال رسالة نصية لكل الأعضاء في الخاص"""
        if not message:
            await ctx.send(
                "❌ **الاستخدام الصحيح:**\n"
                "`!broadcast <الرسالة>`\n\n"
                "**مثال:** `!broadcast مرحباً بالجميع، عندنا حدث جديد!`",
                delete_after=10
            )
            return

        if ctx.guild.id in self.active_broadcasts:
            await ctx.send("⚠️ فيه برودكاست شغال بالفعل! استنى يخلص أو استخدم `!broadcast-cancel`", delete_after=10)
            return

        embed = discord.Embed(
            title="📢 تأكيد البرودكاست",
            description=(
                f"**الرسالة:**\n{message}\n\n"
                f"**عدد الأعضاء:** `{ctx.guild.member_count}`\n"
                f"**الوقت المتوقع:** ~`{int(ctx.guild.member_count * 1.2 // 60)}` دقيقة\n\n"
                "⚠️ **تحذير:** العملية دي مش هتتوقف بمجرد ما تبدأ!\n"
                "هتاخد وقت طويل عشان نتفادى الـ rate limit."
            ),
            color=0xE67E22
        )
        embed.set_footer(text="اضغط ✅ للتأكيد أو ❌ للإلغاء")

        view = ConfirmView(self, ctx, message, "text")
        await ctx.send(embed=embed, view=view)

    # ═══════════════════════════════════════
    # 📢 !broadcast-embed — إرسال embed
    # ═══════════════════════════════════════
    @commands.command(
        name="broadcast-embed",
        aliases=["bce", "برودكاست-ايمبد"],
        description="📢 إرسال Embed في الخاص لكل الأعضاء"
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def broadcast_embed(self, ctx: commands.Context, *, args: str = None):
        """إرسال embed لكل الأعضاء في الخاص"""
        if not args or "|" not in args:
            await ctx.send(
                "❌ **الاستخدام الصحيح:**\n"
                "`!broadcast-embed العنوان | الوصف`\n\n"
                "**مثال:** `!broadcast-embed حدث جديد | عندنا حدث مميز النهارده!`",
                delete_after=12
            )
            return

        title, description = args.split("|", 1)
        title = title.strip()
        description = description.strip()

        if not title or not description:
            await ctx.send("❌ لازم تحط العنوان والوصف، مفصولين بـ `|`", delete_after=10)
            return

        if ctx.guild.id in self.active_broadcasts:
            await ctx.send("⚠️ فيه برودكاست شغال بالفعل! استنى يخلص أو استخدم `!broadcast-cancel`", delete_after=10)
            return

        embed = discord.Embed(
            title="📢 تأكيد برودكاست Embed",
            description=(
                f"**العنوان:** {title}\n"
                f"**الوصف:** {description}\n\n"
                f"**عدد الأعضاء:** `{ctx.guild.member_count}`\n"
                f"**الوقت المتوقع:** ~`{int(ctx.guild.member_count * 1.2 // 60)}` دقيقة"
            ),
            color=0xE67E22
        )
        embed.set_footer(text="اضغط ✅ للتأكيد أو ❌ للإلغاء")

        view = ConfirmView(self, ctx, f"{title}|{description}", "embed")
        await ctx.send(embed=embed, view=view)

    # ═══════════════════════════════════════
    # 🚀 تنفيذ البرودكاست
    # ═══════════════════════════════════════
    async def _run_broadcast(self, ctx, content, bc_type):
        """تنفيذ البرودكاست"""
        guild = ctx.guild

        self.active_broadcasts[guild.id] = {
            "started_at": datetime.now().isoformat(),
            "by": ctx.author.id,
            "content": content,
            "sent": 0,
            "failed": 0,
            "total": 0
        }

        start_embed = discord.Embed(
            title="📢 بدأ البرودكاست",
            description="**جاري الإرسال...**\nهيتم إرسال رسالة لكل عضو في السيرفر",
            color=0x3498DB
        )
        status_msg = await ctx.send(embed=start_embed)

        sent = 0
        failed = 0

        members = [m for m in guild.members if not m.bot]
        total = len(members)

        for i, member in enumerate(members, 1):
            if guild.id not in self.active_broadcasts:
                cancel_embed = discord.Embed(
                    title="🛑 تم إلغاء البرودكاست",
                    description=f"**تم الإرسال:** `{sent}`\n**فشل:** `{failed}`",
                    color=0xE74C3C
                )
                await status_msg.edit(embed=cancel_embed)
                return

            try:
                if bc_type == "text":
                    await member.send(content)
                else:
                    title, description = content.split("|", 1)
                    embed = discord.Embed(
                        title=f"📢 {title.strip()}",
                        description=description.strip(),
                        color=0x9B59B6,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.set_footer(
                        text=f"من سيرفر {guild.name}",
                        icon_url=guild.icon.url if guild.icon else None
                    )
                    await member.send(embed=embed)
                sent += 1
            except discord.Forbidden:
                failed += 1
            except discord.HTTPException:
                failed += 1
                await asyncio.sleep(2)

            if i % 10 == 0:
                progress_embed = discord.Embed(
                    title="📢 جاري الإرسال...",
                    description=(
                        f"**التقدم:** `{i}/{total}`\n"
                        f"✅ **تم الإرسال:** `{sent}`\n"
                        f"❌ **فشل:** `{failed}`\n"
                        f"📊 **النسبة:** `{int(i * 100 / total)}%`"
                    ),
                    color=0x3498DB
                )
                try:
                    await status_msg.edit(embed=progress_embed)
                except:
                    pass

            await asyncio.sleep(1.2)

        self.data.setdefault(str(guild.id), []).append({
            "started_at": self.active_broadcasts[guild.id]["started_at"],
            "finished_at": datetime.now().isoformat(),
            "by": ctx.author.id,
            "sent": sent,
            "failed": failed,
            "total": total,
            "content": content[:100]
        })
        save_data(self.data)

        del self.active_broadcasts[guild.id]

        finish_embed = discord.Embed(
            title="✅ اكتمل البرودكاست",
            description=(
                f"**الإجمالي:** `{total}`\n"
                f"✅ **تم الإرسال:** `{sent}`\n"
                f"❌ **فشل:** `{failed}`\n"
                f"📊 **نسبة النجاح:** `{int(sent * 100 / total) if total > 0 else 0}%`"
            ),
            color=0x2ECC71,
            timestamp=discord.utils.utcnow()
        )
        await status_msg.edit(embed=finish_embed)

    # ═══════════════════════════════════════
    # 🛑 !broadcast-cancel — إلغاء
    # ═══════════════════════════════════════
    @commands.command(
        name="broadcast-cancel",
        aliases=["bcc", "الغاء-البرودكاست"],
        description="🛑 إلغاء البرودكاست الجاري"
    )
    @commands.has_permissions(administrator=True)
    async def broadcast_cancel(self, ctx: commands.Context):
        """إلغاء البرودكاست الجاري"""
        if ctx.guild.id not in self.active_broadcasts:
            await ctx.send("❌ مفيش برودكاست شغال حالياً!", delete_after=8)
            return

        del self.active_broadcasts[ctx.guild.id]
        await ctx.send("🛑 تم إلغاء البرودكاست!")

    # ═══════════════════════════════════════
    # 📊 !broadcast-status — الحالة
    # ═══════════════════════════════════════
    @commands.command(
        name="broadcast-status",
        aliases=["bcs", "حالة-البرودكاست"],
        description="📊 عرض حالة البرودكاست"
    )
    @commands.has_permissions(administrator=True)
    async def broadcast_status(self, ctx: commands.Context):
        """عرض حالة البرودكاست"""
        if ctx.guild.id in self.active_broadcasts:
            bc = self.active_broadcasts[ctx.guild.id]
            embed = discord.Embed(
                title="📢 برودكاست شغال حالياً",
                description=(
                    f"**بدأ:** <t:{int(datetime.fromisoformat(bc['started_at']).timestamp())}:R>\n"
                    f"**بواسطة:** <@{bc['by']}>\n"
                    f"✅ **تم الإرسال:** `{bc['sent']}`\n"
                    f"❌ **فشل:** `{bc['failed']}`"
                ),
                color=0x3498DB
            )
            await ctx.send(embed=embed)
        else:
            guild_data = self.data.get(str(ctx.guild.id), [])
            if not guild_data:
                await ctx.send("📭 مفيش برودكاستات مسجلة!", delete_after=8)
                return

            recent = guild_data[-5:]
            desc = ""
            for i, bc in enumerate(reversed(recent), 1):
                desc += (
                    f"**{i}.** <t:{int(datetime.fromisoformat(bc['finished_at']).timestamp())}:R>\n"
                    f"   ✅ `{bc['sent']}` | ❌ `{bc['failed']}` | 📊 `{bc['total']}`\n"
                )
            embed = discord.Embed(
                title="📊 آخر 5 برودكاستات",
                description=desc,
                color=0x9B59B6
            )
            await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ⚠️ معالجة الأخطاء
    # ═══════════════════════════════════════
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت مفيش عنده صلاحية **Administrator**!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص بيانات: `{error.param.name}`", delete_after=8)
        else:
            print(f"❌ خطأ في أمر {ctx.command}: {error}")


# ═══════════════════════════════════════
# 🎛️ View للتأكيد
# ═══════════════════════════════════════
class ConfirmView(discord.ui.View):
    def __init__(self, cog, ctx, content, bc_type):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.content = content
        self.bc_type = bc_type

    @discord.ui.button(label="تأكيد", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ ده مش أمرك!", ephemeral=True)

        await interaction.response.edit_message(
            content="✅ **تم التأكيد — جاري بدء البرودكاست...**",
            embed=None,
            view=None
        )

        await self.cog._run_broadcast(self.ctx, self.content, self.bc_type)

    @discord.ui.button(label="إلغاء", emoji="❌", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ ده مش أمرك!", ephemeral=True)

        await interaction.response.edit_message(
            content="❌ **تم إلغاء البرودكاست**",
            embed=None,
            view=None
        )


async def setup(bot):
    await bot.add_cog(Broadcast(bot))