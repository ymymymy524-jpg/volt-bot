import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
from typing import Optional

# تحميل المتغيرات من ملف .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# إعدادات Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    vision_model = genai.GenerativeModel('gemini-pro-vision')
else:
    model = None
    vision_model = None


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 🌐 Slash Commands (زي ما هي)
    # ═══════════════════════════════════════
    ai_group = app_commands.Group(
        name="ai",
        description="أوامر الذكاء الاصطناعي باستخدام Gemini"
    )

    @ai_group.command(name="ask", description="اسأل الذكاء الاصطناعي أي سؤال")
    @app_commands.describe(question="السؤال اللي عايز تسأله")
    async def ai_ask(self, interaction: discord.Interaction, question: str):
        if not model:
            embed = discord.Embed(title="❌ خطأ في الإعدادات",
                                  description="لم يتم إعداد Gemini API Key!",
                                  color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            response = await asyncio.to_thread(model.generate_content, question)
            answer = response.text

            if len(answer) > 4000:
                answer = answer[:4000] + "\n\n... (تم اختصار الإجابة)"

            embed = discord.Embed(title="🤖 إجابة الذكاء الاصطناعي",
                                  description=answer,
                                  color=discord.Color.blue(),
                                  timestamp=discord.utils.utcnow())
            embed.set_footer(text=f"سُئل بواسطة: {interaction.user.display_name}")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(title="❌ حدث خطأ",
                                  description=f"```{str(e)}```",
                                  color=discord.Color.red())
            await interaction.followup.send(embed=embed)

    @ai_group.command(name="imagine", description="وصف صورة بالتفصيل")
    @app_commands.describe(prompt="وصف الصورة")
    async def ai_imagine(self, interaction: discord.Interaction, prompt: str):
        if not model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            image_prompt = f"صف صورة مفصلة عن: {prompt}"
            response = await asyncio.to_thread(model.generate_content, image_prompt)
            description = response.text

            embed = discord.Embed(
                title="🎨 وصف الصورة",
                description=f"**الوصف:**\n{description}",
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    @ai_group.command(name="translate", description="ترجمة نص")
    @app_commands.describe(text="النص", lang="اللغة")
    @app_commands.choices(lang=[
        app_commands.Choice(name="🇬🇧 إنجليزي", value="English"),
        app_commands.Choice(name="🇸🇦 عربي", value="Arabic"),
        app_commands.Choice(name="🇫🇷 فرنساوي", value="French"),
        app_commands.Choice(name="🇩🇪 ألماني", value="German"),
        app_commands.Choice(name="🇪🇸 إسباني", value="Spanish"),
        app_commands.Choice(name="🇹🇷 تركي", value="Turkish"),
    ])
    async def ai_translate(self, interaction: discord.Interaction, text: str, lang: app_commands.Choice[str]):
        if not model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            prompt = f"ترجم النص التالي إلى {lang.value}:\n\n{text}\n\nالترجمة فقط."
            response = await asyncio.to_thread(model.generate_content, prompt)
            translation = response.text

            embed = discord.Embed(title=f"🌐 الترجمة إلى {lang.name}",
                                  color=discord.Color.green())
            embed.add_field(name="📝 النص الأصلي", value=text[:1024], inline=False)
            embed.add_field(name="✅ الترجمة", value=translation[:1024], inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    @ai_group.command(name="summarize", description="تلخيص نص")
    @app_commands.describe(text="النص")
    async def ai_summarize(self, interaction: discord.Interaction, text: str):
        if not model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            prompt = f"لخص النص التالي:\n\n{text}"
            response = await asyncio.to_thread(model.generate_content, prompt)
            summary = response.text

            embed = discord.Embed(title="📋 الملخص",
                                  description=summary[:4000],
                                  color=discord.Color.orange())
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    @ai_group.command(name="code", description="كتابة كود")
    @app_commands.describe(task="المهمة")
    async def ai_code(self, interaction: discord.Interaction, task: str):
        if not model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            prompt = f"اكتب كود للمهمة التالية:\n\n{task}"
            response = await asyncio.to_thread(model.generate_content, prompt)
            code = response.text

            embed = discord.Embed(title="💻 الكود",
                                  description=f"```\n{code[:3900]}\n```",
                                  color=discord.Color.dark_theme())
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    @ai_group.command(name="story", description="كتابة قصة")
    @app_commands.describe(topic="الموضوع")
    async def ai_story(self, interaction: discord.Interaction, topic: str):
        if not model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            prompt = f"اكتب قصة قصيرة عن: {topic}"
            response = await asyncio.to_thread(model.generate_content, prompt)
            story = response.text

            embed = discord.Embed(title="📖 القصة",
                                  description=story[:4000],
                                  color=discord.Color.dark_purple())
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    @ai_group.command(name="analyze", description="تحليل صورة")
    @app_commands.describe(image="الصورة")
    async def ai_analyze(self, interaction: discord.Interaction, image: discord.Attachment):
        if not vision_model:
            await interaction.response.send_message("❌ Gemini غير مفعّل", ephemeral=True)
            return

        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message("❌ ملف غير صالح", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            image_bytes = await image.read()
            image_data = {'mime_type': image.content_type, 'data': image_bytes}
            prompt = "حلل الصورة بالتفصيل:"
            response = await asyncio.to_thread(vision_model.generate_content, [prompt, image_data])
            analysis = response.text

            embed = discord.Embed(title="🔍 تحليل الصورة",
                                  description=analysis[:4000],
                                  color=discord.Color.teal())
            embed.set_image(url=image.url)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ خطأ: {e}")

    # ═══════════════════════════════════════
    # 📨 Text Commands (للاختصارات)
    # ═══════════════════════════════════════
    @commands.command(name="ask")
    async def ask_text(self, ctx, *, question: str):
        """!ask - سؤال للـ AI"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content, question)
                answer = response.text

                if len(answer) > 4000:
                    answer = answer[:4000] + "..."

                embed = discord.Embed(title="🤖 إجابة AI", description=answer, color=0x3498DB)
                embed.set_footer(text=f"بواسطة: {ctx.author.display_name}")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="imagine")
    async def imagine_text(self, ctx, *, prompt: str):
        """!imagine - وصف صورة"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content, f"صف صورة مفصلة عن: {prompt}")
                embed = discord.Embed(title="🎨 وصف الصورة",
                                      description=response.text[:4000],
                                      color=0x9B59B6)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="translate")
    async def translate_text(self, ctx, lang: str, *, text: str):
        """!translate [اللغة] [النص]"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content,
                                                   f"ترجم النص التالي إلى {lang}:\n\n{text}")
                embed = discord.Embed(title=f"🌐 الترجمة إلى {lang}",
                                      color=0x2ECC71)
                embed.add_field(name="📝 الأصلي", value=text[:1024], inline=False)
                embed.add_field(name="✅ الترجمة", value=response.text[:1024], inline=False)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="summarize")
    async def summarize_text(self, ctx, *, text: str):
        """!summarize - تلخيص"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content, f"لخص: {text}")
                embed = discord.Embed(title="📋 الملخص",
                                      description=response.text[:4000],
                                      color=0xE67E22)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="code")
    async def code_text(self, ctx, *, task: str):
        """!code - كتابة كود"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content, f"اكتب كود: {task}")
                embed = discord.Embed(title="💻 الكود",
                                      description=f"```\n{response.text[:3900]}\n```",
                                      color=0x2C3E50)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="story")
    async def story_text(self, ctx, *, topic: str):
        """!story - قصة"""
        if not model:
            return await ctx.send("❌ Gemini غير مفعّل")

        try:
            async with ctx.typing():
                response = await asyncio.to_thread(model.generate_content, f"اكتب قصة عن: {topic}")
                embed = discord.Embed(title="📖 القصة",
                                      description=response.text[:4000],
                                      color=0x8E44AD)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")

    @commands.command(name="analyze")
    async def analyze_text(self, ctx):
        """!analyze - تحليل صورة (لازم ترفق صورة)"""
        if not vision_model:
            return await ctx.send("❌ Gemini غير مفعّل")

        if not ctx.message.attachments:
            return await ctx.send("❌ ارفق صورة مع الأمر")

        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await ctx.send("❌ الملف مش صورة")

        try:
            async with ctx.typing():
                image_bytes = await attachment.read()
                image_data = {'mime_type': attachment.content_type, 'data': image_bytes}
                response = await asyncio.to_thread(vision_model.generate_content,
                                                   ["حلل الصورة:", image_data])
                embed = discord.Embed(title="🔍 تحليل الصورة",
                                      description=response.text[:4000],
                                      color=0x1ABC9C)
                embed.set_image(url=attachment.url)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ خطأ: {e}")


async def setup(bot):
    await bot.add_cog(AI(bot))