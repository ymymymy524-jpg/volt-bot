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


def format_duration(seconds):
    if seconds < 60:
        return f"{int(seconds)} ثانية"
    minutes = seconds // 60
    if minutes < 60:
        return f"{int(minutes)} دقيقة"
    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} ساعة"
    return f"{int(hours // 24)} يوم"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "cash": 0, "bank": 0, "total_earned": 0, "total_spent": 0,
                "last_daily": None, "last_work": None,
                "last_crime": None, "last_rob": None,
                "transactions": [], "inventory": []
            }
        # ترقية البيانات القديمة: balance → cash
        if "balance" in self.data[uid] and "cash" not in self.data[uid]:
            self.data[uid]["cash"] = self.data[uid].pop("balance", 0)
            self.data[uid].setdefault("bank", 0)
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

    def check_cooldown(self, user, key, seconds):
        last = user.get(f"last_{key}")
        if last:
            diff = (discord.utils.utcnow() - datetime.fromisoformat(last)).total_seconds()
            if diff < seconds:
                return int(seconds - diff)
        return 0

    # ═══════════════════════════════════════
    # 💰 balance
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="balance", aliases=["bal", "رصيدي", "رصيد"], description="💰 عرض الرصيد")
    @app_commands.describe(member="العضو (اختياري)")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user = self.get_user(target.id)
        total = user["cash"] + user["bank"]
        all_users = sorted(self.data.items(), key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0), reverse=True)
        rank = next((i + 1 for i, (uid, _) in enumerate(all_users) if uid == str(target.id)), 0)
        embed = discord.Embed(title=f"💎 محفظة {COIN_NAME} — {target.display_name}", color=0xF7931A, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👛 الكاش", value=f"**{user['cash']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="🏦 البنك", value=f"**{user['bank']:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="💎 الإجمالي", value=f"**{total:,} {COIN_SYMBOL}**", inline=True)
        embed.add_field(name="🏆 الترتيب", value=f"**#{rank}**", inline=True)
        embed.add_field(name="📈 المكتسب", value=f"**{user['total_earned']:,}**", inline=True)
        embed.add_field(name="🎒 العناصر", value=f"**{len(user.get('inventory', []))}**", inline=True)
        embed.set_footer(text=f"ID: {target.id}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎁 daily
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="daily", aliases=["يومي", "راتب"], description="🎁 المكافأة اليومية")
    async def daily(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        remaining = self.check_cooldown(user, "daily", 86400)
        if remaining:
            await ctx.send(f"⏰ استلمت بالفعل! ارجع بعد **{format_duration(remaining)}**")
            return
        amount = random.randint(800, 1500)
        user["cash"] += amount
        user["total_earned"] += amount
        user["last_daily"] = discord.utils.utcnow().isoformat()
        self.add_transaction(ctx.author.id, "daily", amount, "مكافأة يومية")
        self.save()
        embed = discord.Embed(title="🎁 المكافأة اليومية", description=f"حصلت على **{amount:,} {COIN_SYMBOL}**!", color=0xF7931A)
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💼 work
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="work", aliases=["اشتغل", "عمل"], description="💼 اشتغل واكسب")
    async def work(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        remaining = self.check_cooldown(user, "work", 3600)
        if remaining:
            await ctx.send(f"⏰ ارتاح شوية! ارجع بعد **{format_duration(remaining)}**")
            return
        jobs = ["مبرمج 👨‍💻", "طبيب 👨‍⚕️", "مهندس 👷", "معلم 👨‍🏫", "طباخ 👨‍🍳", "فنان 🎨", "كاتب ✍️", "مصور 📸", "سائق 🚗", "نجار 🔨"]
        job = random.choice(jobs)
        amount = random.randint(200, 600)
        user["cash"] += amount
        user["total_earned"] += amount
        user["last_work"] = discord.utils.utcnow().isoformat()
        self.add_transaction(ctx.author.id, "work", amount, f"عمل كـ {job}")
        self.save()
        embed = discord.Embed(title=f"💼 {job}", description=f"اشتغلت وكسبت **{amount:,} {COIN_SYMBOL}**!", color=0x3498DB)
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🦹 crime
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="crime", aliases=["جريمة"], description="🦹 مخاطرة")
    async def crime(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        remaining = self.check_cooldown(user, "crime", 1800)
        if remaining:
            await ctx.send(f"⏰ ارتاح! ارجع بعد **{format_duration(remaining)}**")
            return
        user["last_crime"] = discord.utils.utcnow().isoformat()
        if random.random() < 0.5:
            amount = random.randint(500, 1500)
            user["cash"] += amount
            user["total_earned"] += amount
            self.add_transaction(ctx.author.id, "crime", amount, "عملية ناجحة")
            self.save()
            embed = discord.Embed(title="🦹 نجحت العملية", description=f"هربت بغنيمة **{amount:,} {COIN_SYMBOL}**", color=0x2ECC71)
        else:
            fine = min(user["cash"], random.randint(300, 900))
            user["cash"] -= fine
            user["total_spent"] += fine
            self.add_transaction(ctx.author.id, "crime", -fine, "غرامة")
            self.save()
            embed = discord.Embed(title="🚓 انمسكت", description=f"دفعت غرامة **{fine:,} {COIN_SYMBOL}**", color=0xE74C3C)
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🥷 rob
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="rob", aliases=["سرقة", "اسرق"], description="🥷 سرقة عضو")
    @app_commands.describe(member="العضو")
    async def rob(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send("❌ ما تسرق نفسك!")
            return
        if member.bot:
            await ctx.send("❌ ما تسرق بوت!")
            return
        user = self.get_user(ctx.author.id)
        victim = self.get_user(member.id)
        if victim["cash"] < 200:
            await ctx.send(f"❌ {member.mention} كاشه قليل!")
            return
        if user["cash"] < 200:
            await ctx.send("❌ لازم يكون معك 200 كاش على الأقل!")
            return
        remaining = self.check_cooldown(user, "rob", 3600)
        if remaining:
            await ctx.send(f"⏰ ارتاح! ارجع بعد **{format_duration(remaining)}**")
            return
        user["last_rob"] = discord.utils.utcnow().isoformat()
        if random.random() < 0.45:
            amount = int(victim["cash"] * (random.randint(10, 30) / 100))
            victim["cash"] -= amount
            user["cash"] += amount
            user["total_earned"] += amount
            self.add_transaction(ctx.author.id, "rob", amount, f"سرقة من {member.display_name}")
            self.save()
            embed = discord.Embed(title="🥷 سرقة ناجحة", description=f"سرقت **{amount:,} {COIN_SYMBOL}** من {member.mention}", color=0x2ECC71)
        else:
            fine = int(user["cash"] * 0.15)
            user["cash"] -= fine
            victim["cash"] += fine
            self.add_transaction(ctx.author.id, "rob_fail", -fine, "فشل السرقة")
            self.save()
            embed = discord.Embed(title="🚨 فشلت السرقة", description=f"انمسكت ودفعت **{fine:,} {COIN_SYMBOL}** لـ {member.mention}", color=0xE74C3C)
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🏦 deposit
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="deposit", aliases=["ايداع", "ودع"], description="🏦 إيداع في البنك")
    @app_commands.describe(amount="المبلغ (أو اكتب all)")
    async def deposit(self, ctx: commands.Context, amount: str):
        user = self.get_user(ctx.author.id)
        if amount.lower() in ["all", "كل", "الكل"]:
            amt = user["cash"]
        else:
            try:
                amt = int(amount)
            except ValueError:
                await ctx.send("❌ اكتب مبلغ صحيح أو `all`")
                return
        if amt < 1 or amt > user["cash"]:
            await ctx.send(f"❌ مبلغ غير صحيح! كاشك: `{user['cash']:,}` {COIN_SYMBOL}")
            return
        user["cash"] -= amt
        user["bank"] += amt
        self.add_transaction(ctx.author.id, "deposit", -amt, "إيداع في البنك")
        self.save()
        embed = discord.Embed(title="🏦 تم الإيداع", description=f"أودعت **{amt:,} {COIN_SYMBOL}**\n\n👛 كاشك: `{user['cash']:,}`\n🏦 بنكك: `{user['bank']:,}`", color=0x2ECC71)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 👛 withdraw
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="withdraw", aliases=["سحب_بنك", "اسحب"], description="👛 سحب من البنك")
    @app_commands.describe(amount="المبلغ (أو اكتب all)")
    async def withdraw(self, ctx: commands.Context, amount: str):
        user = self.get_user(ctx.author.id)
        if amount.lower() in ["all", "كل", "الكل"]:
            amt = user["bank"]
        else:
            try:
                amt = int(amount)
            except ValueError:
                await ctx.send("❌ اكتب مبلغ صحيح أو `all`")
                return
        if amt < 1 or amt > user["bank"]:
            await ctx.send(f"❌ مبلغ غير صحيح! بنكك: `{user['bank']:,}` {COIN_SYMBOL}")
            return
        user["bank"] -= amt
        user["cash"] += amt
        self.add_transaction(ctx.author.id, "withdraw", amt, "سحب من البنك")
        self.save()
        embed = discord.Embed(title="👛 تم السحب", description=f"سحبت **{amt:,} {COIN_SYMBOL}**\n\n👛 كاشك: `{user['cash']:,}`\n🏦 بنكك: `{user['bank']:,}`", color=0x2ECC71)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎲 luck
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="luck", aliases=["حظ", "رهان"], description="🎲 رهان")
    @app_commands.describe(choice="صورة أو كتابة", amount="المبلغ")
    async def luck(self, ctx: commands.Context, choice: str, amount: int):
        sides = {"صورة": "صورة", "كتابة": "كتابة", "ملك": "صورة", "نقش": "كتابة"}
        pick = sides.get(choice)
        if not pick:
            await ctx.send("❌ اختر: `صورة` أو `كتابة`")
            return
        user = self.get_user(ctx.author.id)
        if amount < 1 or amount > user["cash"]:
            await ctx.send(f"❌ مبلغ غير صحيح! كاشك: `{user['cash']:,}`")
            return
        result = random.choice(["صورة", "كتابة"])
        won = result == pick
        user["cash"] += amount if won else -amount
        if won:
            user["total_earned"] += amount
        else:
            user["total_spent"] += amount
        self.add_transaction(ctx.author.id, "luck", amount if won else -amount, f"رهان {pick}")
        self.save()
        embed = discord.Embed(
            title="🎉 ربحت" if won else "💔 خسرت",
            description=f"النتيجة: **{result}**\n{'ربحت' if won else 'خسرت'} **{amount:,} {COIN_SYMBOL}**",
            color=0x2ECC71 if won else 0xE74C3C
        )
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎰 slots
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="slots", aliases=["سلوت", "سلوتس"], description="🎰 ماكينة الحظ")
    @app_commands.describe(amount="المبلغ")
    async def slots(self, ctx: commands.Context, amount: int):
        user = self.get_user(ctx.author.id)
        if amount < 1 or amount > user["cash"]:
            await ctx.send(f"❌ مبلغ غير صحيح! كاشك: `{user['cash']:,}`")
            return
        icons = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
        roll = [random.choice(icons) for _ in range(3)]
        unique = len(set(roll))
        multiplier = 5 if unique == 1 else (1 if unique == 2 else -1)
        user["cash"] += amount * multiplier
        if multiplier > 0:
            user["total_earned"] += amount * multiplier
        else:
            user["total_spent"] += amount
        self.add_transaction(ctx.author.id, "slots", amount * multiplier, f"سلوت: {''.join(roll)}")
        self.save()
        title = "🎰 جاكبوت!" if multiplier == 5 else ("🎰 ربحت" if multiplier == 1 else "🎰 خسرت")
        text = f"ربحت **{amount * multiplier:,} {COIN_SYMBOL}**" if multiplier > 0 else f"خسرت **{amount:,} {COIN_SYMBOL}**"
        embed = discord.Embed(title=title, description=f"## {'  '.join(roll)}\n{text}", color=0x2ECC71 if multiplier > 0 else 0xE74C3C)
        embed.set_footer(text=f"كاشك: {user['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎒 inventory
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="inventory", aliases=["حقيبة", "مشترياتي"], description="🎒 المشتريات")
    async def inventory(self, ctx: commands.Context):
        user = self.get_user(ctx.author.id)
        if not user["inventory"]:
            await ctx.send("🎒 حقيبتك فاضية!")
            return
        counts = {}
        for item in user["inventory"]:
            counts[item] = counts.get(item, 0) + 1
        text = "\n".join(f"• {SHOP_ITEMS.get(k, {}).get('name', k)} × **{v}**" for k, v in counts.items())
        embed = discord.Embed(title="🎒 حقيبتك", description=text, color=0xF7931A)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💸 transfer
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="transfer", aliases=["حول", "تحويل"], description="💸 تحويل")
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
        if sender["cash"] < amount:
            await ctx.send(f"❌ كاشك مش كفاية! عندك `{sender['cash']:,} {COIN_SYMBOL}`")
            return
        receiver = self.get_user(member.id)
        fee = int(amount * 0.02)
        sender["cash"] -= amount
        sender["total_spent"] += amount
        receiver["cash"] += amount - fee
        receiver["total_earned"] += amount - fee
        self.add_transaction(ctx.author.id, "transfer_out", -amount, f"تحويل لـ {member.display_name}")
        self.add_transaction(member.id, "transfer_in", amount - fee, f"تحويل من {ctx.author.display_name}")
        self.save()
        embed = discord.Embed(
            title="💸 تم التحويل",
            description=f"حولت **{amount:,} {COIN_SYMBOL}** لـ {member.mention}\nضريبة 2%: **{fee:,} {COIN_SYMBOL}**",
            color=0x2ECC71
        )
        embed.set_footer(text=f"كاشك: {sender['cash']:,} {COIN_SYMBOL}")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🏆 crypto-top
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="crypto-top", aliases=["btop", "اغنى", "الاغنياء"], description="🏆 أغنى 10 أعضاء")
    async def top(self, ctx: commands.Context):
        if not self.data:
            await ctx.send("📭 مفيش بيانات!")
            return
        sorted_users = sorted(self.data.items(), key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, data) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            if not member:
                continue
            total = data.get("cash", 0) + data.get("bank", 0)
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            desc += f"{medal} **{member.display_name}** — `{total:,}` {COIN_SYMBOL}\n"
        embed = discord.Embed(title=f"🏆 أغنى 10 أعضاء في {COIN_NAME}", description=desc or "لا توجد بيانات", color=0xF7931A)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📜 history
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="history", aliases=["bh", "سجلي"], description="📜 سجل المعاملات")
    @app_commands.describe(member="العضو (اختياري)")
    async def history(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user = self.get_user(target.id)
        embed = discord.Embed(title=f"📜 سجل {target.display_name}", color=0x3498DB)
        embed.add_field(name="👛 الكاش", value=f"`{user['cash']:,}` {COIN_SYMBOL}", inline=True)
        embed.add_field(name="🏦 البنك", value=f"`{user['bank']:,}` {COIN_SYMBOL}", inline=True)
        embed.add_field(name="📈 المكتسب", value=f"`{user['total_earned']:,}` {COIN_SYMBOL}", inline=False)
        recent = user.get("transactions", [])[-10:]
        if recent:
            tx_text = ""
            for tx in reversed(recent):
                emoji = "➕" if tx['amount'] > 0 else "➖"
                tx_text += f"{emoji} `{abs(tx['amount']):,}` {COIN_SYMBOL} — {tx['description']}\n"
            embed.add_field(name="📋 آخر 10 معاملات", value=tx_text[:1024], inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🛒 shop
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="shop", aliases=["متجر"], description="🛒 المتجر")
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(title=f"🛒 متجر {COIN_NAME}", description="اشترِ حاجات رائعة!", color=0xF7931A)
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(name=f"{item['name']} (`{item_id}`)", value=f"💰 `{item['price']:,}` {COIN_SYMBOL}\n📝 {item['description']}", inline=False)
        embed.set_footer(text="استخدم !buy لشراء عنصر")
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💳 buy
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="buy", aliases=["اشتري", "شراء"], description="💳 شراء")
    @app_commands.describe(item_id="معرف العنصر", amount="الكمية")
    async def buy(self, ctx: commands.Context, item_id: str = None, amount: int = 1):
        if not item_id:
            await ctx.send("❌ اكتب اسم العنصر! استخدم `!shop`")
            return
        item_data = SHOP_ITEMS.get(item_id.lower())
        if not item_data:
            available = ", ".join(f"`{k}`" for k in SHOP_ITEMS.keys())
            await ctx.send(f"❌ العنصر مش موجود!\nالمتاح: {available}")
            return
        user = self.get_user(ctx.author.id)
        price = item_data["price"] * amount
        if user["cash"] < price:
            await ctx.send(f"❌ كاشك مش كفاية!\nعندك: `{user['cash']:,}` {COIN_SYMBOL}")
            return
        user["cash"] -= price
        user["total_spent"] += price
        for _ in range(amount):
            user.setdefault("inventory", []).append(item_id.lower())
        self.add_transaction(ctx.author.id, "buy", -price, f"شراء {item_data['name']} x{amount}")
        self.save()
        embed = discord.Embed(title="✅ تم الشراء", description=f"اشتريت **{item_data['name']}** x{amount}!\n\nكاشك: `{user['cash']:,}` {COIN_SYMBOL}", color=0x2ECC71)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🛠️ badmin (group)
    # ═══════════════════════════════════════
    @commands.hybrid_group(name="badmin", aliases=["bitcoin-admin"], description="🛠️ إدارة Crypto", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def badmin(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛠️ أوامر إدارة Crypto",
            description="`!badmin add @عضو مبلغ`\n`!badmin remove @عضو مبلغ`\n`!badmin set @عضو مبلغ`\n`!badmin reset @عضو`",
            color=0xE67E22
        )
        await ctx.send(embed=embed)

    @badmin.command(name="add", aliases=["اضف"], description="إضافة كاش")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_add(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["cash"] += amount
        user["total_earned"] += amount
        self.add_transaction(member.id, "admin", amount, "إضافة من الإدارة")
        self.save()
        await ctx.send(f"✅ تم إضافة `{amount:,}` {COIN_SYMBOL} لـ {member.mention}")

    @badmin.command(name="remove", aliases=["خصم"], description="خصم كاش")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_remove(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["cash"] = max(0, user["cash"] - amount)
        user["total_spent"] += amount
        self.add_transaction(member.id, "admin", -amount, "خصم من الإدارة")
        self.save()
        await ctx.send(f"✅ تم خصم `{amount:,}` {COIN_SYMBOL} من {member.mention}")

    @badmin.command(name="set", aliases=["عين"], description="تعيين كاش")
    @app_commands.describe(member="العضو", amount="المبلغ")
    async def badmin_set(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(member.id)
        user["cash"] = amount
        self.add_transaction(member.id, "admin", amount, "تعيين الرصيد")
        self.save()
        await ctx.send(f"✅ كاش {member.mention} بقى `{amount:,}` {COIN_SYMBOL}")

    @badmin.command(name="reset", aliases=["صفر"], description="تصفير")
    @app_commands.describe(member="العضو")
    async def badmin_reset(self, ctx, member: discord.Member):
        self.data[str(member.id)] = {
            "cash": 0, "bank": 0, "total_earned": 0, "total_spent": 0,
            "last_daily": None, "last_work": None,
            "last_crime": None, "last_rob": None,
            "transactions": [], "inventory": []
        }
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