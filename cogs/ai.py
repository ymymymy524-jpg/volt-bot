import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from typing import Optional

# ═══════════════════════════════════════
# 🧠 Google Gemini (اختياري - البوت يشتغل بدونه)
# ═══════════════════════════════════════
model = None
vision_model = None
genai = None

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    import google.generativeai as genai
    
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        vision_model = genai.GenerativeModel('gemini-pro-vision')
        print("✅ [AI] Google Gemini متصل")
    else:
        print("⚠️ [AI] GEMINI_API_KEY مش موجود — أوامر AI معطلة")
        
except ImportError as e:
    print(f"⚠️ [AI] google.generativeai مش متثبت: {e}")
    print("⚠️ [AI] أوامر AI مش هتشتغل — بس البوت هيشتغل عادي")
    
except Exception as e:
    print(f"⚠️ [AI] فشل تهيئة Gemini: {e}")


class AI(commands.Cog):
    """🧠 أوامر الذكاء الاصطناعي"""

    def __init__(self, bot):
        self.bot = bot

    # ═══════════════════════════════════════
    # 🤖 TEXT COMMANDS (Prefix)
    # ═══════════════════════════════════════

    @commands.command(
        name="ask",
        aliases=["اسأل", "سؤال"],
        description="🤖 اسأل الذكاء الاصطناعي أي سؤال"
    )
    async def ask(self, ctx: commands.Context, *, question: str):
        """اسأل الذكاء الاصطناعي"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                response = await asyncio.to_thread(
                    model.generate_content, question
                )
                embed = discord.Embed(
                    title="🤖 إجابة الذكاء الاصطناعي",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0x9B59B6
                )
                embed.set_footer(
                    text=f"سؤال: {question[:50]}...",
                    icon_url=ctx.author.display_avatar.url
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="imagine",
        aliases=["تخيل"],
        description="🎨 توليد وصف أو فكرة"
    )
    async def imagine(self, ctx: commands.Context, *, prompt: str):
        """توليد وصف أو فكرة"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                full_prompt = f"اكتب وصف تفصيلي ومبدع للفكرة دي: {prompt}"
                response = await asyncio.to_thread(
                    model.generate_content, full_prompt
                )
                embed = discord.Embed(
                    title="🎨 تخيل إبداعي",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0xE91E63
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="translate",
        aliases=["ترجم"],
        description="🌐 ترجمة النصوص"
    )
    async def translate(self, ctx: commands.Context, *, text: str):
        """ترجمة النصوص"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                prompt = f"ترجم النص ده للإنجليزية (أو للعربية لو إنجليزي):\n\n{text}"
                response = await asyncio.to_thread(
                    model.generate_content, prompt
                )
                embed = discord.Embed(
                    title="🌐 ترجمة",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0x3498DB
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="summarize",
        aliases=["لخص"],
        description="📝 تلخيص النصوص الطويلة"
    )
    async def summarize(self, ctx: commands.Context, *, text: str):
        """تلخيص النصوص"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                prompt = f"لخص النص ده في نقاط مختصرة:\n\n{text}"
                response = await asyncio.to_thread(
                    model.generate_content, prompt
                )
                embed = discord.Embed(
                    title="📝 ملخص",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0x2ECC71
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="code",
        aliases=["كود"],
        description="💻 مساعدة في كتابة الكود"
    )
    async def code(self, ctx: commands.Context, *, request: str):
        """مساعدة في الكود"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                prompt = f"ساعدني في الكود ده أو اكتب كود لـ: {request}"
                response = await asyncio.to_thread(
                    model.generate_content, prompt
                )
                text = response.text[:4000] if response.text else "مفيش إجابة"
                embed = discord.Embed(
                    title="💻 مساعدة في الكود",
                    description=text,
                    color=0x2C3E50
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="story",
        aliases=["قصة"],
        description="📖 كتابة قصة قصيرة"
    )
    async def story(self, ctx: commands.Context, *, topic: str):
        """كتابة قصة"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                prompt = f"اكتب قصة قصيرة وممتعة عن: {topic}"
                response = await asyncio.to_thread(
                    model.generate_content, prompt
                )
                embed = discord.Embed(
                    title=f"📖 قصة عن {topic}",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0x9B59B6
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")

    @commands.command(
        name="analyze",
        aliases=["حلل"],
        description="🔍 تحليل النصوص"
    )
    async def analyze(self, ctx: commands.Context, *, text: str):
        """تحليل النص"""
        if not model:
            await ctx.send("❌ خدمة الذكاء الاصطناعي غير متاحة حالياً!")
            return

        async with ctx.typing():
            try:
                prompt = f"حلل النص ده وأعطني رأيك فيه:\n\n{text}"
                response = await asyncio.to_thread(
                    model.generate_content, prompt
                )
                embed = discord.Embed(
                    title="🔍 تحليل",
                    description=response.text[:4000] if response.text else "مفيش إجابة",
                    color=0xE67E22
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"❌ حصل خطأ: {str(e)[:200]}")


async def setup(bot):
    await bot.add_cog(AI(bot))