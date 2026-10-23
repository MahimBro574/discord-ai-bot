import os
import asyncio
import random
import datetime
import io
import urllib.parse
import aiohttp
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ==================== 1. RENDER PORT TIMEOUT FIX ====================
app = Flask('')

@app.route('/')
def home():
    return "MU Bot is active 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ==================== 2. SECURITY & CONFIG ====================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AUTO_LOFI_VC_ID = os.getenv("LOFI_VC_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# In-Memory Databases
user_balances = {}      
user_inventories = {}   
protected_users = set() 
daily_claimed = {}      
user_xp = {}            
user_level = {}         
work_cooldowns = {}     

BANNED_WORDS = [
    "badword1", "badword2", "spamlink.com", "sex", "porno", "nude",
    "gali1", "gali2", "fuck", "bitch", "bastard", "slut"
]

SHOP_ITEMS = {
    "chicken": {"cost": 200, "type": "food", "name": "🍗 Chicken"},
    "pizza": {"cost": 500, "type": "food", "name": "🍕 Pizza"},
    "book": {"cost": 1000, "type": "item", "name": "📚 Book"},
    "protection": {"cost": 10000, "type": "shield", "name": "🛡️ Protection Shield"},
    "conqueror": {"cost": 99999, "type": "role", "name": "CONQUEROR"}
}

