import os
import asyncio
import random
import datetime
import io
import aiohttp
import discord
from discord.ext import commands
from google import genai
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ==================== 1. SECURITY & CONFIG ====================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AUTO_LOFI_VC_ID = os.getenv("LOFI_VC_ID")  # Voice Channel ID for 24/7 Lofi

# Initialize Official Gemini Client with correct model support
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# In-Memory Databases
user_balances = {}      # {user_id: balance}
user_inventories = {}   # {user_id: [item_names]}
protected_users = set() # {user_id}
daily_claimed = {}      # {user_id_or_key: date}
user_xp = {}            # {user_id: xp}
user_level = {}         # {user_id: level}
work_cooldowns = {}     # {user_id: datetime}

BANNED_WORDS = ["badword1", "badword2", "spamlink.com"]

# Shop Items Definition
SHOP_ITEMS = {
    "chicken": {"cost": 200, "type": "food", "name": "🍗 Chicken"},
    "pizza": {"cost": 500, "type": "food", "name": "🍕 Pizza"},
    "book": {"cost": 1000, "type": "item", "name": "📚 Book"},
    "protection": {"cost": 10000, "type": "shield", "name": "🛡️ Protection Shield"},
    "conqueror": {"cost": 99999, "type": "role", "name": "CONQUEROR"}
}

# Quiz Questions Database
QUIZ_QUESTIONS = [
    {"q": "What is the capital of Bangladesh?", "a": "dhaka"},
    {"q": "Which programming language is this bot written in?", "a": "python"},
    {"q": "How many planet(s) are there in our Solar System?", "a": "8"},
    {"q": "What is 15 + 27?", "a": "42"},
    {"q": "Which gas do plants absorb from the atmosphere?", "a": "carbon dioxide"},
    {"q": "What is the largest ocean on Earth?", "a": "pacific"}
]

# 20 Varied Work Scenarios
WORK_SCENARIOS = [
    ("You found a lost coin on the street while walking!", 25),
    ("You sold a used plastic bottle to a local collector!", 35),
    ("You helped an old man cross the busy road!", 40),
    ("You swept the floor of the local tea shop for a quick tip!", 45),
    ("You answered a simple survey online!", 50),
    ("You won an intense Rock-Paper-Scissors match against a stranger!", 65),
    ("You helped an admin clean spam messages from the Discord channel!", 80),
    ("You solved a quick trivia question before anyone else!", 100),
    ("You convinced someone that 'Lofi music improves sleep by 99%'!", 120),
    ("You worked a short evening shift at the local Lofi Tea Stall!", 140),
    ("You hacked your neighbor's WiFi and sold the password to a friend!", 150),
    ("You created a legendary slap meme that went viral on the server!", 160),
    ("You posted top-tier memes on Discord and people tipped you nicely!", 200),
    ("You caught a sneaky robber red-handed and received a police bounty!", 220),
    ("You won a local gaming tournament in your city!", 250),
    ("You sold a fake 'Level 100 Discord VIP Badge' to a rookie!", 300),
    ("You fixed a critical bug in a server bot and got paid by the owner!", 350),
    ("You successfully hosted a mini Discord giveaway event!", 400),
    ("You designed a custom avatar meme for a popular streamer!", 450),
    ("You found a rare digital collectible and sold it on the market!", 500)
]

LOFI_STREAM_URL = "https://stream.zeno.fm/f3wvbbqmdg8uv"

