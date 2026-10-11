import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import asyncio
from typing import List, Optional

# ═══════════════════════════════════════
# 📁 إعدادات
# ═══════════════════════════════════════
GAMES_FILE = "games.json"

WIN_REWARD = 50
MINI_WIN_REWARD = 5
LOBBY_SECONDS = 45


def load_data():
    if os.path.exists(GAMES_FILE):
        try:
            with open(GAMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_data(data):
    with open(GAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ═══════════════════════════════════════
# 🎮 LobbyView للألعاب الجماعية
# ═══════════════════════════════════════
class LobbyView(discord.ui.View):
    def __init__(self, game_name: str, min_players: int, max_players: int, callback, timeout: int = LOBBY_SECONDS):
        super().__init__(timeout=timeout)
        self.game_name = game_name
        self.min_players = min_players
        self.max_players = max_players
        self.players: List[discord.Member] = []
        self.callback = callback
        self.started = False
        self.message: Optional[discord.Message] = None

    async def update_message(self):
        if not self.message:
            return
        embed = discord.Embed(
            title=f"🎮 {self.game_name}",
            description=self.get_players_list(),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"اللاعبين: {len(self.players)}/{self.max_players} | الحد الأدنى: {self.min_players} | يبدأ خلال {int(self.timeout)} ثانية")
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

    def get_players_list(self):
        if not self.players:
            return "لا يوجد لاعبين بعد... اضغط على زر الانضمام!"
        lines = []
        for i, p in enumerate(self.players, 1):
            lines.append(f"`{i}.` {p.mention}")
        return "\n".join(lines)

    @discord.ui.button(label="انضمام 🎯", style=discord.ButtonStyle.success, custom_id="join_btn")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("❌ اللعبة بدأت بالفعل!", ephemeral=True)
        if interaction.user in self.players:
            return await interaction.response.send_message("❌ أنت بالفعل في اللوبي!", ephemeral=True)
        if len(self.players) >= self.max_players:
            return await interaction.response.send_message("❌ اللوبي ممتلئ!", ephemeral=True)
        self.players.append(interaction.user)
        await interaction.response.send_message(f"✅ انضممت للعبة!", ephemeral=True)
        await self.update_message()

    @discord.ui.button(label="خروج 🚪", style=discord.ButtonStyle.danger, custom_id="leave_btn")
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("❌ اللعبة بدأت بالفعل!", ephemeral=True)
        if interaction.user not in self.players:
            return await interaction.response.send_message("❌ أنت مش في اللوبي!", ephemeral=True)
        self.players.remove(interaction.user)
        await interaction.response.send_message(f"👋 خرجت من اللعبة!", ephemeral=True)
        await self.update_message()

    @discord.ui.button(label="بدء اللعبة ▶️", style=discord.ButtonStyle.primary, custom_id="start_btn")
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.started:
            return await interaction.response.send_message("❌ اللعبة بدأت بالفعل!", ephemeral=True)
        if len(self.players) < self.min_players:
            return await interaction.response.send_message(
                f"❌ لازم {self.min_players} لاعبين على الأقل! (الحالي: {len(self.players)})", ephemeral=True
            )
        if interaction.user != self.players[0]:
            return await interaction.response.send_message("❌ فقط صاحب اللوبي يقدر يبدأ اللعبة!", ephemeral=True)
        self.started = True
        self.stop()
        await interaction.response.send_message("🚀 جاري بدء اللعبة...", ephemeral=True)
        try:
            await self.callback(self.players, self.message)
        except Exception as e:
            await self.message.channel.send(f"❌ حدث خطأ في اللعبة: {e}")

    async def on_timeout(self):
        if self.started:
            return
        if len(self.players) < self.min_players and self.message:
            embed = discord.Embed(
                title=f"⏰ انتهى وقت اللوبي - {self.game_name}",
                description="لم يصل عدد اللاعبين للحد الأدنى!",
                color=discord.Color.red()
            )
            try:
                await self.message.edit(embed=embed, view=None)
            except:
                pass


# ═══════════════════════════════════════
# 🎮 الألعاب الجماعية
# ═══════════════════════════════════════

async def g_bomb(players, message, bot):
    """القنبلة الموقوتة"""
    channel = message.channel
    current_players = list(players)
    fuse = random.randint(3, 8)
    current_holder = random.choice(current_players)

    embed = discord.Embed(
        title="💣 القنبلة الموقوتة",
        description=f"القنبلة مع {current_holder.mention}!\nالفتيل: {fuse} تمريرة",
        color=discord.Color.red()
    )
    msg = await channel.send(embed=embed)

    passes = 0
    while len(current_players) > 1:
        await asyncio.sleep(random.uniform(1.5, 3.0))
        passes += 1

        others = [p for p in current_players if p != current_holder]
        if not others:
            break
        current_holder = random.choice(others)

        embed = discord.Embed(
            title="💣 القنبلة تنتقل!",
            description=f"مع {current_holder.mention}!\nالتمريرات: {passes}/{fuse}",
            color=discord.Color.orange()
        )
        try:
            await msg.edit(embed=embed)
        except:
            pass

        if passes >= fuse:
            embed = discord.Embed(
                title="💥 انفجرت القنبلة!",
                description=f"{current_holder.mention} خرج من اللعبة!",
                color=discord.Color.dark_red()
            )
            await msg.edit(embed=embed)
            current_players.remove(current_holder)
            if len(current_players) == 1:
                break
            current_holder = random.choice(current_players)
            fuse = random.randint(3, 8)
            passes = 0
            await asyncio.sleep(2)

    if current_players:
        winner = current_players[0]
        await add_fizzy(bot, winner.id, WIN_REWARD)
        embed = discord.Embed(
            title="🏆 الفائز!",
            description=f"{winner.mention} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)


async def g_button(players, message, bot):
    """زر الحظ"""
    channel = message.channel
    current_players = list(players)

    while len(current_players) > 1:
        loser_index = random.randint(0, 8)
        view = discord.ui.View(timeout=30)

        for i in range(9):
            btn = discord.ui.Button(label=str(i + 1), style=discord.ButtonStyle.secondary, custom_id=f"btn_{i}")
            view.add_item(btn)

        embed = discord.Embed(
            title="🎲 زر الحظ",
            description="اختر زراً! واحد منهم خاسر 😈",
            color=discord.Color.purple()
        )
        msg = await channel.send(embed=embed, view=view)

        for player in current_players:
            try:
                def check(interaction):
                    return interaction.user.id == player.id and interaction.message.id == msg.id
                interaction = await bot.wait_for("interaction", check=check, timeout=30)
                choice = int(interaction.data["custom_id"].split("_")[1])
                await interaction.response.send_message("✅ تم اختيارك!", ephemeral=True)
            except asyncio.TimeoutError:
                choice = random.randint(0, 8)

            if choice == loser_index:
                embed = discord.Embed(
                    title="💀 حظ سيء!",
                    description=f"{player.mention} اختار الزر الخاسر وخرج!",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                current_players.remove(player)
                break

        await asyncio.sleep(2)

    if current_players:
        winner = current_players[0]
        await add_fizzy(bot, winner.id, WIN_REWARD)
        embed = discord.Embed(
            title="🏆 الفائز!",
            description=f"{winner.mention} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)


async def g_chairs(players, message, bot):
    """الكراسي الموسيقية"""
    channel = message.channel
    current_players = list(players)

    while len(current_players) > 1:
        chairs = len(current_players) - 1
        survivors = random.sample(current_players, chairs)
        eliminated = [p for p in current_players if p not in survivors]

        embed = discord.Embed(
            title="🪑 الكراسي الموسيقية",
            description=f"الكراسي المتاحة: {chairs}\n\n" + "\n".join([f"❌ {p.mention} مفيش عنده كرسي!" for p in eliminated]),
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)

        current_players = survivors
        await asyncio.sleep(3)

    if current_players:
        winner = current_players[0]
        await add_fizzy(bot, winner.id, WIN_REWARD)
        embed = discord.Embed(
            title="🏆 الفائز!",
            description=f"{winner.mention} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)


async def g_mafia(players, message, bot):
    """المافيا"""
    channel = message.channel
    current_players = list(players)

    roles = ["مافيا 🗡️", "طبيب 💊", "محقق 🔍"] + ["مواطن 👤"] * (len(current_players) - 3)
    random.shuffle(roles)
    player_roles = dict(zip(current_players, roles))

    for player, role in player_roles.items():
        try:
            await player.send(f"🎭 دورك في لعبة المافيا: **{role}**")
        except:
            pass

    embed = discord.Embed(
        title="🎭 بدأت لعبة المافيا!",
        description=f"عدد اللاعبين: {len(current_players)}\nتم إرسال الأدوار!",
        color=discord.Color.dark_purple()
    )
    await channel.send(embed=embed)

    round_num = 1
    winner = None
    while len([p for p, r in player_roles.items() if r == "مافيا 🗡️"]) > 0:
        embed = discord.Embed(
            title=f"🌙 الليل - الجولة {round_num}",
            description="المافيا تختار ضحيتها...",
            color=discord.Color.dark_blue()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(5)

        civilians = [p for p, r in player_roles.items() if r != "مافيا 🗡️"]
        if not civilians:
            break

        victim = random.choice(civilians)
        del player_roles[victim]

        embed = discord.Embed(
            title=f"☀️ النهار - الجولة {round_num}",
            description=f"تم العثور على جثة {victim.mention}! 💀",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(5)

        if len(player_roles) > 2:
            voted = random.choice(list(player_roles.keys()))
            role = player_roles.get(voted, "مجهول")
            del player_roles[voted]
            embed = discord.Embed(
                title="⚖️ تم التصويت!",
                description=f"تم إعدام {voted.mention}!\nدوره كان: **{role}**",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            await asyncio.sleep(3)

        round_num += 1

    mafia_left = [p for p, r in player_roles.items() if r == "مافيا 🗡️"]
    if mafia_left:
        winner = mafia_left[0]
        embed = discord.Embed(
            title="🗡️ المافيا فازت!",
            description=f"{winner.mention} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.dark_red()
        )
    else:
        citizens = [p for p, r in player_roles.items() if r != "مافيا 🗡️"]
        winner = citizens[0] if citizens else None
        embed = discord.Embed(
            title="👤 المواطنون فازوا!",
            description=f"{winner.mention if winner else 'لا أحد'} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.green()
        )

    await channel.send(embed=embed)
    if winner:
        await add_fizzy(bot, winner.id, WIN_REWARD)


async def g_roulette(players, message, bot):
    """الروليت الروسية"""
    channel = message.channel
    current_players = list(players)

    embed = discord.Embed(
        title="🔫 الروليت الروسية",
        description="كل واحد يسحب الزناد... احتمال 1/6!",
        color=discord.Color.dark_gray()
    )
    await channel.send(embed=embed)

    while len(current_players) > 1:
        for player in list(current_players):
            await asyncio.sleep(2)
            if random.randint(1, 6) == 1:
                embed = discord.Embed(
                    title="💀 بام!",
                    description=f"{player.mention} المسدس أطلق! 💥",
                    color=discord.Color.dark_red()
                )
                await channel.send(embed=embed)
                current_players.remove(player)
                break
            else:
                embed = discord.Embed(
                    title="😅 نجا!",
                    description=f"{player.mention} سحب الزناد... ونجا!",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)

    if current_players:
        winner = current_players[0]
        await add_fizzy(bot, winner.id, WIN_REWARD)
        embed = discord.Embed(
            title="🏆 الناجي الأخير!",
            description=f"{winner.mention} فاز بـ **{WIN_REWARD} Fizzy** 💰",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)


# ═══════════════════════════════════════
# ⚡ الألعاب السريعة
# ═══════════════════════════════════════

async def g_colors(message, bot):
    """تخمين الألوان"""
    colors = {
        "🔴 أحمر": discord.Color.red(),
        "🔵 أزرق": discord.Color.blue(),
        "🟢 أخضر": discord.Color.green(),
        "🟡 أصفر": discord.Color.gold(),
        "🟣 بنفسجي": discord.Color.purple()
    }

    correct = random.choice(list(colors.keys()))
    correct_color = colors[correct]

    view = discord.ui.View(timeout=15)
    for color_name in colors.keys():
        btn = discord.ui.Button(
            label=color_name.split(" ")[1],
            emoji=color_name.split(" ")[0],
            style=discord.ButtonStyle.secondary,
            custom_id=f"color_{color_name}"
        )
        view.add_item(btn)

    embed = discord.Embed(
        title="🎨 تخمين اللون!",
        description="أي لون هو الصح؟ أول واحد يدوس الصح يكسب!",
        color=correct_color
    )
    msg = await message.channel.send(embed=embed, view=view)

    def check(interaction):
        return interaction.message.id == msg.id

    try:
        interaction = await bot.wait_for("interaction", check=check, timeout=15)
        chosen = interaction.data["custom_id"].replace("color_", "")

        if chosen == correct:
            await add_fizzy(bot, interaction.user.id, MINI_WIN_REWARD)
            embed = discord.Embed(
                title="✅ إجابة صحيحة!",
                description=f"{interaction.user.mention} كسب **{MINI_WIN_REWARD} Fizzy** 💰",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ إجابة خاطئة!",
                description=f"الإجابة: {correct}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="⏰ انتهى الوقت!",
            description=f"الإجابة: {correct}",
            color=discord.Color.orange()
        )
        await msg.edit(embed=embed, view=None)


async def g_faster(message, bot):
    """الأسرع في الكتابة"""
    words = ["python", "discord", "fizzy", "game", "winner", "fast", "speed", "keyboard"]
    word = random.choice(words)

    embed = discord.Embed(
        title="⚡ الأسرع في الكتابة!",
        description=f"اكتب الكلمة دي الأول: **{word}**",
        color=discord.Color.yellow()
    )
    await message.channel.send(embed=embed)

    def check(m):
        return m.channel.id == message.channel.id and m.content.lower() == word.lower() and not m.author.bot

    try:
        winner_msg = await bot.wait_for("message", check=check, timeout=20)
        await add_fizzy(bot, winner_msg.author.id, MINI_WIN_REWARD)
        embed = discord.Embed(
            title="🏆 الفائز!",
            description=f"{winner_msg.author.mention} كسب **{MINI_WIN_REWARD} Fizzy** 💰",
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="⏰ انتهى الوقت!",
            description=f"الكلمة كانت: **{word}**",
            color=discord.Color.orange()
        )
        await message.channel.send(embed=embed)


async def g_flags(message, bot):
    """تخمين الأعلام"""
    flags = {
        "🇪🇬": "مصر", "🇸🇦": "السعودية", "🇺🇸": "أمريكا",
        "🇫🇷": "فرنسا", "🇯🇵": "اليابان", "🇩🇪": "ألمانيا",
        "🇬🇧": "بريطانيا", "🇧🇷": "البرازيل"
    }

    flag_emoji, country = random.choice(list(flags.items()))

    embed = discord.Embed(
        title="🏳️ تخمين العلم!",
        description=f"أي دولة العلم ده؟ {flag_emoji}",
        color=discord.Color.blue()
    )
    await message.channel.send(embed=embed)

    def check(m):
        return (m.channel.id == message.channel.id and
                m.content.strip().lower() == country.lower() and
                not m.author.bot)

    try:
        winner_msg = await bot.wait_for("message", check=check, timeout=20)
        await add_fizzy(bot, winner_msg.author.id, MINI_WIN_REWARD)
        embed = discord.Embed(
            title="🏆 إجابة صحيحة!",
            description=f"{winner_msg.author.mention} كسب **{MINI_WIN_REWARD} Fizzy** 💰\nالإجابة: **{country}**",
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="⏰ انتهى الوقت!",
            description=f"الإجابة: **{country}**",
            color=discord.Color.orange()
        )
        await message.channel.send(embed=embed)


# ═══════════════════════════════════════
# 🛠️ دوال مساعدة
# ═══════════════════════════════════════

async def add_fizzy(bot, user_id: int, amount: int):
    cog = bot.get_cog("Games")
    if cog:
        cog.add_fizzy_to_user(user_id, amount)


# ═══════════════════════════════════════
# 🎮 الـ Cog الرئيسي
# ═══════════════════════════════════════

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.active_games = set()

    def get_user_data(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {"fizzy": 0}
        return self.data[user_id]

    def add_fizzy_to_user(self, user_id: int, amount: int):
        user_data = self.get_user_data(user_id)
        user_data["fizzy"] += amount
        self.save()

    def save(self):
        save_data(self.data)

    async def _run_game(self, interaction, game_name):
        """تشغيل لعبة من الاسم"""
        channel_id = interaction.channel.id

        if channel_id in self.active_games:
            embed = discord.Embed(
                title="❌ يوجد لعبة نشطة",
                description="استنى اللعبة الحالية تخلص!",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.active_games.add(channel_id)

        # الألعاب السريعة
        if game_name in ["colors", "faster", "flags"]:
            await interaction.response.send_message(f"🎮 جاري بدء اللعبة...")
            try:
                if game_name == "colors":
                    await g_colors(interaction.channel, self.bot)
                elif game_name == "faster":
                    await g_faster(interaction.channel, self.bot)
                elif game_name == "flags":
                    await g_flags(interaction.channel, self.bot)
            finally:
                self.active_games.discard(channel_id)
            return

        # الألعاب الجماعية
        game_configs = {
            "bomb": ("💣 القنبلة الموقوتة", 2, 10, g_bomb),
            "button": ("🎲 زر الحظ", 2, 8, g_button),
            "chairs": ("🪑 الكراسي الموسيقية", 3, 10, g_chairs),
            "mafia": ("🎭 المافيا", 5, 15, g_mafia),
            "roulette": ("🔫 الروليت الروسية", 2, 6, g_roulette),
        }

        title, min_p, max_p, callback = game_configs[game_name]

        async def game_callback(players, msg):
            try:
                await callback(players, msg, self.bot)
            finally:
                self.active_games.discard(channel_id)

        lobby = LobbyView(title, min_p, max_p, game_callback)
        embed = discord.Embed(
            title=f"🎮 {title}",
            description=lobby.get_players_list(),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"اللاعبين: 0/{max_p} | الحد الأدنى: {min_p}")

        await interaction.response.send_message(embed=embed, view=lobby)
        lobby.message = await interaction.original_response()
        await lobby.wait()
        if not lobby.started:
            self.active_games.discard(channel_id)

    # ═══════════════════════════════════════
    # 🌐 Slash Commands
    # ═══════════════════════════════════════

    @app_commands.command(name="game", description="بدء لعبة")
    @app_commands.describe(game="اختر اللعبة")
    @app_commands.choices(game=[
        app_commands.Choice(name="💣 القنبلة (2-10)", value="bomb"),
        app_commands.Choice(name="🎲 زر الحظ (2-8)", value="button"),
        app_commands.Choice(name="🪑 الكراسي (3-10)", value="chairs"),
        app_commands.Choice(name="🎨 الألوان", value="colors"),
        app_commands.Choice(name="⚡ الأسرع", value="faster"),
        app_commands.Choice(name="🏳️ الأعلام", value="flags"),
        app_commands.Choice(name="🎭 المافيا (5-15)", value="mafia"),
        app_commands.Choice(name="🔫 الروليت (2-6)", value="roulette"),
    ])
    async def game_slash(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        await self._run_game(interaction, game.value)

    @app_commands.command(name="fizzy", description="عرض رصيد Fizzy")
    async def fizzy_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = self.get_user_data(target.id)
        embed = discord.Embed(
            title=f"💰 رصيد Fizzy - {target.display_name}",
            description=f"رصيدك: **{user_data['fizzy']} Fizzy** 💎",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fizzytop", description="أفضل 10 لاعبين")
    async def fizzytop_slash(self, interaction: discord.Interaction):
        if not self.data:
            return await interaction.response.send_message("❌ مفيش لاعبين!")
        sorted_users = sorted(self.data.items(), key=lambda x: x[1]["fizzy"], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, udata) in enumerate(sorted_users):
            if udata["fizzy"] == 0:
                continue
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} **{name}** — 💎 {udata['fizzy']}\n"
        embed = discord.Embed(title="🏆 أفضل 10 لاعبين", description=desc or "لا توجد بيانات", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    # ═══════════════════════════════════════
    # 📨 Text Commands (للاختصارات)
    # ═══════════════════════════════════════

    @commands.command(name="bomb")
    async def bomb_text(self, ctx):
        """!bomb — القنبلة"""
        await self._run_game_text(ctx, "bomb")

    @commands.command(name="button")
    async def button_text(self, ctx):
        """!button — زر الحظ"""
        await self._run_game_text(ctx, "button")

    @commands.command(name="chairs")
    async def chairs_text(self, ctx):
        """!chairs — الكراسي"""
        await self._run_game_text(ctx, "chairs")

    @commands.command(name="colors")
    async def colors_text(self, ctx):
        """!colors — الألوان"""
        await g_colors(ctx, self.bot)

    @commands.command(name="faster")
    async def faster_text(self, ctx):
        """!faster — الأسرع"""
        await g_faster(ctx, self.bot)

    @commands.command(name="flags")
    async def flags_text(self, ctx):
        """!flags — الأعلام"""
        await g_flags(ctx, self.bot)

    @commands.command(name="mafia")
    async def mafia_text(self, ctx):
        """!mafia — المافيا"""
        await self._run_game_text(ctx, "mafia")

    @commands.command(name="roulette")
    async def roulette_text(self, ctx):
        """!roulette — الروليت"""
        await self._run_game_text(ctx, "roulette")

    async def _run_game_text(self, ctx, game_name):
        """تشغيل لعبة من نص (مع LobbyView)"""
        channel_id = ctx.channel.id

        if channel_id in self.active_games:
            return await ctx.send("❌ يوجد لعبة نشطة!")

        self.active_games.add(channel_id)

        game_configs = {
            "bomb": ("💣 القنبلة الموقوتة", 2, 10, g_bomb),
            "button": ("🎲 زر الحظ", 2, 8, g_button),
            "chairs": ("🪑 الكراسي الموسيقية", 3, 10, g_chairs),
            "mafia": ("🎭 المافيا", 5, 15, g_mafia),
            "roulette": ("🔫 الروليت الروسية", 2, 6, g_roulette),
        }

        title, min_p, max_p, callback = game_configs[game_name]

        async def game_callback(players, msg):
            try:
                await callback(players, msg, self.bot)
            finally:
                self.active_games.discard(channel_id)

        lobby = LobbyView(title, min_p, max_p, game_callback)
        embed = discord.Embed(
            title=f"🎮 {title}",
            description=lobby.get_players_list(),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"اللاعبين: 0/{max_p} | الحد الأدنى: {min_p}")

        lobby.message = await ctx.send(embed=embed, view=lobby)
        await lobby.wait()
        if not lobby.started:
            self.active_games.discard(channel_id)

    @commands.command(name="fizzy")
    async def fizzy_text(self, ctx, member: discord.Member = None):
        """!fizzy — رصيد Fizzy"""
        target = member or ctx.author
        user_data = self.get_user_data(target.id)
        embed = discord.Embed(
            title=f"💰 رصيد Fizzy - {target.display_name}",
            description=f"رصيدك: **{user_data['fizzy']} Fizzy** 💎",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="fizzytop")
    async def fizzytop_text(self, ctx):
        """!fizzytop — أفضل 10 لاعبين"""
        if not self.data:
            return await ctx.send("❌ مفيش لاعبين!")
        sorted_users = sorted(self.data.items(), key=lambda x: x[1]["fizzy"], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, udata) in enumerate(sorted_users):
            if udata["fizzy"] == 0:
                continue
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"Unknown"
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            desc += f"{medal} **{name}** — 💎 {udata['fizzy']}\n"
        embed = discord.Embed(title="🏆 أفضل 10 لاعبين", description=desc or "لا توجد بيانات", color=discord.Color.gold())
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Games(bot))