# 100+ General Knowledge Quiz Questions
QUIZ_QUESTIONS = [
    {"q": "What is the capital of Bangladesh?", "a": "dhaka"},
    {"q": "Which programming language is this bot written in?", "a": "python"},
    {"q": "How many planet(s) are there in our Solar System?", "a": "8"},
    {"q": "What is 15 + 27?", "a": "42"},
    {"q": "Which gas do plants absorb from the atmosphere?", "a": "carbon dioxide"},
    {"q": "What is the largest ocean on Earth?", "a": "pacific"},
    {"q": "Who wrote 'Gitanjali'?", "a": "rabindranath tagore"},
    {"q": "Which currency is used in Japan?", "a": "yen"},
    {"q": "What is the national sport of Bangladesh?", "a": "kabaddi"},
    {"q": "What is the chemical symbol for Gold?", "a": "au"},
    {"q": "How many colors are in a rainbow?", "a": "7"},
    {"q": "Which planet is known as the Red Planet?", "a": "mars"},
    {"q": "What is the hardest natural substance on Earth?", "a": "diamond"},
    {"q": "What is 100 divided by 4?", "a": "25"},
    {"q": "Who is the founder of Microsoft?", "a": "bill gates"},
    {"q": "What is the national flower of Bangladesh?", "a": "water lily"},
    {"q": "Which organ pumps blood in the human body?", "a": "heart"},
    {"q": "What is the capital of France?", "a": "paris"},
    {"q": "What is the boiling point of water in Celsius?", "a": "100"},
    {"q": "Which continent is Bangladesh located in?", "a": "asia"},
    {"q": "What is the longest river in Bangladesh?", "a": "surma"},
    {"q": "Who painted the Mona Lisa?", "a": "leonardo da vinci"},
    {"q": "What is the chemical symbol for Water?", "a": "h2o"},
    {"q": "How many days are in a leap year?", "a": "366"},
    {"q": "Which animal is known as the Ship of the Desert?", "a": "camel"},
    {"q": "Who discovered gravity?", "a": "isaac newton"},
    {"q": "What is the currency of the UK?", "a": "pound"},
    {"q": "What is the capital of USA?", "a": "washington dc"},
    {"q": "How many sides does a triangle have?", "a": "3"},
    {"q": "Which gas do humans breathe in to survive?", "a": "oxygen"},
    {"q": "What is the chemical symbol for Iron?", "a": "fe"},
    {"q": "Which element has the symbol 'O'?", "a": "oxygen"},
    {"q": "What is 12 multiplied by 12?", "a": "144"},
    {"q": "What is the speed of light in vacuum (approx km/s)?", "a": "300000"},
    {"q": "Which bird is the national bird of Bangladesh?", "a": "magpie robin"},
    {"q": "What is the largest planet in our solar system?", "a": "jupiter"},
    {"q": "What is the smallest prime number?", "a": "2"},
    {"q": "Who invented the telephone?", "a": "alexander graham bell"},
    {"q": "What is the capital of India?", "a": "new delhi"},
    {"q": "What is the capital of Canada?", "a": "ottawa"},
    {"q": "Which country is called the Land of Rising Sun?", "a": "japan"},
    {"q": "What is the freeze point of water in Celsius?", "a": "0"},
    {"q": "How many letters are in the English alphabet?", "a": "26"},
    {"q": "Which animal is the largest mammal in the world?", "a": "blue whale"},
    {"q": "What is 50 percent of 200?", "a": "100"},
    {"q": "Which continent is known as Dark Continent?", "a": "africa"},
    {"q": "Who is known as Father of Computer?", "a": "charles babbage"},
    {"q": "What is the chemical symbol for Silver?", "a": "ag"},
    {"q": "What is the largest desert in the world?", "a": "antarctica"},
    {"q": "What is the national fruit of Bangladesh?", "a": "jackfruit"},
    {"q": "What is 9 squared?", "a": "81"},
    {"q": "Which planet is closest to the Sun?", "a": "mercury"},
    {"q": "What is the capital of Australia?", "a": "canberra"},
    {"q": "What is the capital of Germany?", "a": "berlin"},
    {"q": "Who wrote 'Romeo and Juliet'?", "a": "william shakespeare"},
    {"q": "Which metal is liquid at room temperature?", "a": "mercury"},
    {"q": "What is the national fish of Bangladesh?", "a": "hilsha"},
    {"q": "How many bones are in the adult human body?", "a": "206"},
    {"q": "What is 7 multiplied by 8?", "a": "56"},
    {"q": "Which planet has famous rings around it?", "a": "saturn"},
    {"q": "Who was the first person to walk on the Moon?", "a": "neil armstrong"},
    {"q": "What is the currency of USA?", "a": "dollar"},
    {"q": "What is the capital of Italy?", "a": "rome"},
    {"q": "What is the main component of sun?", "a": "hydrogen"},
    {"q": "How many players are on a soccer team on field?", "a": "11"},
    {"q": "What is 250 - 85?", "a": "165"},
    {"q": "Which country won the First World Cup in Cricket in 1975?", "a": "west indies"},
    {"q": "What is the chemical symbol for Sodium?", "a": "na"},
    {"q": "What is the chemical symbol for Potassium?", "a": "k"},
    {"q": "How many continents are on Earth?", "a": "7"},
    {"q": "What is the capital of Saudi Arabia?", "a": "riyadh"},
    {"q": "Who painted 'The Starry Night'?", "a": "vincent van gogh"},
    {"q": "Which gas causes global warming?", "a": "carbon dioxide"},
    {"q": "What is the capital of Russia?", "a": "moscow"},
    {"q": "What is 10 to the power of 3?", "a": "1000"},
    {"q": "What is the national tree of Bangladesh?", "a": "mango tree"},
    {"q": "Which organ in human body purifies blood?", "a": "kidney"},
    {"q": "What is the capital of Spain?", "a": "madrid"},
    {"q": "How many teeth does a human adult normally have?", "a": "32"},
    {"q": "What is 11 times 11?", "a": "121"},
    {"q": "Which instrument measures temperature?", "a": "thermometer"},
    {"q": "What is the capital of Turkey?", "a": "ankara"},
    {"q": "What is the currency of China?", "a": "yuan"},
    {"q": "Which blood group is universal donor?", "a": "o negative"},
    {"q": "What is the capital of Egypt?", "a": "cairo"},
    {"q": "How many rings are on the Olympic flag?", "a": "5"},
    {"q": "What is 60 divided by 5?", "a": "12"},
    {"q": "Which gas is used in fire extinguishers?", "a": "carbon dioxide"},
    {"q": "Who invented the light bulb?", "a": "thomas edison"},
    {"q": "What is the capital of Nepal?", "a": "kathmandu"},
    {"q": "What is the capital of South Korea?", "a": "seoul"},
    {"q": "Which country invented paper?", "a": "china"},
    {"q": "What is the square root of 64?", "a": "8"},
    {"q": "What is the capital of Thailand?", "a": "bangkok"},
    {"q": "Which planet is known as Earth's twin?", "a": "venus"},
    {"q": "What is the capital of Malaysia?", "a": "kuala lumpur"},
    {"q": "What is 5 cubed (5*5*5)?", "a": "125"},
    {"q": "What is the currency of Europe union?", "a": "euro"},
    {"q": "What is the capital of Argentina?", "a": "buenos aires"},
    {"q": "What is the national animal of Bangladesh?", "a": "royal bengal tiger"},
    {"q": "What is 1000 minus 333?", "a": "667"}
]

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

# ==================== 3. BOT EVENTS ====================
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online and fully active!')
    await bot.change_presence(activity=discord.Game(name="!help | MU Homie AI | Games | 24/7 Lofi"))
    
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

    msg_lower = message.content.lower()

    # Moderation Check
    if any(word in msg_lower for word in BANNED_WORDS):
        try:
            await message.delete()
        except Exception:
            pass
        await message.channel.send(f"{message.author.mention} Ei cilo tomar mone / chi chi tumi ato kharap 🙈")
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

    # Homies Banglish AI Chat Integration
    if (bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)) and not message.content.startswith("!"):
        async with message.channel.typing():
            try:
                user_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip() or "Ki obostha bro?"
                
                if any(bad in user_prompt.lower() for bad in ["sex", "nude", "porno", "gali", "fuck", "bitch"]):
                    await message.reply("Ei cilo tomar mone / chi chi tumi ato kharap 🙈")
                    return

                system_prompt = (
                    "You are MU Bot, a cool Discord homie speaking Banglish (Bengali written in English letters). "
                    "Talk casually like a close friend/bro. Keep responses short, funny, and engaging. "
                    "If someone asks inappropriate things, answer: 'Ei cilo tomar mone / chi chi tumi ato kharap 🙈'."
                )
                
                full_query = f"{system_prompt}\nUser says: {user_prompt}"
                encoded_text = urllib.parse.quote(full_query)
                url = f"https://text.pollinations.ai/{encoded_text}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            output = await response.text()
                            if len(output) > 2000:
                                for chunk in [output[i:i+1900] for i in range(0, len(output), 1900)]:
                                    await message.reply(chunk)
                            else:
                                await message.reply(output)
                        else:
                            await message.reply("Arey bro, server-a ektu chap, abar bol toh!")
            except Exception as e:
                print(f"❌ AI ERROR: {e}")
                await message.reply("Arey chill bro, ektu problem hoise. Abar bol!")

    await bot.process_commands(message)

