import discord
from discord import app_commands
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

# Slash command tree
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()  # register slash commands
    print(f"{bot.user} is online!")

# ----------------- Jobs -----------------
jobs = {
    "miner": (50, 100),
    "farmer": (30, 70),
    "programmer": (80, 150),
    "cashier": (20, 50)
}

@tree.command(name="balance", description="Check your wallet and bank balance")
async def balance(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    await interaction.response.send_message(
        f"{interaction.user.mention} — Wallet: 💵 {user['wallet']} | Bank: 💵 {user['bank']}"
    )

@tree.command(name="job_list", description="See all available jobs")
async def job_list(interaction: discord.Interaction):
    joblist = "\n".join([f"- {j}" for j in jobs.keys()])
    await interaction.response.send_message(f"Available jobs:\n{joblist}")

@tree.command(name="job_choose", description="Pick a permanent job")
@app_commands.describe(job="The job you want to choose")
async def job_choose(interaction: discord.Interaction, job: str):
    user = get_user(interaction.user.id)
    if job not in jobs:
        await interaction.response.send_message("Invalid job choice.")
        return
    user["job"] = job
    user["job_level"] = 1
    save_data()
    add_history(interaction.user.id, f"Chose job: {job}")
    await interaction.response.send_message(f"You are now working as a {job}.")

@tree.command(name="job_promote", description="Try to get promoted at your job")
async def job_promote(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user["job"]:
        await interaction.response.send_message("You must choose a job first with /job_choose.")
        return
    user["job_level"] += 1
    save_data()
    add_history(interaction.user.id, f"Promoted at {user['job']} to level {user['job_level']}")
    await interaction.response.send_message(f"Congrats! Promoted at {user['job']}. Level {user['job_level']} pay unlocked!")

@tree.command(name="work", description="Do your job and earn money")
async def work(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user["job"]:
        await interaction.response.send_message("You must first choose a job with /job_choose.")
        return
    low, high = jobs[user["job"]]
    earnings = random.randint(low, high) * user["job_level"]
    user["wallet"] += earnings
    save_data()
    add_history(interaction.user.id, f"Worked as {user['job']} and earned {earnings}")
    await interaction.response.send_message(f"You worked as a {user['job']} and earned 💵 {earnings}!")

# ----------------- Gambling -----------------
@tree.command(name="gamble", description="Gamble money (50/50 chance)")
@app_commands.describe(amount="Amount to gamble")
async def gamble(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or amount > user["wallet"]:
        await interaction.response.send_message("Invalid amount to gamble.")
        return
    if random.choice([True, False]):
        user["wallet"] += amount
        result = f"won 💵 {amount}"
    else:
        user["wallet"] -= amount
        result = f"lost 💵 {amount}"
    save_data()
    add_history(interaction.user.id, f"Gambled {amount} and {result}")
    await interaction.response.send_message(f"You gambled {amount} and {result}.")

@tree.command(name="slots", description="Play the slot machine")
@app_commands.describe(amount="Amount to bet")
async def slots(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or amount > user["wallet"]:
        await interaction.response.send_message("Invalid bet amount.")
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
    add_history(interaction.user.id, f"Played slots with {amount} → {outcome}")
    await interaction.response.send_message(outcome)

@tree.command(name="rob", description="Try to rob another user")
@app_commands.describe(target="User to rob")
async def rob(interaction: discord.Interaction, target: discord.Member):
    user = get_user(interaction.user.id)
    victim = get_user(target.id)
    if victim["wallet"] <= 0:
        await interaction.response.send_message("Target has no money to rob.")
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
    add_history(interaction.user.id, f"Robbery attempt → {result}")
    await interaction.response.send_message(result)

# ----------------- Lottery -----------------
@tree.command(name="lottery_buy", description="Buy lottery tickets")
@app_commands.describe(tickets="Number of tickets to buy")
async def lottery_buy(interaction: discord.Interaction, tickets: int):
    user = get_user(interaction.user.id)
    price = tickets * 50
    if tickets <= 0 or user["wallet"] < price:
        await interaction.response.send_message("Not enough money or invalid ticket count.")
        return
    user["wallet"] -= price
    user["lottery"] += tickets
    save_data()
    add_history(interaction.user.id, f"Bought {tickets} lottery tickets")
    await interaction.response.send_message(f"Bought {tickets} tickets for 💵 {price}.")

@tree.command(name="lottery_draw", description="Draw the lottery winner (admin only)")
async def lottery_draw(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can draw the lottery.")
        return
    if not users:
        await interaction.response.send_message("No users available.")
        return
    winner = random.choice(list(users.keys()))
    prize = 1000
    users[winner]["wallet"] += prize
    save_data()
    add_history(int(winner), f"Won lottery prize of {prize}")
    await interaction.response.send_message(f"🎉 Lottery draw: <@{winner}> won 💵 {prize}!")

# ----------------- Shop & Items -----------------
shop_items = {
    "car": 500,
    "phone": 200,
    "watch": 100
}

@tree.command(name="shop", description="See shop items")
async def shop(interaction: discord.Interaction):
    items = "\n".join([f"{item} — 💵 {price}" for item, price in shop_items.items()])
    await interaction.response.send_message(f"🛒 Shop:\n{items}")

@tree.command(name="buy", description="Buy an item from the shop")
@app_commands.describe(item="Item to buy")
async def buy(interaction: discord.Interaction, item: str):
    user = get_user(interaction.user.id)
    if item not in shop_items:
        await interaction.response.send_message("Item not found.")
        return
    price = shop_items[item]
    if user["wallet"] < price:
        await interaction.response.send_message("Not enough money.")
        return
    user["wallet"] -= price
    user["inventory"].append(item)
    save_data()
    add_history(interaction.user.id, f"Bought item: {item}")
    await interaction.response.send_message(f"You bought {item} for 💵 {price}.")

@tree.command(name="sell", description="Sell an item from your inventory")
@app_commands.describe(item="Item to sell")
async def sell(interaction: discord.Interaction, item: str):
    user = get_user(interaction.user.id)
    if item not in user["inventory"]:
        await interaction.response.send_message("You don't own this item.")
        return
    value = shop_items.get(item, 50) // 2
    user["inventory"].remove(item)
    user["wallet"] += value
    save_data()
    add_history(interaction.user.id, f"Sold item: {item}")
    await interaction.response.send_message(f"Sold {item} for 💵 {value}.")

@tree.command(name="inventory", description="See your inventory")
async def inventory(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user["inventory"]:
        await interaction.response.send_message("Inventory empty.")
        return
    items = ", ".join(user["inventory"])
    await interaction.response.send_message(f"Your inventory: {items}")

@tree.command(name="use", description="Use an item from your inventory")
@app_commands.describe(item="Item to use")
async def use(interaction: discord.Interaction, item: str):
    user = get_user(interaction.user.id)
    if item not in user["inventory"]:
        await interaction.response.send_message("You don't own this item.")
        return
    add_history(interaction.user.id, f"Used item: {item}")
    await interaction.response.send_message(f"You used {item}!")

# ----------------- Banking -----------------
@tree.command(name="deposit", description="Deposit money into bank")
@app_commands.describe(amount="Amount to deposit")
async def deposit(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or amount > user["wallet"]:
        await interaction.response.send_message("Invalid deposit amount.")
        return
    user["wallet"] -= amount
    user["bank"] += amount
    save_data()
    add_history(interaction.user.id, f"Deposited {amount}")
    await interaction.response.send_message(f"Deposited 💵 {amount} into the bank.")

@tree.command(name="withdraw", description="Withdraw money from bank")
@app_commands.describe(amount="Amount to withdraw")
async def withdraw(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or amount > user["bank"]:
        await interaction.response.send_message("Invalid withdrawal amount.")
        return
    user["bank"] -= amount
    user["wallet"] += amount
    save_data()
    add_history(interaction.user.id, f"Withdrew {amount}")
    await interaction.response.send_message(f"Withdrew 💵 {amount} from the bank.")

@tree.command(name="transfer", description="Transfer money to another user")
@app_commands.describe(target="User to send money to", amount="Amount to send")
async def transfer(interaction: discord.Interaction, target: discord.Member, amount: int):
    user = get_user(interaction.user.id)
    receiver = get_user(target.id)
    if amount <= 0 or amount > user["bank"]:
        await interaction.response.send_message("Invalid transfer amount.")
        return
    user["bank"] -= amount
    receiver["bank"] += amount
    save_data()
    add_history(interaction.user.id, f"Transferred {amount} to {target.name}")
    add_history(target.id, f"Received transfer of {amount} from {interaction.user.name}")
    await interaction.response.send_message(f"Transferred 💵 {amount} to {target.mention}.")

@tree.command(name="loan", description="Take a loan with interest")
@app_commands.describe(amount="Amount to loan")
async def loan(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0:
        await interaction.response.send_message("Invalid loan amount.")
        return
    user["wallet"] += amount
    user["loan"] += amount * 1.1  # 10% interest
    save_data()
    add_history(interaction.user.id, f"Took loan of {amount}")
    await interaction.response.send_message(f"Loan approved. You received 💵 {amount}. Pay back 💵 {user['loan']} total.")

@tree.command(name="repay", description="Repay part of your loan")
@app_commands.describe(amount="Amount to repay")
async def repay(interaction: discord.Interaction, amount: int):
    user = get_user(interaction.user.id)
    if amount <= 0 or amount > user["wallet"]:
        await interaction.response.send_message("Invalid repayment amount.")
        return
    repayment = min(amount, user["loan"])
    user["wallet"] -= repayment
    user["loan"] -= repayment
    save_data()
    add_history(interaction.user.id, f"Repaid {repayment} loan")
    await interaction.response.send_message(f"Repaid 💵 {repayment}. Remaining loan: 💵 {user['loan']}")

@tree.command(name="interest", description="Claim passive interest on your bank")
async def interest(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    interest_earned = int(user["bank"] * 0.05)
    user["bank"] += interest_earned
    save_data()
    add_history(interaction.user.id, f"Claimed interest {interest_earned}")
    await interaction.response.send_message(f"💵 {interest_earned} interest added to your bank.")

# ----------------- History -----------------
@tree.command(name="history", description="Show last 10 actions you did")
async def history(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    if not user["history"]:
        await interaction.response.send_message("No history yet.")
        return
    entries = "\n".join(user["history"][-10:])
    await interaction.response.send_message(f"📜 Last actions:\n{entries}")

# ----------------- Run Bot -----------------
bot.run(os.getenv("BOT_TOKEN"))
