import discord
from discord.ext import commands

# ============================================================
# CONFIGURATION
# ============================================================

VERIFICATION_CHANNEL_ID = 1535124754929815612
VERIFIED_ROLE_ID = 1535115908757061702


# ============================================================
# VERIFICATION VIEW
# ============================================================

class VerificationView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="kazmod_verify"
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild
        member = interaction.user

        if guild is None:
            return

        verified_role = guild.get_role(
            VERIFIED_ROLE_ID
        )

        if verified_role is None:

            await interaction.response.send_message(
                "❌ The Verified role could not be found.",
                ephemeral=True
            )

            return

        # Already verified
        if verified_role in member.roles:

            await interaction.response.send_message(
                "✅ You are already verified!",
                ephemeral=True
            )

            return

        # Give role
        try:

            await member.add_roles(
                verified_role,
                reason="Completed server verification"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I cannot give you the Verified role.\n\n"
                "Make sure KazMod's role is above the "
                "Verified role.",
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ Discord returned an error. "
                "Please try again.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "✅ **Verification successful!**\n\n"
            "You now have access to the server.",
            ephemeral=True
        )


# ============================================================
# VERIFICATION COG
# ============================================================

class Verification(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    async def cog_load(self):

        # Make the button work after restarts
        self.bot.add_view(
            VerificationView()
        )

    # ========================================================
    # CREATE PANEL AFTER BOT IS READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(self):

        # Prevent duplicates during reconnects
        if getattr(
            self.bot,
            "verification_panel_created",
            False
        ):

            return

        self.bot.verification_panel_created = True

        await self.create_verification_panel()

    # ========================================================
    # CREATE PANEL ONLY ONCE
    # ========================================================

    async def create_verification_panel(self):

        channel = self.bot.get_channel(
            VERIFICATION_CHANNEL_ID
        )

        if channel is None:

            print(
                "❌ Verification channel was not found."
            )

            print(
                f"❌ Channel ID: {VERIFICATION_CHANNEL_ID}"
            )

            return

        # ====================================================
        # CHECK EXISTING PANEL
        # ====================================================

        try:

            async for message in channel.history(
                limit=100
            ):

                if (

                    message.author == self.bot.user

                    and message.embeds

                    and message.embeds[0].title
                    == "🔐 Server Verification"
                ):

                    print(
                        "✅ Verification panel already exists."
                    )

                    return

        except discord.Forbidden:

            print(
                "❌ KazMod cannot read the verification channel."
            )

            return

        # ====================================================
        # CREATE PANEL
        # ====================================================

        embed = discord.Embed(

            title="🔐 Server Verification",

            description=(

                "Welcome to the server!\n\n"

                "Before accessing the server, "
                "you must verify yourself.\n\n"

                "Click **Verify** below to receive "
                "your Verified role.\n\n"

                "✅ **Verified** — Gain access to the server."
            ),

            color=discord.Color.green()
        )

        embed.set_footer(
            text="KazMod Verification System"
        )

        await channel.send(

            embed=embed,

            view=VerificationView()
        )

        print(
            "✅ Verification panel created."
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Verification(bot)
    )