# ==================== 2. BOT EVENTS ====================
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online and fully active!')
    await bot.change_presence(activity=discord.Game(name="!help | AI Chat | Games | 24/7 Lofi"))
    
    # Auto-Join 24/7 Lofi Voice Channel
    if AUTO_LOFI_VC_ID:
        try:
            vc_channel = bot.get_channel(int(AUTO_LOFI_VC_ID))
            if vc_channel and isinstance(vc_channel, discord.VoiceChannel):
                vc = await vc_channel.connect()
                ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                vc.play(discord.FFmpegPCMAudio(LOFI_STREAM_URL, **ffmpeg_opts))
                print(f"🎵 Connected to {vc_channel.name} and playing Lofi!")
        except Exception as err:
            print(f"⚠️ Auto-Lofi Error: {err}")

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        embed = discord.Embed(
            title="🎉 Welcome to the Server!",
            description=f"Welcome {member.mention}! Have fun chatting, playing games, and earning points!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Auto-Moderation
    msg_lower = message.content.lower()
    if any(word in msg_lower for word in BANNED_WORDS):
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}, bad words/links are not allowed!", delete_after=5)
        return

    # Leveling System
    uid = message.author.id
    current_xp = user_xp.get(uid, 0) + random.randint(15, 25)
    current_lvl = user_level.get(uid, 1)
    
    if current_xp >= current_lvl * 100:
        current_lvl += 1
        current_xp = 0
        user_level[uid] = current_lvl
        user_balances[uid] = user_balances.get(uid, 100) + 100
        await message.channel.send(f"🎉 **LEVEL UP!** {message.author.mention} reached **Level {current_lvl}** and earned **100** coins reward! 🌟")
    
    user_xp[uid] = current_xp
    user_level[uid] = current_lvl

    # Gemini AI Integration (Using Gemini 3.8 Flash model[cite: 1])
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            try:
                user_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip() or "Hello!"

                response = await asyncio.to_thread(
                    gemini_client.models.generate_content,
                    model='gemini-3.8-flash',
                    contents=user_prompt
                )

                if response and response.text:
                    output = response.text
                    if len(output) > 2000:
                        for chunk in [output[i:i+1900] for i in range(0, len(output), 1900)]:
                            await message.reply(chunk)
                    else:
                        await message.reply(output)
                else:
                    await message.reply("I couldn't generate a response. Please try again.")
            except Exception as e:
                print(f"❌ GEMINI API ERROR: {e}")
                await message.reply(f"Sorry, I encountered an error: {e}")

    await bot.process_commands(message)

