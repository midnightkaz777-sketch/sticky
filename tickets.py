import discord
from discord.ext import commands


# ============================================================
# CONFIGURATION
# ============================================================

TICKET_CATEGORY_ID = 1535126999637430383
TICKET_LOG_CHANNEL_ID = 1535122682616619098
TICKET_PANEL_CHANNEL_ID = 1535127109242978324

STAFF_ROLE_ID = 1535115836149202954
ADMIN_ROLE_ID = 1535115783271878778


# ============================================================
# APPLICATION TYPES
# ============================================================

TICKET_TYPES = {
    "staff": {
        "name": "Staff Application",
        "role_id": STAFF_ROLE_ID,
        "emoji": "🔧",
    },

    "administrator": {
        "name": "Administrator Application",
        "role_id": ADMIN_ROLE_ID,
        "emoji": "🛡️",
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def has_staff_or_admin(member: discord.Member) -> bool:

    staff_role = member.guild.get_role(STAFF_ROLE_ID)
    admin_role = member.guild.get_role(ADMIN_ROLE_ID)

    return (
        (staff_role is not None and staff_role in member.roles)
        or
        (admin_role is not None and admin_role in member.roles)
    )


# ============================================================
# TICKET SELECT MENU
# ============================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="Staff Application",
                description="Apply to become Staff",
                emoji="🔧",
                value="staff",
            ),

            discord.SelectOption(
                label="Administrator Application",
                description="Apply to become Administrator",
                emoji="🛡️",
                value="administrator",
            ),
        ]

        super().__init__(
            placeholder="Choose an application...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="kazmod_ticket_select",
        )

    async def callback(self, interaction: discord.Interaction):

        print(
            f"📩 Application selected by "
            f"{interaction.user} ({interaction.user.id})"
        )

        guild = interaction.guild
        member = interaction.user

        if guild is None:

            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True,
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
                f"❌ Could not acknowledge interaction: {e}"
            )

            return

        # ====================================================
        # GET APPLICATION TYPE
        # ====================================================

        ticket_type = self.values[0]

        ticket_info = TICKET_TYPES.get(
            ticket_type
        )

        if ticket_info is None:

            await interaction.followup.send(
                "❌ Invalid application type.",
                ephemeral=True,
            )

            return

        # ====================================================
        # GET CATEGORY
        # ====================================================

        category = guild.get_channel(
            TICKET_CATEGORY_ID
        )

        if category is None:

            await interaction.followup.send(
                "❌ Ticket category was not found.",
                ephemeral=True,
            )

            return

        # ====================================================
        # CHECK EXISTING TICKET
        # ====================================================

        for channel in guild.text_channels:

            if channel.topic == f"ticket_owner:{member.id}":

                await interaction.followup.send(
                    f"❌ You already have an application ticket: "
                    f"{channel.mention}",
                    ephemeral=True,
                )

                return

        # ====================================================
        # GET STAFF ROLE
        # ====================================================

        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )

        if staff_role is None:

            await interaction.followup.send(
                "❌ Staff role was not found.",
                ephemeral=True,
            )

            return

        # ====================================================
        # CREATE PERMISSIONS
        # ====================================================

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            member:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                ),
        }

        # ====================================================
        # ADD ADMIN ROLE
        # ====================================================

        admin_role = guild.get_role(
            ADMIN_ROLE_ID
        )

        if admin_role is not None:

            overwrites[admin_role] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                )
            )

        # ====================================================
        # CREATE CHANNEL
        # ====================================================

        try:

            channel = await guild.create_text_channel(

                name=f"{ticket_type}-{member.name}",

                category=category,

                topic=f"ticket_owner:{member.id}",

                overwrites=overwrites,

                reason=(
                    f"{ticket_info['name']} "
                    f"created by {member}"
                ),
            )

            print(
                f"✅ Created ticket #{channel.name}"
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ I don't have permission to create "
                "ticket channels.",
                ephemeral=True,
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Channel creation error: {e}"
            )

            await interaction.followup.send(
                "❌ Discord could not create the ticket.",
                ephemeral=True,
            )

            return

        # ====================================================
        # TICKET EMBED
        # ====================================================

        application_name = (
            ticket_info["name"]
            .replace(" Application", "")
        )

        embed = discord.Embed(

            title=(
                f"{ticket_info['emoji']} "
                f"{ticket_info['name']}"
            ),

            description=(

                f"Welcome {member.mention}!\n\n"

                f"**Application:** "
                f"{ticket_info['name']}\n"

                f"**Applicant:** "
                f"{member.mention}\n\n"

                f"Please explain why you would be "
                f"a good **{application_name}**.\n\n"

                "A Staff member will review your "
                "application."
            ),

            color=discord.Color.blurple(),
        )

        embed.set_footer(
            text=f"Applicant ID: {member.id}"
        )

        # ====================================================
        # SEND TICKET MESSAGE
        # ====================================================

        try:

            await channel.send(

                content=member.mention,

                embed=embed,

                view=TicketControlView(),
            )

        except discord.HTTPException as e:

            print(
                f"❌ Could not send ticket message: {e}"
            )

        # ====================================================
        # LOG CHANNEL
        # ====================================================

        log_channel = guild.get_channel(
            TICKET_LOG_CHANNEL_ID
        )

        if log_channel is None:

            print(
                "⚠️ Ticket log channel was not found."
            )

        else:

            log_embed = discord.Embed(

                title="📋 New Application",

                description=(

                    f"**Applicant:** "
                    f"{member.mention}\n"

                    f"**Application:** "
                    f"{ticket_info['name']}\n"

                    f"**Ticket:** "
                    f"{channel.mention}\n"

                    "**Status:** 🟡 Pending"
                ),

                color=discord.Color.yellow(),
            )

            log_embed.set_footer(
                text=f"Applicant ID: {member.id}"
            )

            try:

                await log_channel.send(

                    embed=log_embed,

                    view=ApplicationDecisionView(
                        applicant_id=member.id,
                        role_id=ticket_info["role_id"],
                        ticket_channel_id=channel.id,
                    ),
                )

            except discord.HTTPException as e:

                print(
                    f"❌ Could not send application log: {e}"
                )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        try:

            await interaction.followup.send(

                f"✅ Your application ticket has been "
                f"created: {channel.mention}",

                ephemeral=True,
            )

        except discord.HTTPException as e:

            print(
                f"❌ Could not send final response: {e}"
            )


