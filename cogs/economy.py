import discord
from discord import app_commands
from discord.ext import commands
import json, os, random
from datetime import datetime

BITCOIN_FILE = "bitcoin.json"
COIN_NAME = "Crypto"
COIN_SYMBOL = "₿"

SHOP_ITEMS = {
    "crown": {"name": "👑 تاج", "price": 5000, "description": "تاج ذهبي"},
    "ring": {"name": "💍 خاتم", "price": 2000, "description": "خاتم ألماسي"},
    "car": {"name": "🚗 سيارة", "price": 10000, "description": "سيارة رياضية"},
    "house": {"name": "🏠 منزل", "price": 50000, "description": "منزل فاخر"},
    "yacht": {"name": "🛥️ يخت", "price": 100000, "description": "يخت خاص"},
    "rocket": {"name": "🚀 صاروخ", "price": 250000, "description": "صاروخ للفضاء"},
    "diamond": {"name": "💎 ألماسة", "price": 1000, "description": "ألماسة نادرة"},
    "trophy": {"name": "🏆 كأس", "price": 3000, "description": "كأس الفوز"},
}


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
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "balance": 0, "total_earned": 0, "total_spent": 0,
                "last_daily": None, "last_work": None,
                "transactions": [], "inventory": []
            }
        return self.data[uid]

    def save(self):
        save_data(self.data)

    def add_transaction(self, user_id, tx_type, amount, description):
        user = self.get_user(user_id)
        user["transactions"].append({
            "type": tx_type, "amount": amount,
            "description": description,
            "timestamp": discord.utils.utcnow().isoformat()
        })
        if len(user["transactions"]) > 50:
            user["transactions"] = user["transactions"][-50:]

    @commands.hybrid_command(name="balance", aliases=["bal", "رصيدي"], description="💰 عرض الرصيد")
    @app_commands.describe(member="العضو (اختياري)")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user = self.get_user(target.id)
        embed = discord.Embed(title=f"💎 محفظة {COIN_NAME} — {target.display_name}", color=0xF7931A, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 الرصيد", value=f"**{user['balance']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📈 المكتسب", value=f"**{user['total_earned']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="📉 المنفق", value=f"**{user['total_spent']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="🎒 العناصر", value=f"**{len(user.get('inventory', []))}**", inline=True)
        embed.set_footer(text=f"ID: {target.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", aliases=["يومي"], description="🎁 المكافأة اليومية")
    async def daily(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        now = discord.utils.utcnow()
        if user.get("last_daily"):
            last = datetime.fromisoformat(user["last_daily"])
            diff = (now - last).total_seconds()
            if diff < 86400:
                remaining = 86400 - diff
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                await ctx.send(f"⏰ استلمت بالفعل! ارجع بعد **{hours}س {minutes}د**")
                return
        amount = random.randint(100, 500)
        user["balance"] += amount
        user["total_earned"] += amount
        user["last_daily"] = now.isoformat()
        self.add_transaction(ctx.author.id, "daily", amount, "مكافأة يومية")
        self.save()
        embed = discord.Embed(title="🎁 المكافأة اليومية", description=f"حصلت على **{amount} {COIN_SYMBOL}**!", color=0xF7931A)
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work", aliases=["اشتغل"], description="💼 اشتغل واكسب")
    async def work(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        now = discord.utils.utcnow()
        if user.get("last_work"):
            last = datetime.fromisoformat(user["last_work"])
            diff = (now - last).total_seconds()
            if diff < 3600:
                minutes = int((3600 - diff) // 60)
                await ctx.send(f"⏰ ارتاح شوية! ارجع بعد **{minutes}د**")
                return
        jobs = ["مبرمج 👨‍💻", "طبيب 👨‍⚕️", "مهندس 👷", "معلم 👨‍🏫", "طباخ 👨‍🍳", "فنان 🎨", "كاتب ✍️", "مصور 📸"]
        job = random.choice(jobs)
        amount = random.randint(50, 200)
        user["balance"] += amount
        user["total_earned"] += amount
        user["last_work"] = now.isoformat()
        self.add_transaction(ctx.author.id, "work", amount, f"عمل كـ {job}")
        self.save()
        embed = discord.Embed(title=f"💼 {job}", description=f"اشتغلت وكسبت **{amount} {COIN_SYMBOL}**!", color=0x3498DB)
        embed.set_footer(text=f"رصيدك: {user['balance']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="transfer", aliases=["حول"], description="💸 تحويل")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def transfer(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.id == ctx.author.id:
            await ctx.send("❌ متحولش لنفسك!")
            return
        if member.bot:
            await ctx.send("❌ متحولش لبوت!")
            return
        if amount < 1:
            await ctx.send("❌ المبلغ 1 على الأقل!")
            return
        sender = self.get_user(ctx.author.id)
        if sender["balance"] < amount:
            await ctx.send(f"❌ رصيدك مش كفاية! عندك `{sender['balance']:,} {COIN_SYMBOL}`")
            return
        receiver = self.get_user(member.id)
        sender["balance"] -= amount
        sender["total_spent"] += amount
        receiver["balance"] += amount
        receiver["total_earned"] += amount
        self.add_transaction(ctx.author.id, "transfer_out", -amount, f"تحويل لـ {member.display_name}")
        self.add_transaction(member.id, "transfer_in", amount, f"تحويل من {ctx.author.display_name}")
        self.save()
        embed = discord.Embed(title="💸 تم التحويل", description=f"حولت **{amount:,} {COIN_SYMBOL}** لـ {member.mention}", color=0x2ECC71)
        embed.set_footer(text=f"رصيدك: {sender['balance']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="top", aliases=["btop", "crypto-top"], description="🏆 أغنى 10 أعضاء")
    async def top(self, ctx: commands.Context):
        if not self.data:
            await ctx.send("📭 مفيش بيانات!")
            return
        sorted_users = sorted(self.data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, data) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            if not member:
                continue
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{member.display_name}** — `{data.get('balance', 0):,}` {COIN_SYMBOL}\n"
        embed = discord.Embed(title=f"🏆 أغنى 10 أعضاء في {COIN_NAME}", description=desc or "لا توجد بيانات", color=0xF7931A)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="history", aliases=["bh", "سجلي"], description="📜 سجل المعاملات")
    @app_commands.describe(member="العضو (اختياري)")
    async def history(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user = self.get_user(target.id)
        embed = discord.Embed(title=f"📜 سجل {target.display_name}", color=0x3498DB)
        embed.add_field(name="💰 الرصيد", value=f"`{user['balance']:,}` {COIN_SYMBOL}", inline=False)
        embed.add_field(name="📈 المكتسب", value=f"`{user['total_earned']:,}` {COIN_SYMBOL}", inline=False)
        embed.add_field(name="📉 المنفق", value=f"`{user['total_spent']:,}` {COIN_SYMBOL}", inline=False)
        recent = user.get("transactions", [])[-10:]
        if recent:
            tx_text = ""
            for tx in reversed(recent):
                emoji = "➕" if tx['amount'] > 0 else "➖"
                tx_text += f"{emoji} `{abs(tx['amount']):,}` {COIN_SYMBOL} — {tx['description']}\n"
            embed.add_field(name="📋 آخر 10 معاملات", value=tx_text[:1024], inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", aliases=["متجر"], description="🛒 المتجر")
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(title=f"🛒 متجر {COIN_NAME}", description="اشترِ حاجات رائعة!", color=0xF7931A)
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(name=f"{item['name']} (`{item_id}`)", value=f"💰 `{item['price']:,}` {COIN_SYMBOL}\n📝 {item['description']}", inline=False)
        embed.set_footer(text="استخدم !buy لشراء عنصر")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", aliases=["اشتري"], description="💳 شراء")
    @app_commands.describe(item_id="معرف العنصر", amount="الكمية")
    async def buy(self, ctx: commands.Context, item_id: str = None, amount: int = 1):
        if not item_id:
            await ctx.send("❌ اكتب اسم العنصر! استخدم `!shop`")
            return
        item_id = item_id.lower()
        item_data = SHOP_ITEMS.get(item_id)
        if not item_data:
            available = ", ".join(f"`{k}`" for k in SHOP_ITEMS.keys())
            await ctx.send(f"❌ العنصر مش موجود!\nالمتاح: {available}")
            return
        user = self.get_user(ctx.author.id)
        price = item_data["price"] * amount
        if user["balance"] < price:
            await ctx.send(f"❌ رصيدك مش كفاية!\nعندك: `{user['balance']:,}` {COIN_SYMBOL}")
            return
        user["balance"] -= price
        user["total_spent"] += price
        for _ in range(amount):
            user.setdefault("inventory", []).append(item_id)
        self.add_transaction(ctx.author.id, "buy", -price, f"شراء {item_data['name']} x{amount}")
        self.save()
        embed = discord.Embed(title="✅ تم الشراء", description=f"اشتريت **{item_data['name']}** x{amount}!\n\nرصيدك: `{user['balance']:,}` {COIN_SYMBOL}", color=0x2ECC71)
        await ctx.send(embed=embed)

    @commands.hybrid_group(name="badmin", aliases=["bitcoin-admin"], description="🛠️ إدارة Crypto", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def badmin(self, ctx: commands.Context):
        embed = discord.Embed(title="🛠️ أوامر إدارة Crypto", description="`!badmin add @عضو مبلغ`\n`!badmin remove @عضو مبلغ`\n`!badmin set @عضو مبلغ`\n`!badmin reset @عضو`", color=0xE67E22)
        await ctx.send(embed=embed)

    @badmin.command(name="add", aliases=["اضف"], description="إضافة رصيد")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_add(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] += amount
        user["total_earned"] += amount
        self.add_transaction(member.id, "admin", amount, "إضافة")
        self.save()
        await ctx.send(f"✅ تم إضافة `{amount:,}` {COIN_SYMBOL} لـ {member.mention}")

    @badmin.command(name="remove", aliases=["خصم"], description="خصم رصيد")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_remove(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] = max(0, user["balance"] - amount)
        user["total_spent"] += amount
        self.add_transaction(member.id, "admin", -amount, "خصم")
        self.save()
        await ctx.send(f"✅ تم خصم `{amount:,}` {COIN_SYMBOL} من {member.mention}")

    @badmin.command(name="set", aliases=["عين"], description="تعيين رصيد")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_set(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["balance"] = amount
        self.add_transaction(member.id, "admin", amount, "تعيين")
        self.save()
        await ctx.send(f"✅ رصيد {member.mention} بقى `{amount:,}` {COIN_SYMBOL}")

    @badmin.command(name="reset", aliases=["صفر"], description="تصفير")
    @app_commands.describe(member="العضو")
    async def badmin_reset(self, ctx, member: discord.Member):
        self.data[str(member.id)] = {"balance": 0, "total_earned": 0, "total_spent": 0, "last_daily": None, "last_work": None, "transactions": [], "inventory": []}
        self.save()
        await ctx.send(f"🔄 تم تصفير {member.mention}")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ مفيش عندك الصلاحيات!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ مش لاقي العضو!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ ناقص: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ تأكد من البيانات!")


async def setup(bot):
    await bot.add_cog(Economy(bot))