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
        user["job_level"] = 1
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
        add_history(ctx.author.id, f"Promoted at {user['job']}, now level {user['job_level']}")
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

@bot.command()
async def slots(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0 or amount > user["wallet"]:
        await ctx.send("Invalid bet amount.")
        return
    symbols = ["🍒", "🍋", "🔔", "⭐", "💎"]
    result = [random.choice(symbols) for _ in range(3)]
    if len(set(result)) == 1:
        winnings = amount * 5
        user["wallet"] += winnings
        outcome = f"JACKPOT! {''.join(result)} You won 💵 {winnings}"
    else:
        user["wallet"] -= amount
        outcome = f"{''.join(result)} You lost 💵 {amount}"
    save_data()
    add_history(ctx.author.id, f"Played slots with {amount} → {outcome}")
    await ctx.send(outcome)

@bot.command()
async def rob(ctx, target: discord.Member):
    user = get_user(ctx.author.id)
    victim = get_user(target.id)
    if victim["wallet"] <= 0:
        await ctx.send("Target has no money to rob.")
        return
    if random.random() < 0.5:
        stolen = random.randint(1, victim["wallet"])
        victim["wallet"] -= stolen
        user["wallet"] += stolen
        result = f"successfully robbed {target.mention} for 💵 {stolen}"
    else:
        fine = random.randint(20, 100)
        user["wallet"] = max(0, user["wallet"] - fine)
        result = f"failed the robbery and lost 💵 {fine}"
    save_data()
    add_history(ctx.author.id, f"Robbery attempt → {result}")
    await ctx.send(f"{ctx.author.mention} {result}.")

@bot.command()
async def lottery(ctx, action=None, tickets: int = 1):
    user = get_user(ctx.author.id)
    if action == "buy":
        price = tickets * 50
        if tickets <= 0 or user["wallet"] < price:
            await ctx.send("Not enough money or invalid ticket count.")
            return
        user["wallet"] -= price
        user["lottery"] += tickets
        save_data()
        add_history(ctx.author.id, f"Bought {tickets} lottery tickets")
        await ctx.send(f"Bought {tickets} tickets for 💵 {price}.")
        return
    if action == "draw":
        winner = random.choice(list(users.keys()))
        prize = 1000
        users[winner]["wallet"] += prize
        save_data()
        add_history(winner, f"Won lottery prize of {prize}")
        await ctx.send(f"🎉 Lottery draw: <@{winner}> won 💵 {prize}!")
        return
    await ctx.send("Usage: `!lottery buy <tickets>` or `!lottery draw`")

# ----------------- Shop & Items -----------------
shop_items = {
    "car": 500,
    "phone": 200,
    "watch": 100
}

@bot.command()
async def shop(ctx):
    items = "\n".join([f"{item} — 💵 {price}" for item, price in shop_items.items()])
    await ctx.send(f"🛒 Shop:\n{items}")

@bot.command()
async def buy(ctx, item: str):
    user = get_user(ctx.author.id)
    if item not in shop_items:
        await ctx.send("Item not found.")
        return
    price = shop_items[item]
    if user["wallet"] < price:
        await ctx.send("Not enough money.")
        return
    user["wallet"] -= price
    user["inventory"].append(item)
    save_data()
    add_history(ctx.author.id, f"Bought item: {item}")
    await ctx.send(f"{ctx.author.mention} bought {item} for 💵 {price}.")

@bot.command()
async def inventory(ctx):
    user = get_user(ctx.author.id)
    if not user["inventory"]:
        await ctx.send("Inventory empty.")
        return
    items = ", ".join(user["inventory"])
    await ctx.send(f"{ctx.author.mention}'s inventory: {items}")

@bot.command()
async def sell(ctx, item: str):
    user = get_user(ctx.author.id)
    if item not in user["inventory"]:
        await ctx.send("You don't own this item.")
        return
    value = shop_items.get(item, 50) // 2
    user["inventory"].remove(item)
    user["wallet"] += value
    save_data()
    add_history(ctx.author.id, f"Sold item: {item}")
    await ctx.send(f"Sold {item} for 💵 {value}.")

@bot.command()
async def use(ctx, item: str):
    user = get_user(ctx.author.id)
    if item not in user["inventory"]:
        await ctx.send("You don't own this item.")
        return
    effect = f"{ctx.author.mention} used {item}!"
    add_history(ctx.author.id, f"Used item: {item}")
    await ctx.send(effect)

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
    add_history(ctx.author.id, f"Deposited {amount}")
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
    add_history(ctx.author.id, f"Withdrew {amount}")
    await ctx.send(f"{ctx.author.mention} withdrew 💵 {amount} from the bank.")

@bot.command()
async def transfer(ctx, target: discord.Member, amount: int):
    user = get_user(ctx.author.id)
    receiver = get_user(target.id)
    if amount <= 0 or amount > user["bank"]:
        await ctx.send("Invalid transfer amount.")
        return
    user["bank"] -= amount
    receiver["bank"] += amount
    save_data()
    add_history(ctx.author.id, f"Transferred {amount} to {target.name}")
    add_history(target.id, f"Received transfer of {amount} from {ctx.author.name}")
    await ctx.send(f"Transferred 💵 {amount} to {target.mention}.")

@bot.command()
async def loan(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0:
        await ctx.send("Invalid loan amount.")
        return
    user["wallet"] += amount
    user["loan"] += amount * 1.1  # 10% interest
    save_data()
    add_history(ctx.author.id, f"Took loan of {amount}")
    await ctx.send(f"Loan approved. You received 💵 {amount}. Pay back 💵 {user['loan']} total.")

@bot.command()
async def repay(ctx, amount: int):
    user = get_user(ctx.author.id)
    if amount <= 0 or amount > user["wallet"]:
        await ctx.send("Invalid repayment amount.")
        return
    repayment = min(amount, user["loan"])
    user["wallet"] -= repayment
    user["loan"] -= repayment
    save_data()
    add_history(ctx.author.id, f"Repaid {repayment} loan")
    await ctx.send(f"Repaid 💵 {repayment}. Remaining loan: 💵 {user['loan']}")

@bot.command()
async def interest(ctx):
    user = get_user(ctx.author.id)
    interest_earned = int(user["bank"] * 0.05)
    user["bank"] += interest_earned
    save_data()
    add_history(ctx.author.id, f"Claimed interest {interest_earned}")
    await ctx.send(f"💵 {interest_earned} interest added to your bank.")

# ----------------- History -----------------
@bot.command()
async def history(ctx):
    user = get_user(ctx.author.id)
    if not user["history"]:
        await ctx.send("No history yet.")
        return
    entries = "\n".join(user["history"][-10:])  # last 10
    await ctx.send(f"📜 Last actions for {ctx.author.mention}:\n{entries}")

# ----------------- Run Bot -----------------
bot.run(os.getenv("BOT_TOKEN"))
