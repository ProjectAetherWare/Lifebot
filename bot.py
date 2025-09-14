import discord
from discord.ext import commands
import random
import json
import os
from datetime import datetime

# ----------------- Persistent Data -----------------
DATA_FILE = "economy.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

users = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "wallet": 100,
            "bank": 0,
            "job": None,
            "job_level": 1,
            "inventory": [],
            "loan": 0,
            "lottery": 0,
            "history": []
        }
        save_data()
    return users[uid]

def add_history(uid, action):
    user = get_user(uid)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user["history"].append(f"[{timestamp}] {action}")
    save_data()

# ----------------- Bot Setup -----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

# ----------------- Balance -----------------
@bot.command()
async def balance(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(f"{ctx.author.mention} — Wallet: 💵 {user['wallet']} | Bank: 💵 {user['bank']}")

# ----------------- Jobs -----------------
jobs = {
    "miner": (50, 100),
    "farmer": (30, 70),
    "programmer": (80, 150),
    "cashier": (20, 50)
}

@bot.command()
async def job(ctx, action=None, choice=None):
    user = get_user(ctx.author.id)

    if action == "list":
        joblist = "\n".join([f"- {j}" for j in jobs.keys()])
        await ctx.send(f"Available jobs:\n{joblist}")
        return

    if action == "choose":
        if choice not in jobs:
            await ctx.send("Invalid job choice.")
            return
        user["job"] = choice
        save_data()
        add_history(ctx.author.id, f"Chose job: {choice}")
        await ctx.send(f"You are now working as a {choice}.")
        return

    if action == "promote":
        if not user["job"]:
            await ctx.send("You must choose a job first with `!job choose <job>`.")
            return
        user["job_level"] += 1
        save_data()
        add_history(ctx.author.id, f"Got promoted at {user['job']}, now level {user['job_level']}")
        await ctx.send(f"Congrats! You got promoted at your {user['job']} job. Level {user['job_level']} pay unlocked!")
        return

    await ctx.send("Usage: `!job list`, `!job choose <job>`, or `!job promote`.")

@bot.command()
async def work(ctx):
    user = get_user(ctx.author.id)
    if not user["job"]:
        await ctx.send("You must first choose a job with `!job choose <job>`.")
        return
    low, high = jobs[user["job"]]
    earnings = random.randint(low, high) * user["job_level"]
    user["wallet"] += earnings
    save_data()
    add_history(ctx.author.id, f"Worked as {user['job']} and earned {earnings}")
    await ctx.send(f"{ctx.author.mention} worked as a {user['job']} and earned 💵 {earnings}!")

# ----------------- Gambling -----------------
@bot.command()
async def gamble(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0 or amount > user["wallet"]:
        await ctx.send("Invalid amount to gamble.")
        return
    if random.choice([True, False]):
        user["wallet"] += amount
        result = f"won 💵 {amount}"
    else:
        user["wallet"] -= amount
        result = f"lost 💵 {amount}"
    save_data()
    add_history(ctx.author.id, f"Gambled {amount} and {result}")
    await ctx.send(f"{ctx.author.mention} gambled {amount} and {result}.")

# ----------------- Banking -----------------
@bot.command()
async def deposit(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0 or amount > user["wallet"]:
        await ctx.send("Invalid deposit amount.")
        return
    user["wallet"] -= amount
    user["bank"] += amount
    save_data()
    add_history(ctx.author.id, f"Deposited {amount} into bank")
    await ctx.send(f"{ctx.author.mention} deposited 💵 {amount} into the bank.")

@bot.command()
async def withdraw(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0 or amount > user["bank"]:
        await ctx.send("Invalid withdrawal amount.")
        return
    user["bank"] -= amount
    user["wallet"] += amount
    save_data()
    add_history(ctx.author.id, f"Withdrew {amount} from bank")
    await ctx.send(f"{ctx.author.mention} withdrew 💵 {amount} from the bank.")

# ----------------- History -----------------
@bot.command()
async def history(ctx):
    user = get_user(ctx.author.id)
    if not user["history"]:
        await ctx.send("No history yet.")
        return
    entries = "\n".join(user["history"][-10:])  # last 10 actions
    await ctx.send(f"📜 Last actions for {ctx.author.mention}:\n{entries}")

# ----------------- Run Bot -----------------
bot.run(os.getenv("BOT_TOKEN"))