# ============================================================
# TICKET PANEL
# ============================================================

class TicketPanelView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


# ============================================================
# TICKET CONTROL VIEW
# ============================================================

class TicketControlView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="kazmod_close_ticket",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        guild = interaction.guild

        if guild is None:

            return

        if not has_staff_or_admin(
            interaction.user
        ):

            await interaction.response.send_message(

                "❌ Only Staff or Administrators "
                "can close tickets.",

                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            "🔒 Closing ticket...",
            ephemeral=True,
        )

        try:

            await interaction.channel.delete(
                reason=(
                    f"Ticket closed by "
                    f"{interaction.user}"
                )
            )

        except discord.Forbidden:

            print(
                "❌ KazMod cannot delete ticket channel."
            )

        except discord.HTTPException as e:

            print(
                f"❌ Ticket deletion error: {e}"
            )


# ============================================================
# APPLICATION DECISION VIEW
# ============================================================

class ApplicationDecisionView(
    discord.ui.View
):

    def __init__(
        self,
        applicant_id: int,
        role_id: int,
        ticket_channel_id: int,
    ):

        super().__init__(
            timeout=None
        )

        self.applicant_id = applicant_id
        self.role_id = role_id
        self.ticket_channel_id = ticket_channel_id

    # ========================================================
    # ACCEPT
    # ========================================================

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="kazmod_application_accept",
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # ----------------------------------------------------
        # PERMISSION CHECK
        # ----------------------------------------------------

        if not has_staff_or_admin(
            interaction.user
        ):

            await interaction.response.send_message(

                "❌ Only Staff or Administrators "
                "can accept applications.",

                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # ACKNOWLEDGE
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild

        if guild is None:

            await interaction.followup.send(
                "❌ Server not found.",
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # FIND MEMBER
        # ----------------------------------------------------

        member = guild.get_member(
            self.applicant_id
        )

        if member is None:

            try:

                member = await guild.fetch_member(
                    self.applicant_id
                )

            except discord.NotFound:

                await interaction.followup.send(
                    "❌ Applicant could not be found.",
                    ephemeral=True,
                )

                return

            except discord.HTTPException:

                await interaction.followup.send(
                    "❌ Discord could not find the applicant.",
                    ephemeral=True,
                )

                return

        # ----------------------------------------------------
        # FIND ROLE
        # ----------------------------------------------------

        role = guild.get_role(
            self.role_id
        )

        if role is None:

            await interaction.followup.send(
                "❌ Application role could not be found.",
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # GIVE ROLE
        # ----------------------------------------------------

        try:

            await member.add_roles(

                role,

                reason=(
                    f"Application accepted by "
                    f"{interaction.user}"
                ),
            )

        except discord.Forbidden:

            await interaction.followup.send(

                "❌ I cannot give this role.\n\n"
                "Make sure KazMod's highest role is "
                "**above** the Staff/Administrator role.",

                ephemeral=True,
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Role error: {e}"
            )

            await interaction.followup.send(
                "❌ Discord could not give the role.",
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # UPDATE LOG
        # ----------------------------------------------------

        if interaction.message.embeds:

            embed = interaction.message.embeds[0]

            embed.description = (

                f"**Applicant:** "
                f"{member.mention}\n"

                "**Status:** 🟢 ACCEPTED\n"

                f"**Approved by:** "
                f"{interaction.user.mention}\n"

                f"**Role:** {role.mention}"
            )

            embed.color = discord.Color.green()

            try:

                await interaction.message.edit(

                    embed=embed,

                    view=None,
                )

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # DM
        # ----------------------------------------------------

        try:

            await member.send(

                f"🎉 Your **{role.name}** application "
                f"in **{guild.name}** was accepted!\n\n"

                f"You have received the "
                f"**{role.name}** role."
            )

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):

            pass

        # ----------------------------------------------------
        # UPDATE TICKET
        # ----------------------------------------------------

        ticket_channel = guild.get_channel(
            self.ticket_channel_id
        )

        if ticket_channel:

            try:

                await ticket_channel.send(

                    f"🎉 {member.mention}, your "
                    f"application was **accepted** by "
                    f"{interaction.user.mention}!"
                )

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # DONE
        # ----------------------------------------------------

        await interaction.followup.send(
            "✅ Application accepted.",
            ephemeral=True,
        )

    # ========================================================
    # DENY
    # ========================================================

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="kazmod_application_deny",
    )
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        # ----------------------------------------------------
        # PERMISSION CHECK
        # ----------------------------------------------------

        if not has_staff_or_admin(
            interaction.user
        ):

            await interaction.response.send_message(

                "❌ Only Staff or Administrators "
                "can deny applications.",

                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # ACKNOWLEDGE
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild

        if guild is None:

            await interaction.followup.send(
                "❌ Server not found.",
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # FIND MEMBER
        # ----------------------------------------------------

        member = guild.get_member(
            self.applicant_id
        )

        # ----------------------------------------------------
        # UPDATE LOG
        # ----------------------------------------------------

        if interaction.message.embeds:

            embed = interaction.message.embeds[0]

            if member:

                embed.description = (

                    f"**Applicant:** "
                    f"{member.mention}\n"

                    "**Status:** 🔴 DENIED\n"

                    f"**Denied by:** "
                    f"{interaction.user.mention}"
                )

            else:

                embed.description = (

                    f"**Applicant ID:** "
                    f"`{self.applicant_id}`\n"

                    "**Status:** 🔴 DENIED\n"

                    f"**Denied by:** "
                    f"{interaction.user.mention}"
                )

            embed.color = discord.Color.red()

            try:

                await interaction.message.edit(

                    embed=embed,

                    view=None,
                )

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # DM
        # ----------------------------------------------------

        if member:

            try:

                await member.send(

                    f"❌ Your application in "
                    f"**{guild.name}** was denied."
                )

            except (
                discord.Forbidden,
                discord.HTTPException,
            ):

                pass

            # ------------------------------------------------
            # UPDATE TICKET
            # ------------------------------------------------

            ticket_channel = guild.get_channel(
                self.ticket_channel_id
            )

            if ticket_channel:

                try:

                    await ticket_channel.send(

                        f"❌ {member.mention}, your "
                        f"application was **denied** by "
                        f"{interaction.user.mention}."
                    )

                except discord.HTTPException:

                    pass

        # ----------------------------------------------------
        # DONE
        # ----------------------------------------------------

        await interaction.followup.send(
            "❌ Application denied.",
            ephemeral=True,
        )


# ============================================================
# COG
# ============================================================

class Tickets(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    async def cog_load(self):

        # ----------------------------------------------------
        # REGISTER PERSISTENT VIEWS
        # ----------------------------------------------------

        self.bot.add_view(
            TicketPanelView()
        )

        self.bot.add_view(
            TicketControlView()
        )

        print(
            "✅ Ticket persistent views registered"
        )

    # ========================================================
    # READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(self):

        if getattr(
            self.bot,
            "ticket_panel_created",
            False,
        ):

            return

        self.bot.ticket_panel_created = True

        await self.create_ticket_panel()

    # ========================================================
    # CREATE PANEL
    # ========================================================

    async def create_ticket_panel(self):

        channel = self.bot.get_channel(
            TICKET_PANEL_CHANNEL_ID
        )

        if channel is None:

            print(
                "❌ Ticket panel channel was not found."
            )

            return

        # ----------------------------------------------------
        # CHECK FOR EXISTING PANEL
        # ----------------------------------------------------

        try:

            async for message in channel.history(
                limit=100
            ):

                if (

                    message.author == self.bot.user

                    and message.embeds

                    and message.embeds[0].title
                    == "🎫 Staff Applications"

                ):

                    print(
                        "✅ Ticket panel already exists."
                    )

                    return

        except discord.Forbidden:

            print(
                "❌ KazMod cannot read the ticket panel channel."
            )

            return

        except discord.HTTPException as e:

            print(
                f"❌ Could not check ticket panel: {e}"
            )

            return

        # ----------------------------------------------------
        # PANEL EMBED
        # ----------------------------------------------------

        embed = discord.Embed(

            title="🎫 Staff Applications",

            description=(

                "Want to join the staff team?\n\n"

                "Select an application below to "
                "create a private ticket.\n\n"

                "🔧 **Staff Application**\n"
                "Apply to become Staff.\n\n"

                "🛡️ **Administrator Application**\n"
                "Apply to become an Administrator."
            ),

            color=discord.Color.blurple(),
        )

        embed.set_footer(
            text="KazMod Staff Applications"
        )

        # ----------------------------------------------------
        # SEND PANEL
        # ----------------------------------------------------

        try:

            await channel.send(

                embed=embed,

                view=TicketPanelView(),
            )

            print(
                "✅ Ticket panel created."
            )

        except discord.Forbidden:

            print(
                "❌ KazMod cannot send messages "
                "in the ticket panel channel."
            )

        except discord.HTTPException as e:

            print(
                f"❌ Could not create ticket panel: {e}"
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Tickets(bot)
    )
