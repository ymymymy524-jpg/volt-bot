import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

# ═══════════════════════════════════════
# 📁 إعدادات
# ═══════════════════════════════════════
BITCOIN_FILE = "bitcoin.json"
COIN_NAME = "Crypto"
COIN_SYMBOL = "₿"

# عناصر المتجر
SHOP_ITEMS = {
    "crown": {"name": "👑 تاج", "price": 5000, "description": "تاج ذهبي يظهر في بروفايلك"},
    "ring": {"name": "💍 خاتم", "price": 2000, "description": "خاتم ألماسي"},
    "car": {"name": "🚗 سيارة", "price": 10000, "description": "سيارة رياضية"},
    "house": {"name": "🏠 منزل", "price": 50000, "description": "منزل فاخر"},
    "yacht": {"name": "🛥️ يخت", "price": 100000, "description": "يخت خاص"},
    "rocket": {"name": "🚀 صاروخ", "price": 250000, "description": "صاروخ للفضاء"},
    "diamond": {"name": "💎 ألماسة", "price": 1000, "description": "ألماسة نادرة"},
    "trophy": {"name": "🏆 كأس", "price": 3000, "description": "كأس الفوز"},
}


# ═══════════════════════════════════════
# 📂 دوال التحميل والحفظ
# ═══════════════════════════════════════
def load_data():
    if os.path.exists(BITCOIN_FILE):
        try:
            with open(BITCOIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(BITCOIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Economy(commands.Cog):
    """نظام الاقتصاد — Crypto"""

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "last_daily": None,
                "last_work": None,
                "transactions": [],
                "inventory": []
            }
        return self.data[uid]

    def save(self):
        save_data(self.data)

    def add_transaction(self, user_id, tx_type, amount, description):
        user = self.get_user(user_id)
        user["transactions"].append({
            "type": tx_type,
            "amount": amount,
            "description": description,
            "timestamp": discord.utils.utcnow().isoformat()
        })
        if len(user["transactions"]) > 50:
            user["transactions"] = user["transactions"][-50:]

    # ═══════════════════════════════════════
    # 🌐 SLASH COMMANDS
    # ═══════════════════════════════════════

    @app_commands.command(name="balance", description="💰 عرض رصيد Crypto")
    @app_commands.describe(member="العضو (اختياري)")
    async def balance_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = self.get_user(target.id)

        embed = discord.Embed(
            title=f"💎 محفظة {COIN_NAME} — {target.display_name}",
            color=0xF7931A,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 الرصيد", value=f"**{user['balance']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📈 المكتسب", value=f"**{user['total_earned']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📉 المنفق", value=f"**{user['total_spent']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="🎒 العناصر", value=f"**{len(user.get('inventory', []))}**", inline=True)
        embed.set_footer(text=f"ID: {target.id}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="🎁 استلام المكافأة اليومية (100-500 ₿)")
    async def daily_slash(self, interaction: discord.Interaction):
        user = self.get_user(interaction.user.id)
        now = discord.utils.utcnow()

        if user.get("last_daily"):
            last = datetime.fromisoformat(user["last_daily"])
            diff = (now - last).total_seconds()
            if diff < 86400:
                remaining = 86400 - diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return await interaction.response.send_message(
                    f"⏰ استلمت بالفعل! ارجع بعد **{hours}س {minutes}د**",
                    ephemeral=True
                )

        amount = random.randint(100, 500)
        user["balance"] += amount
        user["total_earned"] += amount
        user["last_daily"] = now.isoformat()
        self.add_transaction(interaction.user.id, "daily", amount, "مكافأة يومية")
        self.save()

        embed = discord.Embed(
            title="🎁 المكافأة اليومية",
            description=f"حصلت على **{amount} {COIN_SYMBOL}**!",
            color=0xF7931A
        )
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="💼 اشتغل واكسب Crypto (50-200 ₿)")
    async def work_slash(self, interaction: discord.Interaction):
        user = self.get_user(interaction.user.id)
        now = discord.utils.utcnow()

        if user.get("last_work"):
            last = datetime.fromisoformat(user["last_work"])
            diff = (now - last).total_seconds()
            if diff < 3600:
                remaining = 3600 - diff
                minutes = int(remaining // 60)
                return await interaction.response.send_message(
                    f"⏰ ارتاح شوية! ارجع بعد **{minutes}د**",
                    ephemeral=True
                )

        jobs = ["مبرمج 👨‍💻", "طبيب 👨‍⚕️", "مهندس 👷", "معلم 👨‍🏫",
                "طباخ 👨‍🍳", "فنان 🎨", "كاتب ✍️", "مصور 📸",
                "سائق 🚗", "مزارع 🌾", "صائد سمك 🎣", "نجار 🔨"]
        job = random.choice(jobs)
        amount = random.randint(50, 200)

        user["balance"] += amount
        user["total_earned"] += amount
        user["last_work"] = now.isoformat()
        self.add_transaction(interaction.user.id, "work", amount, f"عمل كـ {job}")
        self.save()

        embed = discord.Embed(
            title=f"💼 {job}",
            description=f"اشتغلت وكسبت **{amount} {COIN_SYMBOL}**!",
            color=0x3498DB
        )
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="transfer", description="💸 تحويل Crypto لعضو")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def transfer_slash(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1]):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ متحولش لنفسك!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ متحولش لبوت!", ephemeral=True)

        sender = self.get_user(interaction.user.id)
        if sender["balance"] < amount:
            return await interaction.response.send_message(
                f"❌ رصيدك مش كفاية! عندك **{sender['balance']:,} {COIN_SYMBOL}**",
                ephemeral=True
            )

        receiver = self.get_user(member.id)
        sender["balance"] -= amount
        sender["total_spent"] += amount
        receiver["balance"] += amount
        receiver["total_earned"] += amount

        self.add_transaction(interaction.user.id, "transfer_out", -amount, f"تحويل إلى {member.display_name}")
        self.add_transaction(member.id, "transfer_in", amount, f"تحويل من {interaction.user.display_name}")
        self.save()

        embed = discord.Embed(
            title="💸 تم التحويل",
            description=f"حولت **{amount:,} {COIN_SYMBOL}** لـ {member.mention}",
            color=0x2ECC71
        )
        embed.set_footer(text=f"رصيدك: {sender['balance']:,} {COIN_SYMBOL}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bitcoin-top", description="🏆 أغنى 10 أعضاء")
    async def top_slash(self, interaction: discord.Interaction):
        if not self.data:
            return await interaction.response.send_message("📭 مفيش بيانات!")

        sorted_users = sorted(self.data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""

        for i, (uid, data) in enumerate(sorted_users):
            member = interaction.guild.get_member(int(uid))
            if not member:
                continue
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{member.display_name}** — `{data.get('balance', 0):,}` {COIN_SYMBOL}\n"

        embed = discord.Embed(title=f"🏆 أغنى 10 أعضاء في {COIN_NAME}",
                              description=desc or "لا توجد بيانات",
                              color=0xF7931A)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bitcoin-history", description="📜 سجل معاملاتك")
    async def history_slash(self, interaction: discord.Interaction):
        user = self.get_user(interaction.user.id)
        embed = discord.Embed(title=f"📜 سجل {interaction.user.display_name}", color=0x3498DB)
        embed.add_field(name="💰 الرصيد", value=f"`{user['balance']:,}` {COIN_SYMBOL}", inline=False)
        embed.add_field(name="📈 المكتسب", value=f"`{user['total_earned']:,}` {COIN_SYMBOL}", inline=False)
        embed.add_field(name="📉 المنفق", value=f"`{user['total_spent']:,}` {COIN_SYMBOL}", inline=False)
        embed.add_field(name="🎒 العناصر", value=f"`{len(user.get('inventory', []))}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="🛒 متجر Crypto")
    async def shop_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🛒 متجر {COIN_NAME}",
            description="اشترِ حاجات رائعة بالـ Crypto!",
            color=0xF7931A
        )
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['name']}",
                value=f"💰 `{item['price']:,}` {COIN_SYMBOL}\n📝 {item['description']}",
                inline=False
            )
        embed.set_footer(text="استخدم /buy لشراء عنصر")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="💳 شراء من المتجر")
    @app_commands.describe(item="معرف العنصر (من /shop)")
    @app_commands.choices(item=[
        app_commands.Choice(name="👑 تاج (5000 ₿)", value="crown"),
        app_commands.Choice(name="💍 خاتم (2000 ₿)", value="ring"),
        app_commands.Choice(name="🚗 سيارة (10000 ₿)", value="car"),
        app_commands.Choice(name="🏠 منزل (50000 ₿)", value="house"),
        app_commands.Choice(name="🛥️ يخت (100000 ₿)", value="yacht"),
        app_commands.Choice(name="🚀 صاروخ (250000 ₿)", value="rocket"),
        app_commands.Choice(name="💎 ألماسة (1000 ₿)", value="diamond"),
        app_commands.Choice(name="🏆 كأس (3000 ₿)", value="trophy"),
    ])
    async def buy_slash(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        item_id = item.value
        item_data = SHOP_ITEMS.get(item_id)

        if not item_data:
            return await interaction.response.send_message("❌ العنصر مش موجود", ephemeral=True)

        user = self.get_user(interaction.user.id)
        price = item_data["price"]

        if user["balance"] < price:
            return await interaction.response.send_message(
                f"❌ رصيدك مش كفاية!\nعندك: `{user['balance']:,}` {COIN_SYMBOL}\nالسعر: `{price:,}` {COIN_SYMBOL}",
                ephemeral=True
            )

        user["balance"] -= price
        user["total_spent"] += price
        user.setdefault("inventory", []).append(item_id)
        self.add_transaction(interaction.user.id, "buy", -price, f"شراء {item_data['name']}")
        self.save()

        embed = discord.Embed(
            title="✅ تم الشراء",
            description=f"اشتريت **{item_data['name']}**!\n\nالسعر: `{price:,}` {COIN_SYMBOL}\nرصيدك: `{user['balance']:,}` {COIN_SYMBOL}",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 🛠️ Admin Group
    # ═══════════════════════════════════════
    admin_group = app_commands.Group(
        name="bitcoin-admin",
        description="أدوات إدارة Crypto",
        default_permissions=discord.Permissions(administrator=True)
    )

    @admin_group.command(name="add", description="➕ إضافة Crypto لعضو")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def admin_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] += amount
        user["total_earned"] += amount
        self.add_transaction(member.id, "admin", amount, "إضافة من المشرف")
        self.save()

        embed = discord.Embed(
            title="✅ تم الإضافة",
            description=f"أضفت `{amount:,}` {COIN_SYMBOL} لـ {member.mention}",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=embed)

    @admin_group.command(name="remove", description="➖ خصم Crypto من عضو")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def admin_remove(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] = max(0, user["balance"] - amount)
        user["total_spent"] += amount
        self.add_transaction(member.id, "admin", -amount, "خصم من المشرف")
        self.save()

        embed = discord.Embed(
            title="✅ تم الخصم",
            description=f"خصمت `{amount:,}` {COIN_SYMBOL} من {member.mention}",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed)

    @admin_group.command(name="set", description="⚙️ تعيين رصيد عضو")
    @app_commands.describe(member="العضو", amount="المبلغ الجديد")
    async def admin_set(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] = amount
        self.add_transaction(member.id, "admin", amount, "تعيين الرصيد")
        self.save()

        embed = discord.Embed(
            title="✅ تم التعيين",
            description=f"رصيد {member.mention} بقى `{amount:,}` {COIN_SYMBOL}",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed)

    @admin_group.command(name="reset", description="🔄 تصفير عضو")
    @app_commands.describe(member="العضو")
    async def admin_reset(self, interaction: discord.Interaction, member: discord.Member):
        self.data[str(member.id)] = {
            "balance": 0,
            "total_earned": 0,
            "total_spent": 0,
            "last_daily": None,
            "last_work": None,
            "transactions": [],
            "inventory": []
        }
        self.save()

        embed = discord.Embed(
            title="🔄 تم التصفير",
            description=f"تم تصفير بيانات {member.mention}",
            color=0xE67E22
        )
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 📨 TEXT COMMANDS (للاختصارات)
    # ═══════════════════════════════════════

    @commands.command(name="balance", aliases=["bal"])
    async def balance_text(self, ctx, member: discord.Member = None):
        """!balance — عرض الرصيد"""
        target = member or ctx.author
        user = self.get_user(target.id)

        embed = discord.Embed(
            title=f"💎 محفظة {COIN_NAME} — {target.display_name}",
            color=0xF7931A
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 الرصيد", value=f"**{user['balance']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📈 المكتسب", value=f"**{user['total_earned']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📉 المنفق", value=f"**{user['total_spent']:,} {COIN_SYMBOL}**", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily_text(self, ctx):
        """!daily — المكافأة اليومية"""
        user = self.get_user(ctx.author.id)
        now = discord.utils.utcnow()

        if user.get("last_daily"):
            last = datetime.fromisoformat(user["last_daily"])
            diff = (now - last).total_seconds()
            if diff < 86400:
                remaining = 86400 - diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return await ctx.send(f"⏰ استلمت بالفعل! ارجع بعد **{hours}س {minutes}د**")

        amount = random.randint(100, 500)
        user["balance"] += amount
        user["total_earned"] += amount
        user["last_daily"] = now.isoformat()
        self.add_transaction(ctx.author.id, "daily", amount, "مكافأة يومية")
        self.save()

        embed = discord.Embed(
            title="🎁 المكافأة اليومية",
            description=f"حصلت على **{amount} {COIN_SYMBOL}**!",
            color=0xF7931A
        )
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    @commands.command(name="work")
    async def work_text(self, ctx):
        """!work — اشتغل واكسب"""
        user = self.get_user(ctx.author.id)
        now = discord.utils.utcnow()

        if user.get("last_work"):
            last = datetime.fromisoformat(user["last_work"])
            diff = (now - last).total_seconds()
            if diff < 3600:
                remaining = 3600 - diff
                minutes = int(remaining // 60)
                return await ctx.send(f"⏰ ارتاح شوية! ارجع بعد **{minutes}د**")

        jobs = ["مبرمج 👨‍💻", "طبيب 👨‍⚕️", "مهندس 👷", "معلم 👨‍🏫",
                "طباخ 👨‍🍳", "فنان 🎨", "كاتب ✍️", "مصور 📸"]
        job = random.choice(jobs)
        amount = random.randint(50, 200)

        user["balance"] += amount
        user["total_earned"] += amount
        user["last_work"] = now.isoformat()
        self.add_transaction(ctx.author.id, "work", amount, f"عمل كـ {job}")
        self.save()

        embed = discord.Embed(
            title=f"💼 {job}",
            description=f"اشتغلت وكسبت **{amount} {COIN_SYMBOL}**!",
            color=0x3498DB
        )
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    @commands.command(name="transfer")
    async def transfer_text(self, ctx, member: discord.Member, amount: int):
        """!transfer @user amount — تحويل"""
        if member.id == ctx.author.id:
            return await ctx.send("❌ متحولش لنفسك!")
        if member.bot:
            return await ctx.send("❌ متحولش لبوت!")
        if amount < 1:
            return await ctx.send("❌ المبلغ لازم يكون 1 على الأقل")

        sender = self.get_user(ctx.author.id)
        if sender["balance"] < amount:
            return await ctx.send(f"❌ رصيدك مش كفاية! عندك `{sender['balance']:,} {COIN_SYMBOL}`")

        receiver = self.get_user(member.id)
        sender["balance"] -= amount
        sender["total_spent"] += amount
        receiver["balance"] += amount
        receiver["total_earned"] += amount

        self.add_transaction(ctx.author.id, "transfer_out", -amount, f"تحويل إلى {member.display_name}")
        self.add_transaction(member.id, "transfer_in", amount, f"تحويل من {ctx.author.display_name}")
        self.save()

        embed = discord.Embed(
            title="💸 تم التحويل",
            description=f"حولت **{amount:,} {COIN_SYMBOL}** لـ {member.mention}",
            color=0x2ECC71
        )
        await ctx.send(embed=embed)

    @commands.command(name="shop")
    async def shop_text(self, ctx):
        """!shop — المتجر"""
        embed = discord.Embed(
            title=f"🛒 متجر {COIN_NAME}",
            description="اشترِ حاجات رائعة بالـ Crypto!",
            color=0xF7931A
        )
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['name']}",
                value=f"💰 `{item['price']:,}` {COIN_SYMBOL}\n📝 {item['description']}",
                inline=False
            )
        embed.set_footer(text="استخدم /buy لشراء عنصر")
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_text(self, ctx, item_id: str, amount: int = 1):
        """!buy [item_id] — شراء"""
        item_id = item_id.lower()
        item_data = SHOP_ITEMS.get(item_id)

        if not item_data:
            available = ", ".join(SHOP_ITEMS.keys())
            return await ctx.send(f"❌ العنصر مش موجود!\nالمتاح: `{available}`")

        user = self.get_user(ctx.author.id)
        price = item_data["price"] * amount

        if user["balance"] < price:
            return await ctx.send(f"❌ رصيدك مش كفاية!\nعندك: `{user['balance']:,}` {COIN_SYMBOL}\nالسعر: `{price:,}` {COIN_SYMBOL}")

        user["balance"] -= price
        user["total_spent"] += price
        for _ in range(amount):
            user.setdefault("inventory", []).append(item_id)
        self.add_transaction(ctx.author.id, "buy", -price, f"شراء {item_data['name']} x{amount}")
        self.save()

        embed = discord.Embed(
            title="✅ تم الشراء",
            description=f"اشتريت **{item_data['name']}** x{amount}!\n\nالسعر: `{price:,}` {COIN_SYMBOL}\nرصيدك: `{user['balance']:,}` {COIN_SYMBOL}",
            color=0x2ECC71
        )
        await ctx.send(embed=embed)

    @commands.command(name="top", aliases=["crypto-top"])
    async def top_text(self, ctx):
        """!top — أغنى الأعضاء"""
        if not self.data:
            return await ctx.send("📭 مفيش بيانات!")

        sorted_users = sorted(self.data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""

        for i, (uid, data) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            if not member:
                continue
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{member.display_name}** — `{data.get('balance', 0):,}` {COIN_SYMBOL}\n"

        embed = discord.Embed(
            title=f"🏆 أغنى 10 أعضاء في {COIN_NAME}",
            description=desc or "لا توجد بيانات",
            color=0xF7931A
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))