import discord
from discord.ext import commands
from discord import app_commands
import random
from config import Colors


class Fun(commands.Cog):
    """🎮 أوامر الترفيه والألعاب السريعة"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 🎲 نرد
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="dice", aliases=["نرد", "زهر"], description="🎲 رمي النرد")
    @app_commands.describe(sides="عدد الأوجه (افتراضي 6)")
    async def dice(self, ctx: commands.Context, sides: int = 6):
        sides = max(2, min(1000, sides))
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 النرد",
            description=f"طلع لك **{result}** من {sides}",
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🪙 عملة
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="coin", aliases=["عملة", "قلب_عملة"], description="🪙 رمي عملة")
    async def coin(self, ctx: commands.Context):
        result = random.choice(["صورة 👑", "كتابة 📝"])
        embed = discord.Embed(
            title="🪙 العملة",
            description=f"طلعت **{result}**",
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔮 كرة
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="ball", aliases=["كرة", "الكرة_السحرية"], description="🔮 اسأل الكرة السحرية")
    @app_commands.describe(question="سؤالك")
    async def ball(self, ctx: commands.Context, *, question: str):
        answers = [
            "اكيد 💯", "نعم", "مؤكد", "على الأغلب نعم", "الأمور تبشر بالخير",
            "مو متأكد، اسأل مرة ثانية", "ركز واسأل بعدين", "لا أنصحك",
            "لا", "مستحيل", "الأغلب لا", "ما أتوقع"
        ]
        embed = discord.Embed(title="🔮 الكرة السحرية", color=Colors.FUN)
        embed.add_field(name="❓ السؤال", value=question, inline=False)
        embed.add_field(name="💬 الجواب", value=random.choice(answers), inline=False)
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🤔 اختر
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="choose", aliases=["اختر", "اختار"], description="🤔 اختيار عشوائي")
    @app_commands.describe(options="خياراتك مفصولة بـ |")
    async def choose(self, ctx: commands.Context, *, options: str):
        choices = [x.strip() for x in options.split("|") if x.strip()]
        if len(choices) < 2:
            await ctx.send("❌ اكتب خيارين على الأقل مفصولة بـ `|`")
            return
        result = random.choice(choices)
        embed = discord.Embed(
            title="🤔 اختياري",
            description=f"أنا اخترت: **{result}**",
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # ✊ حجر ورقة مقص
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="rps", aliases=["حجر_ورقة_مقص"], description="✊ حجر ورقة مقص")
    @app_commands.describe(choice="حجر / ورقة / مقص")
    async def rps(self, ctx: commands.Context, choice: str):
        rps_map = {"حجر": "🪨", "ورقة": "📄", "مقص": "✂️"}
        beats = {"حجر": "مقص", "ورقة": "حجر", "مقص": "ورقة"}
        if choice not in rps_map:
            await ctx.send("❌ اختر: `حجر` أو `ورقة` أو `مقص`")
            return
        bot_choice = random.choice(list(rps_map.keys()))
        if choice == bot_choice:
            result = "تعادل 🤝"
            color = Colors.WARNING
        elif beats[choice] == bot_choice:
            result = "فزت 🎉"
            color = Colors.SUCCESS
        else:
            result = "خسرت 💔"
            color = Colors.ERROR
        embed = discord.Embed(title="✊ حجر ورقة مقص", color=color)
        embed.description = f"أنت: {rps_map[choice]} **{choice}**\nأنا: {rps_map[bot_choice]} **{bot_choice}**\n\n## {result}"
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 💘 حب
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="love", aliases=["حب", "نسبة_الحب"], description="💘 نسبة الحب")
    @app_commands.describe(member="العضو")
    async def love(self, ctx: commands.Context, member: discord.Member):
        seed = "".join(sorted([str(ctx.author.id), str(member.id)]))
        hash_val = 0
        for ch in seed:
            hash_val = (hash_val * 31 + ord(ch)) % 101
        bar = "▰" * (hash_val // 10) + "▱" * (10 - hash_val // 10)
        embed = discord.Embed(
            title="💘 مقياس الحب",
            description=f"{ctx.author.mention} ❤️ {member.mention}\n\n{bar} **{hash_val}%**",
            color=0xE91E63
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔁 عكس
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="reverse", aliases=["عكس", "اعكس"], description="🔁 عكس نص")
    @app_commands.describe(text="النص")
    async def reverse(self, ctx: commands.Context, *, text: str):
        embed = discord.Embed(
            title="🔁 النص المعكوس",
            description="".join(reversed(text)),
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 📜 حكمة
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="wisdom", aliases=["حكمة", "قول"], description="📜 حكمة عشوائية")
    async def wisdom(self, ctx: commands.Context):
        wisdoms = [
            "من جدّ وجد ومن زرع حصد.",
            "الوقت كالسيف إن لم تقطعه قطعك.",
            "اللي ما يعرف الصقر يشويه.",
            "الصديق وقت الضيق.",
            "العلم في الصغر كالنقش على الحجر.",
            "خير الكلام ما قل ودل.",
            "من صبر ظفر.",
            "الوحدة خير من جليس السوء.",
            "اللي يبي العسل يصبر على قرص النحل.",
            "القناعة كنز لا يفنى."
        ]
        embed = discord.Embed(
            title="📜 حكمة",
            description=f"> {random.choice(wisdoms)}",
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 😂 نكتة
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="joke", aliases=["نكتة", "اضحكني"], description="😂 نكتة عشوائية")
    async def joke(self, ctx: commands.Context):
        jokes = [
            "واحد راح للدكتور قال له: كل ما أشرب قهوة أحس بألم في عيني، قال له: جرب تشيل الملعقة من الكوب.",
            "مرة واحد غبي اشترى ساعة، قالوا له ليش؟ قال: عشان أعرف كم الوقت الضايع.",
            "واحد سأل صاحبه: ليش تنام والنافذة مفتوحة؟ قال: عشان الحلم يدخل بسرعة.",
            "قال المدرس: من يعطيني جملة فيها كلمة \"لأن\"؟ قال طالب: أنا ما سويت الواجب لأن.",
            "واحد بخيل ما يشرب شاي لأن الكوب يكلف ماء."
        ]
        embed = discord.Embed(
            title="😂 نكتة",
            description=random.choice(jokes),
            color=Colors.FUN
        )
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🤷 خيروك
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="wyr", aliases=["خيروك", "لو_خيروك"], description="🤷 سؤال لو خيروك")
    async def wyr(self, ctx: commands.Context):
        questions = [
            "لو خيروك: تعيش بالماضي أو بالمستقبل؟",
            "لو خيروك: تفقد جوالك أسبوع أو تفقد النوم ليلة؟",
            "لو خيروك: تكون غني ومشغول أو متوسط وعندك وقت؟",
            "لو خيروك: تسافر لأي مكان أو تتعلم أي مهارة؟",
            "لو خيروك: تعرف متى تموت أو كيف تموت؟",
            "لو خيروك: تقرأ الأفكار أو تختفي متى ما تبي؟",
            "لو خيروك: صديق واحد وفي أو عشرة معارف؟",
            "لو خيروك: تاكل أكلة وحدة طول عمرك أو ما تاكل المفضلة أبداً؟"
        ]
        embed = discord.Embed(
            title="🤷 لو خيروك",
            description=random.choice(questions),
            color=Colors.FUN
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")

    # ═══════════════════════════════════════
    # ⚡ سرعة
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="fast", aliases=["سرعة", "تحدي"], description="⚡ أول من يكتب الكلمة")
    async def fast(self, ctx: commands.Context):
        words = ["مستشفى", "مدرسة", "سيارة", "طائرة", "حاسوب", "مكتبة", "برمجة", "سيرفر", "شجرة", "صحراء"]
        word = random.choice(words)
        embed = discord.Embed(
            title="⚡ تحدي السرعة",
            description=f"اكتب الكلمة دي بأسرع ما تقدر:\n## {word}\n\nعندكم **15** ثانية",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.channel.id == ctx.channel.id and m.content.strip() == word and not m.author.bot

        try:
            winner = await self.bot.wait_for("message", check=check, timeout=15)
            embed = discord.Embed(
                title="🏆 فائز",
                description=f"{winner.author.mention} أجاب أول!",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(
                title="⏰ انتهى الوقت",
                description=f"الكلمة كانت: **{word}**",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🔢 حساب
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="math", aliases=["حساب", "رياضيات"], description="🔢 أول من يحل المسألة")
    async def math(self, ctx: commands.Context):
        a = random.randint(10, 99)
        b = random.randint(2, 20)
        op = random.choice(["+", "-", "×"])
        if op == "+":
            answer = a + b
        elif op == "-":
            answer = a - b
        else:
            answer = a * b
        embed = discord.Embed(
            title="🔢 تحدي الرياضيات",
            description=f"احسب الناتج:\n## {a} {op} {b}\n\nعندكم **20** ثانية",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.channel.id == ctx.channel.id and m.content.strip() == str(answer) and not m.author.bot

        try:
            winner = await self.bot.wait_for("message", check=check, timeout=20)
            embed = discord.Embed(
                title="🏆 فائز",
                description=f"{winner.author.mention} حل المسألة!",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(
                title="⏰ انتهى الوقت",
                description=f"الإجابة: **{answer}**",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)

    # ═══════════════════════════════════════
    # 🎯 تخمين
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="guess", aliases=["تخمين", "خمن"], description="🎯 خمن الرقم من 1 لـ 50")
    async def guess(self, ctx: commands.Context):
        secret = random.randint(1, 50)
        embed = discord.Embed(
            title="🔢 خمن الرقم",
            description="فكرت برقم من **1** إلى **50**\nعندك **6** محاولات، اكتب تخمينك في الشات",
            color=Colors.WARNING
        )
        await ctx.send(embed=embed)
        tries = 6

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.strip().isdigit()

        while tries > 0:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except:
                await ctx.send(f"⏰ انتهى الوقت! الرقم كان **{secret}**")
                return
            guess = int(msg.content.strip())
            tries -= 1
            if guess == secret:
                await ctx.send(f"🎉 صح! الرقم هو **{secret}**")
                return
            if tries == 0:
                await ctx.send(f"💔 خلصت محاولاتك! الرقم كان **{secret}**")
                return
            hint = "أكبر" if guess < secret else "أصغر"
            await ctx.send(f"❌ الرقم **{hint}** من تخمينك • باقي **{tries}** محاولات")

    # ═══════════════════════════════════════
    # 🔤 حرف
    # ═══════════════════════════════════════
    @commands.hybrid_command(name="letter", aliases=["حرف", "حرف_عشوائي"], description="🔤 حرف عشوائي")
    async def letter(self, ctx: commands.Context):
        letters = "أبتثجحخدذرزسشصضطظعغفقكلمنهوي"
        embed = discord.Embed(
            title="🔤 حرف عشوائي",
            description=f"## {random.choice(list(letters))}",
            color=Colors.FUN
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))