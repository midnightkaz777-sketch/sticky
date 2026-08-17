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

        print(
            f"📩 Verification requested by "
            f"{interaction.user} ({interaction.user.id})"
        )

        guild = interaction.guild
        member = interaction.user

        if guild is None:

            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )

            return

        # ====================================================
        # RESPOND IMMEDIATELY
        # ====================================================

        try:

            await interaction.response.defer(
                ephemeral=True
            )

        except Exception as e:

            print(
                f"❌ Verification interaction error: {e}"
            )

            return

        # ====================================================
        # GET VERIFIED ROLE
        # ====================================================

        verified_role = guild.get_role(
            VERIFIED_ROLE_ID
        )

        if verified_role is None:

            await interaction.followup.send(
                "❌ The Verified role could not be found.",
                ephemeral=True
            )

            return

        # ====================================================
        # ALREADY VERIFIED
        # ====================================================

        if verified_role in member.roles:

            await interaction.followup.send(
                "✅ You are already verified!",
                ephemeral=True
            )

            return

        # ====================================================
        # GIVE ROLE
        # ====================================================

        try:

            await member.add_roles(
                verified_role,
                reason="Completed server verification"
            )

        except discord.Forbidden:

            await interaction.followup.send(

                "❌ I cannot give you the Verified role.\n\n"
                "Make sure KazMod's role is **above** "
                "the Verified role.",

                ephemeral=True
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Verification role error: {e}"
            )

            await interaction.followup.send(

                "❌ Discord returned an error while "
                "giving you the role. Please try again.",

                ephemeral=True
            )

            return

        # ====================================================
        # SUCCESS
        # ====================================================

        await interaction.followup.send(

            "✅ **Verification successful!**\n\n"
            "You now have access to the server.",

            ephemeral=True
        )

        print(
            f"✅ {member} was verified."
        )


# ============================================================
# VERIFICATION COG
# ============================================================

class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # LOAD PERSISTENT VIEW
    # ========================================================

    async def cog_load(self):

        self.bot.add_view(
            VerificationView()
        )

        print(
            "✅ Verification persistent view registered."
        )

    # ========================================================
    # READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(self):

        if getattr(
            self.bot,
            "verification_panel_created",
            False
        ):

            return

        self.bot.verification_panel_created = True

        await self.create_verification_panel()

    # ========================================================
    # CREATE VERIFICATION PANEL
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
                f"❌ Channel ID: "
                f"{VERIFICATION_CHANNEL_ID}"
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

        except discord.HTTPException as e:

            print(
                f"❌ Could not check verification channel: {e}"
            )

            return

        # ====================================================
        # CREATE EMBED
        # ====================================================

        embed = discord.Embed(

            title="🔐 Server Verification",

            description=(

                "Welcome to the server!\n\n"

                "Before accessing the server, "
                "you must verify yourself.\n\n"

                "Click **Verify** below to receive "
                "your Verified role.\n\n"

                "✅ **Verified** — Gain access "
                "to the server."
            ),

            color=discord.Color.green()
        )

        embed.set_footer(
            text="KazMod Verification System"
        )

        # ====================================================
        # SEND PANEL
        # ====================================================

        try:

            await channel.send(

                embed=embed,

                view=VerificationView()
            )

            print(
                "✅ Verification panel created."
            )

        except discord.Forbidden:

            print(
                "❌ KazMod cannot send messages "
                "in the verification channel."
            )

        except discord.HTTPException as e:

            print(
                f"❌ Could not create verification panel: {e}"
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Verification(bot)
    )
