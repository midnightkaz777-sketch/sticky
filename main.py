import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("❌ TOKEN is missing from your .env file!")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


# ============================================================
# BOT
# ============================================================

class KazMod(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        print("🔄 Loading extensions...")

        # ----------------------------------------------------
        # TICKETS
        # ----------------------------------------------------

        try:

            await self.load_extension("tickets")

            print("✅ tickets.py loaded")

        except Exception:

            print("❌ tickets.py FAILED to load:")
            traceback.print_exc()

        # ----------------------------------------------------
        # VERIFICATION
        # ----------------------------------------------------

        try:

            await self.load_extension("verification")

            print("✅ verification.py loaded")

        except Exception:

            print("❌ verification.py FAILED to load:")
            traceback.print_exc()

        # ----------------------------------------------------
        # SYNC SLASH COMMANDS
        # ----------------------------------------------------

        try:

            synced = await self.tree.sync()

            print(
                f"✅ Synced {len(synced)} slash commands"
            )

        except Exception:

            print("❌ Slash command sync failed:")
            traceback.print_exc()


# ============================================================
# CREATE BOT
# ============================================================

bot = KazMod()


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    print("====================================")
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print("🤖 KazMod is ready!")
    print("====================================")


# ============================================================
# ERROR HANDLER
# ============================================================

@bot.event
async def on_error(event, *args, **kwargs):

    print(f"❌ Discord event error: {event}")

    traceback.print_exc()


# ============================================================
# START
# ============================================================

try:

    bot.run(TOKEN)

except Exception:

    print("❌ BOT CRASHED:")
    traceback.print_exc()
