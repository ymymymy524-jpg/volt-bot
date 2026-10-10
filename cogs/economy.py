import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from datetime import timedelta

# مسار ملف التخزين
BITCOIN_FILE = "bitcoin.json"

# متجر العناصر
SHOP_ITEMS = {
    "crown": {"name": "👑 تاج", "price": 5000, "description": "تاج ذهبي يظهر في بروفايلك"},
    "ring": {"name": "💍 خاتم", "price": 2000, "description": "خاتم ألماسي"},
    "car": {"name": "🚗 سيارة", "price": 10000, "description": "سيارة رياضية"},
    "house": {"name": "🏠 منزل", "price": 50000, "description": "منزل فاخر"},
    "yacht": {"name": "🛥️ يخت", "price": 100000, "description": "يخت خاص"},
    "rocket": {"name": "🚀 صاروخ", "price": 250000, "description": "صاروخ للفضاء"},
    "diamond": {"name": "💎 ألماسة", "price": 1000, "description": "ألماسة نادرة"},
    "trophy": {"name": "🏆 كأس", "price": 3000, "description": "كأس الفوز"}
}

# دالة لتحميل البيانات من ملف JSON
def load_data():
    if os.path.exists(BITCOIN_FILE):
        try:
            with open(BITCOIN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# دالة لحفظ البيانات في ملف JSON
def save_data(data):
    with open(BITCOIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Bitcoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # دالة لجلب بيانات عضو (وإنشائها لو مش موجودة)
    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                "balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "last_daily": None,
                "last_work": None,
                "transactions": [],
                "inventory": []
            }
        return self.data[user_id]

    # دالة مساعدة لحفظ البيانات
    def save(self):
        save_data(self.data)

    # دالة لإضافة معاملة للسجل
    def add_transaction(self, user_id, tx_type, amount, description):
        user_data = self.get_user_data(user_id)
        transaction = {
            "type": tx_type,
            "amount": amount,
            "description": description,
            "timestamp": discord.utils.utcnow().isoformat()
        }
        user_data["transactions"].append(transaction)
        if len(user_data["transactions"]) > 50:
            user_data["transactions"] = user_data["transactions"][-50:]

    # أمر /balance لعرض الرصيد
    @app_commands.command(name="balance", description="عرض رصيد Bitcoin الخاص بك أو بعضو آخر")
    @app_commands.describe(member="العضو اللي عايز تشوف رصيده (اختياري)")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = self.get_user_data(target.id)
        
        balance = user_data["balance"]
        total_earned = user_data["total_earned"]
        total_spent = user_data["total_spent"]
        inventory_count = len(user_data.get("inventory", []))

        embed = discord.Embed(
            title=f"💎 محفظة Bitcoin - {target.display_name}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="💰 الرصيد الحالي", value=f"**{balance:,} ₿**", inline=True)
        embed.add_field(name="📈 إجمالي المكتسب", value=f"**{total_earned:,} ₿**", inline=True)
        embed.add_field(name="📉 إجمالي المنفق", value=f"**{total_spent:,} ₿**", inline=True)
        embed.add_field(name="🎒 عدد العناصر", value=f"**{inventory_count}**", inline=True)
        
        embed.set_footer(text=f"آيدي العضو: {target.id}")

        await interaction.response.send_message(embed=embed)

    # أمر /daily للحصول على الرصيد اليومي
    @app_commands.command(name="daily", description="احصل على مكافأتك اليومية (100-500 ₿)")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)
    async def daily(self, interaction: discord.Interaction):
        amount = random.randint(100, 500)
        user_data = self.get_user_data(interaction.user.id)
        
        user_data["balance"] += amount
        user_data["total_earned"] += amount
        user_data["last_daily"] = discord.utils.utcnow().isoformat()
        self.add_transaction(interaction.user.id, "daily", amount, "مكافأة يومية")
        self.save()

        embed = discord.Embed(
            title="🎁 المكافأة اليومية",
            description=f"حصلت على **{amount} ₿** 💎\n\nعد غداً لنفس الوقت للحصول على مكافأة جديدة!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"رصيدك الجديد: {user_data['balance']:,} ₿")
        
        await interaction.response.send_message(embed=embed)

    # معالجة خطأ الكولداون للأمر اليومي
    @daily.error
    async def daily_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            remaining = int(error.retry_after)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            
            embed = discord.Embed(
                title="⏰ انتظر قليلاً",
                description=f"لقد أخذت مكافأتك اليومية بالفعل!\n\nعد بعد **{hours}س {minutes}د {seconds}ث**",
                color=discord.Color.orange()
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    # أمر /work للعمل
    @app_commands.command(name="work", description="اعمل واحصل على 50-200 ₿ (كل ساعة)")
    @app_commands.checks.cooldown(1, 3600, key=lambda i: i.user.id)
    async def work(self, interaction: discord.Interaction):
        jobs = [
            "مبرمج 💻", "طبيب 👨‍⚕️", "مهندس 👷", "معلم 👨‍🏫", 
            "طباخ 👨‍🍳", "فنان 🎨", "كاتب ✍️", "مصور 📸",
            "سائق 🚗", "مزارع 🌾", "صائد سمك 🎣", "نجار 🔨"
        ]
        job = random.choice(jobs)
        amount = random.randint(50, 200)
        
        user_data = self.get_user_data(interaction.user.id)
        user_data["balance"] += amount
        user_data["total_earned"] += amount
        user_data["last_work"] = discord.utils.utcnow().isoformat()
        self.add_transaction(interaction.user.id, "work", amount, f"عمل كـ {job}")
        self.save()

        embed = discord.Embed(
            title=f"💼 {job}",
            description=f"اشتغلت كـ **{job}** وكسبت **{amount} ₿** 💎",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"رصيدك الجديد: {user_data['balance']:,} ₿")
        
        await interaction.response.send_message(embed=embed)

    # معالجة خطأ الكولداون لأمر العمل
    @work.error
    async def work_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            remaining = int(error.retry_after)
            minutes = remaining // 60
            seconds = remaining % 60
            
            embed = discord.Embed(
                title="⏰ انتظر قليلاً",
                description=f"لقد عملت مؤخراً!\n\nعد بعد **{minutes}د {seconds}ث**",
                color=discord.Color.orange()
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)

    # أمر /transfer لتحويل Bitcoin
    @app_commands.command(name="transfer", description="تحويل Bitcoin لعضو آخر")
    @app_commands.describe(
        member="العضو اللي عايز تحوله",
        amount="المبلغ اللي عايز تحوله"
    )
    async def transfer(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1]):
        if member.id == interaction.user.id:
            embed = discord.Embed(
                title="❌ غير مسموح",
                description="لا يمكنك تحويل Bitcoin لنفسك!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if member.bot:
            embed = discord.Embed(
                title="❌ غير مسموح",
                description="لا يمكنك تحويل Bitcoin لبوت!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        sender_data = self.get_user_data(interaction.user.id)
        
        if sender_data["balance"] < amount:
            embed = discord.Embed(
                title="❌ رصيد غير كافٍ",
                description=f"رصيدك الحالي: **{sender_data['balance']:,} ₿**\nالمطلوب: **{amount:,} ₿**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        receiver_data = self.get_user_data(member.id)
        
        sender_data["balance"] -= amount
        sender_data["total_spent"] += amount
        self.add_transaction(interaction.user.id, "transfer_out", -amount, f"تحويل إلى {member.display_name}")
        
        receiver_data["balance"] += amount
        receiver_data["total_earned"] += amount
        self.add_transaction(member.id, "transfer_in", amount, f"تحويل من {interaction.user.display_name}")
        
        self.save()

        embed = discord.Embed(
            title="✅ تم التحويل",
            description=(
                f"تم تحويل **{amount:,} ₿** 💎\n\n"
                f"من: {interaction.user.mention}\n"
                f"إلى: {member.mention}"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"رصيدك الجديد: {sender_data['balance']:,} ₿")
        
        await interaction.response.send_message(embed=embed)

    # أمر /bitcoin-top لأفضل 10 أغنياء
    @app_commands.command(name="bitcoin-top", description="أفضل 10 أغنياء في Bitcoin")
    async def bitcoin_top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.data:
            await interaction.followup.send("❌ مفيش بيانات لسه!")
            return
        
        sorted_users = sorted(
            self.data.items(),
            key=lambda x: x[1]["balance"],
            reverse=True
        )[:10]
        
        medals = ["🥇", "🥈", "🥉"]
        description = ""
        
        for i, (user_id, udata) in enumerate(sorted_users):
            if udata["balance"] <= 0:
                continue
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"Unknown ({user_id})"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            description += f"{medal} **{name}** — 💎 {udata['balance']:,} ₿\n"
        
        if not description:
            await interaction.followup.send("❌ مفيش أعضاء عندهم Bitcoin!")
            return
        
        embed = discord.Embed(
            title="🏆 أفضل 10 أغنياء في Bitcoin",
            description=description,
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.followup.send(embed=embed)

    # أمر /bitcoin-history لعرض سجل المعاملات
    @app_commands.command(name="bitcoin-history", description="عرض سجل معاملاتك")
    async def bitcoin_history(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_data = self.get_user_data(interaction.user.id)
        transactions = user_data.get("transactions", [])
        
        if not transactions:
            embed = discord.Embed(
                title="📜 سجل المعاملات",
                description="لا توجد معاملات حتى الآن!",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        recent = transactions[-10:][::-1]
        description = ""
        
        for tx in recent:
            tx_type = tx["type"]
            amount = tx["amount"]
            desc = tx["description"]
            timestamp = tx.get("timestamp", "")
            
            icons = {
                "daily": "🎁",
                "work": "💼",
                "transfer_in": "📥",
                "transfer_out": "📤",
                "buy": "🛒",
                "admin": "⚙️"
            }
            icon = icons.get(tx_type, "💰")
            
            amount_str = f"+{amount:,}" if amount > 0 else f"{amount:,}"
            
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_str = f"<t:{int(dt.timestamp())}:R>"
            except:
                time_str = "غير معروف"
            
            description += f"{icon} **{amount_str} ₿** — {desc} ({time_str})\n"
        
        embed = discord.Embed(
            title="📜 سجل المعاملات (آخر 10)",
            description=description,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"إجمالي المعاملات: {len(transactions)}")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    # أمر /bitcoin-shop لعرض المتجر
    @app_commands.command(name="bitcoin-shop", description="عرض متجر العناصر")
    async def bitcoin_shop(self, interaction: discord.Interaction):
        description = "🛒 **متجر Bitcoin** - اشترِ عناصر رائعة!\n\n"
        
        for item_id, item in SHOP_ITEMS.items():
            description += f"**{item['name']}**\n"
            description += f"└ السعر: 💎 **{item['price']:,} ₿**\n"
            description += f"└ {item['description']}\n"
            description += f"└ استخدم: `/buy item:{item_id}`\n\n"
        
        embed = discord.Embed(
            title="🏪 متجر Bitcoin",
            description=description,
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="استخدم /buy لشراء عنصر")
        
        await interaction.response.send_message(embed=embed)

    # أمر /buy لشراء عنصر
    @app_commands.command(name="buy", description="شراء عنصر من المتجر")
    @app_commands.describe(item="العنصر اللي عايز تشتريه")
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
    async def buy(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
        item_id = item.value
        item_data = SHOP_ITEMS.get(item_id)
        
        if not item_data:
            embed = discord.Embed(
                title="❌ عنصر غير موجود",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_data = self.get_user_data(interaction.user.id)
        price = item_data["price"]
        
        if user_data["balance"] < price:
            embed = discord.Embed(
                title="❌ رصيد غير كافٍ",
                description=(
                    f"رصيدك الحالي: **{user_data['balance']:,} ₿**\n"
                    f"السعر: **{price:,} ₿**\n"
                    f"النقص: **{price - user_data['balance']:,} ₿**"
                ),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_data["balance"] -= price
        user_data["total_spent"] += price
        
        if "inventory" not in user_data:
            user_data["inventory"] = []
        user_data["inventory"].append(item_id)
        
        self.add_transaction(interaction.user.id, "buy", -price, f"شراء {item_data['name']}")
        self.save()

        embed = discord.Embed(
            title="✅ تم الشراء",
            description=(
                f"اشتريت **{item_data['name']}** 💎\n\n"
                f"السعر: **{price:,} ₿**\n"
                f"رصيدك الجديد: **{user_data['balance']:,} ₿**"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    # مجموعة أوامر /bitcoin-admin للمشرفين
    bitcoin_admin = app_commands.Group(
        name="bitcoin-admin",
        description="أدوات إدارة Bitcoin (للمشرفين)",
        default_permissions=discord.Permissions(administrator=True)
    )

    # أمر إضافة Bitcoin
    @bitcoin_admin.command(name="add", description="إضافة Bitcoin لعضو")
    @app_commands.describe(
        member="العضو",
        amount="المبلغ",
        reason="السبب (اختياري)"
    )
    async def admin_add(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1], reason: str = None):
        user_data = self.get_user_data(member.id)
        user_data["balance"] += amount
        user_data["total_earned"] += amount
        
        reason_text = reason or "إضافة من المشرف"
        self.add_transaction(member.id, "admin", amount, reason_text)
        self.save()

        embed = discord.Embed(
            title="⚙️ تم إضافة Bitcoin",
            description=(
                f"تم إضافة **{amount:,} ₿** لـ {member.mention}\n"
                f"السبب: {reason_text}"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"رصيد العضو الجديد: {user_data['balance']:,} ₿")
        
        await interaction.response.send_message(embed=embed)

    # أمر خصم Bitcoin
    @bitcoin_admin.command(name="remove", description="خصم Bitcoin من عضو")
    @app_commands.describe(
        member="العضو",
        amount="المبلغ",
        reason="السبب (اختياري)"
    )
    async def admin_remove(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1], reason: str = None):
        user_data = self.get_user_data(member.id)
        
        if user_data["balance"] < amount:
            embed = discord.Embed(
                title="❌ رصيد غير كافٍ",
                description=f"رصيد العضو: **{user_data['balance']:,} ₿**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_data["balance"] -= amount
        user_data["total_spent"] += amount
        
        reason_text = reason or "خصم من المشرف"
        self.add_transaction(member.id, "admin", -amount, reason_text)
        self.save()

        embed = discord.Embed(
            title="⚙️ تم خصم Bitcoin",
            description=(
                f"تم خصم **{amount:,} ₿** من {member.mention}\n"
                f"السبب: {reason_text}"
            ),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"رصيد العضو الجديد: {user_data['balance']:,} ₿")
        
        await interaction.response.send_message(embed=embed)

    # أمر تعيين الرصيد
    @bitcoin_admin.command(name="set", description="تعيين رصيد عضو")
    @app_commands.describe(
        member="العضو",
        amount="الرصيد الجديد"
    )
    async def admin_set(self, interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 0]):
        user_data = self.get_user_data(member.id)
        old_balance = user_data["balance"]
        user_data["balance"] = amount
        
        self.add_transaction(member.id, "admin", amount - old_balance, f"تعيين الرصيد من المشرف")
        self.save()

        embed = discord.Embed(
            title="⚙️ تم تعيين الرصيد",
            description=(
                f"تم تعيين رصيد {member.mention} إلى **{amount:,} ₿**\n"
                f"الرصيد القديم: **{old_balance:,} ₿**"
            ),
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        await interaction.response.send_message(embed=embed)

    # أمر إعادة تعيين الرصيد
    @bitcoin_admin.command(name="reset", description="إعادة تعيين رصيد عضو")
    @app_commands.describe(member="العضو")
    async def admin_reset(self, interaction: discord.Interaction, member: discord.Member):
        user_data = self.get_user_data(member.id)
        old_balance = user_data["balance"]
        user_data["balance"] = 0
        user_data["total_earned"] = 0
        user_data["total_spent"] = 0
        user_data["transactions"] = []
        user_data["inventory"] = []
        self.save()

        embed = discord.Embed(
            title="🔄 تم إعادة التعيين",
            description=f"تم إعادة تعيين بيانات {member.mention} بالكامل",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        await interaction.response.send_message(embed=embed)

    # معالجة أخطاء الصلاحيات
    @admin_add.error
    @admin_remove.error
    @admin_set.error
    @admin_reset.error
    async def admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ مفيش عندك صلاحية Administrator!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(Bitcoin(bot))