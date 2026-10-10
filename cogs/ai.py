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

    # مجموعة أوامر /ai
    ai_group = app_commands.Group(
        name="ai",
        description="أوامر الذكاء الاصطناعي باستخدام Gemini"
    )

    # أمر /ai ask - سؤال للـ AI
    @ai_group.command(name="ask", description="اسأل الذكاء الاصطناعي أي سؤال")
    @app_commands.describe(question="السؤال اللي عايز تسأله")
    async def ai_ask(self, interaction: discord.Interaction, question: str):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!\nيرجى إضافته في ملف .env",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # إرسال السؤال للـ AI
            response = await asyncio.to_thread(
                model.generate_content,
                question
            )

            answer = response.text

            # تقسيم الإجابة لو طويلة (Discord limit: 4096 حرف في embed)
            if len(answer) > 4000:
                answer = answer[:4000] + "\n\n... (تم اختصار الإجابة)"

            embed = discord.Embed(
                title="🤖 إجابة الذكاء الاصطناعي",
                description=answer,
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"سُئل بواسطة: {interaction.user.display_name}")
            embed.set_thumbnail(url="https://i.imgur.com/gemini-icon.png")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء معالجة السؤال:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai imagine - توليد صورة
    @ai_group.command(name="imagine", description="توليد صورة باستخدام الذكاء الاصطناعي")
    @app_commands.describe(prompt="وصف الصورة اللي عايز تولدها")
    async def ai_imagine(self, interaction: discord.Interaction, prompt: str):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # طلب من Gemini وصف صورة مفصلة
            image_prompt = f"صف صورة مفصلة عن: {prompt}\n(وصف بصري فقط، بدون نص إضافي)"
            
            response = await asyncio.to_thread(
                model.generate_content,
                image_prompt
            )

            description = response.text

            embed = discord.Embed(
                title="🎨 وصف الصورة المولدة",
                description=f"**الوصف:**\n{description}\n\n⚠️ ملاحظة: Gemini لا يولد صور مباشرة، لكن يمكن وصف الصورة بالتفصيل.",
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء توليد الصورة:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai translate - ترجمة
    @ai_group.command(name="translate", description="ترجمة نص إلى لغة أخرى")
    @app_commands.describe(
        text="النص اللي عايز تترجمه",
        lang="اللغة اللي عايز تترجم ليها"
    )
    @app_commands.choices(lang=[
        app_commands.Choice(name="🇬🇧 إنجليزي", value="English"),
        app_commands.Choice(name="🇸🇦 عربي", value="Arabic"),
        app_commands.Choice(name="🇫🇷 فرنساوي", value="French"),
        app_commands.Choice(name="🇩🇪 ألماني", value="German"),
        app_commands.Choice(name="🇪🇸 إسباني", value="Spanish"),
        app_commands.Choice(name="🇮🇹 إيطالي", value="Italian"),
        app_commands.Choice(name="🇵🇹 برتغالي", value="Portuguese"),
        app_commands.Choice(name="🇷🇺 روسي", value="Russian"),
        app_commands.Choice(name="🇯🇵 ياباني", value="Japanese"),
        app_commands.Choice(name="🇰🇷 كوري", value="Korean"),
        app_commands.Choice(name="🇨🇳 صيني", value="Chinese"),
        app_commands.Choice(name="🇹🇷 تركي", value="Turkish"),
    ])
    async def ai_translate(self, interaction: discord.Interaction, text: str, lang: app_commands.Choice[str]):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # طلب الترجمة
            translate_prompt = f"ترجم النص التالي إلى {lang.value}:\n\n{text}\n\nالترجمة فقط، بدون أي نص إضافي."
            
            response = await asyncio.to_thread(
                model.generate_content,
                translate_prompt
            )

            translation = response.text

            if len(translation) > 4000:
                translation = translation[:4000] + "..."

            embed = discord.Embed(
                title=f"🌐 الترجمة إلى {lang.name}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="📝 النص الأصلي", value=text[:1024], inline=False)
            embed.add_field(name="✅ الترجمة", value=translation, inline=False)
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء الترجمة:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai summarize - تلخيص
    @ai_group.command(name="summarize", description="تلخيص نص طويل")
    @app_commands.describe(text="النص اللي عايز تلخصه")
    async def ai_summarize(self, interaction: discord.Interaction, text: str):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # طلب التلخيص
            summarize_prompt = f"لخص النص التالي بشكل مختصر ومفيد:\n\n{text}\n\nالتلخيص:"
            
            response = await asyncio.to_thread(
                model.generate_content,
                summarize_prompt
            )

            summary = response.text

            if len(summary) > 4000:
                summary = summary[:4000] + "..."

            embed = discord.Embed(
                title="📋 الملخص",
                description=summary,
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="📖 النص الأصلي", value=f"عدد الأحرف: {len(text)}", inline=False)
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء التلخيص:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai code - كتابة كود
    @ai_group.command(name="code", description="كتابة كود برمجي")
    @app_commands.describe(
        task="وصف الكود اللي عايزه",
        language="لغة البرمجة (اختياري)"
    )
    @app_commands.choices(language=[
        app_commands.Choice(name="🐍 Python", value="python"),
        app_commands.Choice(name="🌐 JavaScript", value="javascript"),
        app_commands.Choice(name="☕ Java", value="java"),
        app_commands.Choice(name="🎯 C++", value="cpp"),
        app_commands.Choice(name="🦀 Rust", value="rust"),
        app_commands.Choice(name="💎 Ruby", value="ruby"),
        app_commands.Choice(name="🐘 PHP", value="php"),
        app_commands.Choice(name="🔷 TypeScript", value="typescript"),
    ])
    async def ai_code(self, interaction: discord.Interaction, task: str, language: app_commands.Choice[str] = None):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # طلب كتابة الكود
            lang_text = f"بلغة {language.value}" if language else ""
            code_prompt = f"اكتب كود {lang_text} للمهمة التالية:\n\n{task}\n\nالكود فقط مع تعليقات بسيطة، بدون شرح طويل."
            
            response = await asyncio.to_thread(
                model.generate_content,
                code_prompt
            )

            code = response.text

            # استخراج الكود من الرد
            if "```" in code:
                # استخراج الكود بين ```
                parts = code.split("```")
                if len(parts) >= 3:
                    code = parts[1]
                    # إزالة اسم اللغة لو موجود
                    if "\n" in code:
                        code = "\n".join(code.split("\n")[1:])

            if len(code) > 4000:
                code = code[:4000] + "\n... (تم اختصار الكود)"

            embed = discord.Embed(
                title="💻 الكود المولد",
                description=f"```{language.value if language else 'code'}\n{code}\n```",
                color=discord.Color.dark_theme(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="📝 المهمة", value=task[:1024], inline=False)
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء كتابة الكود:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai story - كتابة قصة
    @ai_group.command(name="story", description="كتابة قصة قصيرة")
    @app_commands.describe(
        topic="موضوع القصة",
        style="أسلوب القصة (اختياري)"
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="🎭 درامي", value="درامي"),
        app_commands.Choice(name="😂 كوميدي", value="كوميدي"),
        app_commands.Choice(name="🔮 خيال علمي", value="خيال علمي"),
        app_commands.Choice(name="🧚 خيالي", value="خيالي"),
        app_commands.Choice(name="🔪 رعب", value="رعب"),
        app_commands.Choice(name="💕 رومانسي", value="رومانسي"),
        app_commands.Choice(name="🔍 غموض", value="غموض"),
    ])
    async def ai_story(self, interaction: discord.Interaction, topic: str, style: app_commands.Choice[str] = None):
        if not model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # طلب كتابة القصة
            style_text = f"بأسلوب {style.value}" if style else ""
            story_prompt = f"اكتب قصة قصيرة {style_text} عن: {topic}\n\nالقصة:"
            
            response = await asyncio.to_thread(
                model.generate_content,
                story_prompt
            )

            story = response.text

            if len(story) > 4000:
                story = story[:4000] + "..."

            embed = discord.Embed(
                title="📖 القصة",
                description=story,
                color=discord.Color.dark_purple(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="🎯 الموضوع", value=topic, inline=False)
            if style:
                embed.add_field(name="🎨 الأسلوب", value=style.name, inline=False)
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء كتابة القصة:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    # أمر /ai analyze - تحليل صورة
    @ai_group.command(name="analyze", description="تحليل صورة باستخدام الذكاء الاصطناعي")
    @app_commands.describe(image="الصورة اللي عايز تحللها")
    async def ai_analyze(self, interaction: discord.Interaction, image: discord.Attachment):
        if not vision_model:
            embed = discord.Embed(
                title="❌ خطأ في الإعدادات",
                description="لم يتم إعداد Gemini API Key!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # التحقق من نوع الملف
        if not image.content_type or not image.content_type.startswith('image/'):
            embed = discord.Embed(
                title="❌ ملف غير صالح",
                description="يرجى رفع صورة صحيحة!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # تحميل الصورة
            image_bytes = await image.read()
            
            # تحويل إلى format مناسب لـ Gemini
            image_data = {
                'mime_type': image.content_type,
                'data': image_bytes
            }

            # طلب تحليل الصورة
            analyze_prompt = "حلل الصورة التالية بالتفصيل وصف ما تراه فيها:"
            
            response = await asyncio.to_thread(
                vision_model.generate_content,
                [analyze_prompt, image_data]
            )

            analysis = response.text

            if len(analysis) > 4000:
                analysis = analysis[:4000] + "..."

            embed = discord.Embed(
                title="🔍 تحليل الصورة",
                description=analysis,
                color=discord.Color.teal(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_image(url=image.url)
            embed.set_footer(text=f"طلب بواسطة: {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"حدث خطأ أثناء تحليل الصورة:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

# دالة تحميل الـ Cog للبوت
async def setup(bot):
    await bot.add_cog(AI(bot))