# ==================== 3. TRANSLATION SYSTEM ====================
@bot.command(aliases=["tr"])
async def translate(ctx, target_lang: str, *, text: str = None):
    """Translate text or replied message (!tr bn How are you / reply with !tr en)"""
    if ctx.message.reference and not text:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = replied_msg.content

    if not text:
        await ctx.send("❌ Please provide text to translate or reply to a message!\nExample: `!tr bangla How are you?` or reply with `!tr english`")
        return

    async with ctx.typing():
        try:
            prompt = f"Translate the following text accurately into {target_lang}. Return ONLY the translated text without extra explanation:\n\n{text}"
            response = await asyncio.to_thread(
                gemini_client.models.generate_content,
                model='gemini-3.8-flash',
                contents=prompt
            )

            if response and response.text:
                embed = discord.Embed(
                    title=f"🌐 Translation to {target_lang.title()}",
                    description=response.text,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Could not translate text.")
        except Exception as e:
            await ctx.send(f"❌ Translation Error: {e}")

# ==================== 4. ECONOMY, WORK & SHOP ====================
@bot.command()
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    bal = user_balances.get(user.id, 100)
    user_balances[user.id] = bal
    await ctx.send(f"💰 {user.mention} has **{bal}** points/coins!")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    today = datetime.date.today()
    if daily_claimed.get(f"daily_{user_id}") == today:
        await ctx.send(f"⏳ {ctx.author.mention}, you already claimed your daily reward today!")
        return
    daily_claimed[f"daily_{user_id}"] = today
    user_balances[user_id] = user_balances.get(user_id, 100) + 200
    await ctx.send(f"🎁 {ctx.author.mention}, you claimed **200** daily points! Total: **{user_balances[user_id]}**")

@bot.command()
async def collect(ctx):
    """Claim role-based daily points"""
    user_id = ctx.author.id
    today = datetime.date.today()
    collect_key = f"collect_{user_id}"
    
    if daily_claimed.get(collect_key) == today:
        await ctx.send(f"⏳ {ctx.author.mention}, you have already claimed your `!collect` reward today!")
        return

    points_awarded = 500
    role_title = "Member"

    if ctx.author.guild_permissions.administrator or any(role.name.lower() in ["supreme leader", "admin", "owner"] for role in ctx.author.roles):
        points_awarded = 5000
        role_title = "Supreme Leader / Admin"
    elif ctx.author.guild_permissions.manage_messages or any(role.name.lower() in ["moderator", "mod"] for role in ctx.author.roles):
        points_awarded = 1000
        role_title = "Moderator"

    daily_claimed[collect_key] = today
    user_balances[user_id] = user_balances.get(user_id, 100) + points_awarded

    embed = discord.Embed(
        title="🎁 Daily Collection Claimed!",
        description=f"{ctx.author.mention} ({role_title}) collected **{points_awarded}** points today!\n💰 Total: `{user_balances[user_id]}` points.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    """Do funny work to earn points (Cooldown: 1 hour)"""
    user_id = ctx.author.id
    now = datetime.datetime.now()

    if user_id in work_cooldowns:
        last_work = work_cooldowns[user_id]
        time_diff = (now - last_work).total_seconds()
        if time_diff < 3600:
            remaining_mins = int((3600 - time_diff) // 60)
            await ctx.send(f"⏳ {ctx.author.mention}, you are tired! Please wait **{remaining_mins} minutes** before working again.")
            return

    scenario, earned_points = random.choice(WORK_SCENARIOS)
    user_balances[user_id] = user_balances.get(user_id, 100) + earned_points
    work_cooldowns[user_id] = now

    embed = discord.Embed(
        title="💼 Work Done!",
        description=f"{ctx.author.mention}, {scenario}\n\n💰 **Earned:** `{earned_points}` points!\nTotal Balance: `{user_balances[user_id]}` points.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    sender_id, receiver_id = ctx.author.id, member.id
    if sender_id == receiver_id or amount <= 0:
        await ctx.send("❌ Invalid transfer!")
        return

    sender_bal = user_balances.get(sender_id, 100)
    if sender_bal < amount:
        await ctx.send(f"❌ Not enough coins! Balance: **{sender_bal}**")
        return

    user_balances[sender_id] -= amount
    user_balances[receiver_id] = user_balances.get(receiver_id, 100) + amount
    await ctx.send(f"💸 {ctx.author.mention} transferred **{amount}** coins to {member.mention}!")

@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🛒 Server Point Shop", color=discord.Color.purple())
    desc = "".join([f"🔹 **{details['name']}** — Price: `{details['cost']} points`\n" for details in SHOP_ITEMS.values()])
    embed.description = desc
    embed.set_footer(text="Use !buy <item_name> to purchase! (e.g., !buy chicken)")
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, item_name: str):
    item_key = item_name.lower()
    user_id = ctx.author.id
    if item_key not in SHOP_ITEMS:
        await ctx.send("❌ Item not found in shop!")
        return

    item = SHOP_ITEMS[item_key]
    cost = item["cost"]
    bal = user_balances.get(user_id, 100)

    if bal < cost:
        await ctx.send(f"❌ Not enough points! Balance: **{bal}**, Needed: **{cost}**")
        return

    user_balances[user_id] = bal - cost
    if user_id not in user_inventories:
        user_inventories[user_id] = []

    if item["type"] == "role":
        role = discord.utils.get(ctx.guild.roles, name=item["name"])
        if role:
            try:
                await ctx.author.add_roles(role)
                await ctx.send(f"👑 CONGRATULATIONS {ctx.author.mention}! You bought **{item['name']}** role!")
            except Exception:
                await ctx.send("🎉 Bought role, but bot lacks permissions to assign it!")
        else:
            await ctx.send(f"🎉 Spent **{cost}** points for **{item['name']}**! (Admin needs to create the role).")
    elif item["type"] == "shield":
        protected_users.add(user_id)
        user_inventories[user_id].append(item["name"])
        await ctx.send(f"🛡️ {ctx.author.mention}, Protection Shield active!")
    else:
        user_inventories[user_id].append(item["name"])
        await ctx.send(f"🛍️ {ctx.author.mention}, bought **{item['name']}**!")

@bot.command(aliases=["inv"])
async def inventory(ctx, member: discord.Member = None):
    user = member or ctx.author
    items = user_inventories.get(user.id, [])
    if not items:
        await ctx.send(f"🎒 {user.mention}'s inventory is empty!")
        return
    desc = "\n".join([f"• {it}" for it in set(items)])
    embed = discord.Embed(title=f"🎒 {user.name}'s Inventory", description=desc, color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def rob(ctx, member: discord.Member):
    robber_id, victim_id = ctx.author.id, member.id
    if robber_id == victim_id:
        await ctx.send("❌ You cannot rob yourself!")
        return

    if victim_id in protected_users:
        protected_users.remove(victim_id)
        await ctx.send(f"🛡️ **ROB FAILED!** {member.mention}'s Protection Shield absorbed the attack and broke!")
        return

    victim_bal = user_balances.get(victim_id, 100)
    robber_bal = user_balances.get(robber_id, 100)
    if victim_bal < 50:
        await ctx.send(f"❌ {member.mention} has less than 50 points.")
        return

    if random.choice([True, False]):
        stolen = random.randint(20, int(victim_bal * 0.4))
        user_balances[victim_id] -= stolen
        user_balances[robber_id] = robber_bal + stolen
        await ctx.send(f"🥷 **SUCCESS!** {ctx.author.mention} stole **{stolen}** points from {member.mention}!")
    else:
        fine = random.randint(30, 100)
        user_balances[robber_id] = max(0, robber_bal - fine)
        await ctx.send(f"🚨 **CAUGHT!** {ctx.author.mention} failed and was fined **{fine}** points!")

@bot.command(aliases=["lb"])
async def leaderboard(ctx):
    if not user_balances:
        await ctx.send("📊 Leaderboard is empty!")
        return
    sorted_u = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "\n".join([f"**#{i+1}** <@{uid}> — `{bal}` coins" for i, (uid, bal) in enumerate(sorted_u)])
    embed = discord.Embed(title="🏆 Top Richest Members", description=desc, color=discord.Color.gold())
    await ctx.send(embed=embed)

# ==================== 5. GAMES & MEMES ====================
@bot.command()
async def quiz(ctx):
    quiz_item = random.choice(QUIZ_QUESTIONS)
    question, correct_answer = quiz_item["q"], quiz_item["a"]

    embed = discord.Embed(
        title="🧠 Quick Quiz!",
        description=f"**{question}**\n\n⏱️ You have **15 seconds** to answer in chat!",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

    def check(m):
        return m.channel == ctx.channel and not m.author.bot

    try:
        while True:
            msg = await bot.wait_for("message", check=check, timeout=15.0)
            if msg.content.strip().lower() == correct_answer:
                user_id = msg.author.id
                user_balances[user_id] = user_balances.get(user_id, 100) + 50
                await ctx.send(f"🎉 Correct Answer {msg.author.mention}! The answer was **{correct_answer.title()}**. You won **50** coins! 💰")
                return
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Time's up! The correct answer was: **{correct_answer.title()}**")

@bot.command()
async def blackjack(ctx, bet: int):
    user_id = ctx.author.id
    bal = user_balances.get(user_id, 100)
    if bet <= 0 or bet > bal:
        await ctx.send("❌ Invalid bet!")
        return

    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
    u_cards, b_cards = [random.choice(cards), random.choice(cards)], [random.choice(cards), random.choice(cards)]
    u_score, b_score = sum(u_cards), sum(b_cards)

    while b_score < 17:
        b_cards.append(random.choice(cards))
        b_score = sum(b_cards)

    msg = f"🃏 **Blackjack** | You: `{u_cards}` ({u_score}) VS Bot: `{b_cards}` ({b_score})\n"
    if u_score > 21:
        user_balances[user_id] -= bet
        msg += f"💥 Bust! Lost **{bet}** coins."
    elif b_score > 21 or u_score > b_score:
        user_balances[user_id] += bet
        msg += f"🎉 Won **{bet}** coins!"
    elif u_score < b_score:
        user_balances[user_id] -= bet
        msg += f"📉 Lost **{bet}** coins."
    else:
        msg += "🤝 Push! Tie game."
    await ctx.send(msg)

@bot.command()
async def roll(ctx):
    await ctx.send(f"🎲 {ctx.author.mention} rolled a **{random.randint(1, 6)}**!")

@bot.command()
async def coinflip(ctx):
    await ctx.send(f"🪙 Result: **{random.choice(['Heads 🪙', 'Tails 🪙'])}**")

@bot.command()
async def slap(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("❌ You cannot slap yourself!")
        return

    await ctx.typing()
    try:
        author_url, target_url = ctx.author.display_avatar.url, member.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(author_url) as r1, session.get(target_url) as r2:
                author_bytes, target_bytes = await r1.read(), await r2.read()

        author_img = Image.open(io.BytesIO(author_bytes)).convert("RGBA").resize((110, 110))
        target_img = Image.open(io.BytesIO(target_bytes)).convert("RGBA").resize((90, 90))

        mask_a = Image.new("L", (110, 110), 0)
        ImageDraw.Draw(mask_a).ellipse((0, 0, 110, 110), fill=255)
        author_circular = ImageOps.fit(author_img, mask_a.size, centering=(0.5, 0.5))
        author_circular.putalpha(mask_a)

        mask_t = Image.new("L", (90, 90), 0)
        ImageDraw.Draw(mask_t).ellipse((0, 0, 90, 90), fill=255)
        target_circular = ImageOps.fit(target_img, mask_t.size, centering=(0.5, 0.5))
        target_circular.putalpha(mask_t)

        base = Image.new("RGB", (600, 380), color=(230, 230, 230))
        ImageDraw.Draw(base).text((20, 20), f"SLAP! {ctx.author.name} ---> {member.name}", fill=(200, 0, 0))

        base.paste(author_circular, (130, 90), author_circular)
        base.paste(target_circular, (360, 200), target_circular)

        out = io.BytesIO()
        base.save(out, format="PNG")
        out.seek(0)
        await ctx.send(f"💥 {ctx.author.mention} slapped {member.mention}!", file=discord.File(out, filename="slap.png"))
    except Exception as e:
        await ctx.send(f"❌ Slap meme error: {e}")

@bot.command()
async def meme(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://meme-api.com/gimme") as resp:
            if resp.status == 200:
                data = await resp.json()
                embed = discord.Embed(title=data["title"], color=discord.Color.random())
                embed.set_image(url=data["url"])
                await ctx.send(embed=embed)

@bot.command()
async def creatememe(ctx, *, text: str):
    parts = text.split("|")
    top_text = parts[0].strip().upper()
    bottom_text = parts[1].strip().upper() if len(parts) > 1 else ""

    img = Image.new('RGB', (600, 350), color=(50, 50, 50))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((20, 20), top_text, fill=(255, 255, 255), font=font)
    if bottom_text:
        draw.text((20, 280), bottom_text, fill=(255, 255, 255), font=font)

    arr = io.BytesIO()
    img.save(arr, format='PNG')
    arr.seek(0)
    await ctx.send(file=discord.File(arr, filename='meme.png'))

# ==================== 6. RANK, UTILITIES & MODERATION ====================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    user = member or ctx.author
    lvl = user_level.get(user.id, 1)
    xp = user_xp.get(user.id, 0)
    embed = discord.Embed(title=f"📊 {user.name}'s Rank", color=discord.Color.blue())
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Level", value=f"⭐ `{lvl}`", inline=True)
    embed.add_field(name="XP Progress", value=f"📈 `{xp}/{lvl*100}` XP", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, *, question: str):
    embed = discord.Embed(title="📊 Community Poll", description=question, color=discord.Color.gold())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, time_sec: int, *, prize: str):
    embed = discord.Embed(title="🎉 GIVEAWAY!", description=f"**Prize:** {prize}\nReact with 🎉 to enter!", color=discord.Color.purple())
    gmsg = await ctx.send(embed=embed)
    await gmsg.add_reaction("🎉")

    await asyncio.sleep(time_sec)
    new_msg = await ctx.channel.fetch_message(gmsg.id)
    users = [u async for r in new_msg.reactions if str(r.emoji) == "🎉" for u in r.users() if not u.bot]

    if users:
        await ctx.send(f"🎊 Winner of **{prize}**: {random.choice(users).mention}!")
    else:
        await ctx.send("❌ No valid entrants for the giveaway.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'👢 {member.mention} kicked.')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'🔨 {member.mention} banned.')

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'🧹 {amount} messages cleared!', delete_after=3)

# ==================== 7. RUN BOT ====================
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN environment variable is missing!")