# ==================== 4. TRANSLATION SYSTEM ====================
@bot.command(aliases=["tr"])
async def translate(ctx, target_lang: str, *, text: str = None):
    if ctx.message.reference and not text:
        replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        text = replied_msg.content

    if not text:
        await ctx.send("❌ Please provide text to translate or reply to a message!")
        return

    async with ctx.typing():
        try:
            prompt = f"Translate the following text accurately into {target_lang}. Return ONLY the translated text: {text}"
            encoded_text = urllib.parse.quote(prompt)
            url = f"https://text.pollinations.ai/{encoded_text}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        translated_text = await response.text()
                        embed = discord.Embed(title=f"🌐 Translation to {target_lang.title()}", description=translated_text, color=discord.Color.blue())
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Could not translate text.")
        except Exception as e:
            await ctx.send(f"❌ Translation Error: {e}")

# ==================== 5. ECONOMY, WORK, GAMES & SHOP ====================
@bot.command()
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    bal = user_balances.get(user.id, 100)
    user_balances[user.id] = bal
    await ctx.send(f"💰 {user.mention} has **{bal}** coins!")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    today = datetime.date.today()
    if daily_claimed.get(f"daily_{user_id}") == today:
        await ctx.send(f"⏳ {ctx.author.mention}, you already claimed your daily reward today!")
        return
    daily_claimed[f"daily_{user_id}"] = today
    user_balances[user_id] = user_balances.get(user_id, 100) + 200
    await ctx.send(f"🎁 {ctx.author.mention}, you claimed **200** daily points!")

@bot.command()
async def work(ctx):
    user_id = ctx.author.id
    now = datetime.datetime.now()

    if user_id in work_cooldowns:
        last_work = work_cooldowns[user_id]
        time_diff = (now - last_work).total_seconds()
        if time_diff < 3600:
            remaining_mins = int((3600 - time_diff) // 60)
            await ctx.send(f"⏳ {ctx.author.mention}, please wait **{remaining_mins} minutes** before working again.")
            return

    scenario, earned_points = random.choice(WORK_SCENARIOS)
    user_balances[user_id] = user_balances.get(user_id, 100) + earned_points
    work_cooldowns[user_id] = now

    embed = discord.Embed(title="💼 Work Done!", description=f"{ctx.author.mention}, {scenario}\n\n💰 **Earned:** `{earned_points}` points!", color=discord.Color.green())
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
async def imagine(ctx, *, prompt: str):
    """Generate AI Images using Pollinations AI"""
    async with ctx.typing():
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        embed = discord.Embed(title=f"🎨 Prompt: {prompt}", color=discord.Color.purple())
        embed.set_image(url=image_url)
        await ctx.reply(embed=embed)

@bot.command()
async def slap(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("❌ You cannot slap yourself!")
        return

    await ctx.typing()
    try:
        author_url = ctx.author.display_avatar.url
        target_url = member.display_avatar.url

        async with aiohttp.ClientSession() as session:
            async with session.get(author_url) as r1, session.get(target_url) as r2:
                author_bytes = await r1.read()
                target_bytes = await r2.read()

        author_img = Image.open(io.BytesIO(author_bytes)).convert("RGBA").resize((110, 110))
        target_img = Image.open(io.BytesIO(target_bytes)).convert("RGBA").resize((90, 90))

        base = Image.new("RGBA", (600, 380), color=(230, 230, 230, 255))
        draw = ImageDraw.Draw(base)
        draw.text((20, 20), f"SLAP! {ctx.author.name} ---> {member.name}", fill=(200, 0, 0, 255))
        
        base.paste(author_img, (130, 90), author_img)
        base.paste(target_img, (360, 200), target_img)

        out = io.BytesIO()
        base.save(out, format="PNG")
        out.seek(0)
        await ctx.send(f"💥 {ctx.author.mention} slapped {member.mention}!", file=discord.File(out, filename="slap.png"))
    except Exception as e:
        await ctx.send(f"❌ Slap Error: {e}")

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

# ==================== 6. RUN BOT ====================
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN is missing!")
