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
# TICKET TYPES
# ============================================================

TICKET_TYPES = {
    "staff": {
        "name": "Staff Application",
        "role_id": STAFF_ROLE_ID,
        "emoji": "🔧"
    },
    "administrator": {
        "name": "Administrator Application",
        "role_id": ADMIN_ROLE_ID,
        "emoji": "🛡️"
    }
}


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
                value="staff"
            ),
            discord.SelectOption(
                label="Administrator Application",
                description="Apply to become Administrator",
                emoji="🛡️",
                value="administrator"
            )
        ]

        super().__init__(
            placeholder="Choose an application...",
            options=options,
            custom_id="kazmod_ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        member = interaction.user
        ticket_type = self.values[0]

        if guild is None:
            await interaction.response.send_message(
                "❌ This can only be used inside a server.",
                ephemeral=True
            )
            return

        # --------------------------------------------------------
        # ACKNOWLEDGE IMMEDIATELY
        # --------------------------------------------------------

        await interaction.response.defer(ephemeral=True)

        # --------------------------------------------------------
        # CATEGORY
        # --------------------------------------------------------

        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            await interaction.followup.send(
                "❌ Ticket category was not found.",
                ephemeral=True
            )
            return

        # --------------------------------------------------------
        # CHECK EXISTING TICKET
        # --------------------------------------------------------

        for channel in guild.text_channels:

            if channel.topic == f"ticket_owner:{member.id}":

                await interaction.followup.send(
                    f"❌ You already have a ticket: {channel.mention}",
                    ephemeral=True
                )
                return

        # --------------------------------------------------------
        # GET STAFF ROLE
        # --------------------------------------------------------

        staff_role = guild.get_role(STAFF_ROLE_ID)

        if staff_role is None:
            await interaction.followup.send(
                "❌ Staff role was not found.",
                ephemeral=True
            )
            return

        ticket_info = TICKET_TYPES.get(ticket_type)

        if ticket_info is None:
            await interaction.followup.send(
                "❌ Invalid application type.",
                ephemeral=True
            )
            return

        # --------------------------------------------------------
        # PERMISSIONS
        # --------------------------------------------------------

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),

            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )
        }

        # --------------------------------------------------------
        # CREATE TICKET
        # --------------------------------------------------------

        try:

            channel = await guild.create_text_channel(
                name=f"{ticket_type}-{member.name}",
                category=category,
                topic=f"ticket_owner:{member.id}",
                overwrites=overwrites,
                reason=f"{ticket_info['name']} created by {member}"
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ I don't have permission to create ticket channels.",
                ephemeral=True
            )
            return

        except discord.HTTPException as e:

            print(f"Ticket channel creation error: {e}")

            await interaction.followup.send(
                "❌ Discord could not create the ticket channel.",
                ephemeral=True
            )
            return

        # --------------------------------------------------------
        # TICKET EMBED
        # --------------------------------------------------------

        application_name = ticket_info["name"].replace(
            " Application",
            ""
        )

        embed = discord.Embed(
            title=f"{ticket_info['emoji']} {ticket_info['name']}",
            description=(
                f"Welcome {member.mention}!\n\n"
                f"**Application:** {ticket_info['name']}\n"
                f"**Applicant:** {member.mention}\n\n"
                f"Please explain why you would be a good "
                f"**{application_name}**.\n\n"
                "A Staff member will review your application."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text=f"Applicant ID: {member.id}"
        )

        # --------------------------------------------------------
        # SEND TICKET MESSAGE
        # --------------------------------------------------------

        try:

            await channel.send(
                content=member.mention,
                embed=embed,
                view=TicketControlView()
            )

        except discord.HTTPException as e:

            print(f"Ticket message error: {e}")

        # --------------------------------------------------------
        # LOG CHANNEL
        # --------------------------------------------------------

        log_channel = guild.get_channel(
            TICKET_LOG_CHANNEL_ID
        )

        if log_channel:

            log_embed = discord.Embed(
                title="📋 New Application",
                description=(
                    f"**Applicant:** {member.mention}\n"
                    f"**Application:** {ticket_info['name']}\n"
                    f"**Ticket:** {channel.mention}\n"
                    "**Status:** 🟡 Pending"
                ),
                color=discord.Color.yellow()
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
                        ticket_channel_id=channel.id
                    )
                )

            except discord.HTTPException as e:

                print(f"Log message error: {e}")

        # --------------------------------------------------------
        # FINAL RESPONSE
        # --------------------------------------------------------

        await interaction.followup.send(
            f"✅ Your application ticket has been created: "
            f"{channel.mention}",
            ephemeral=True
        )


# ============================================================
# PANEL VIEW
# ============================================================

class TicketPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            TicketSelect()
        )


# ============================================================
# TICKET CONTROL VIEW
# ============================================================

class TicketControlView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="kazmod_close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        if guild is None:
            return

        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )

        admin_role = guild.get_role(
            ADMIN_ROLE_ID
        )

        is_staff = (
            staff_role is not None
            and staff_role in interaction.user.roles
        )

        is_admin = (
            admin_role is not None
            and admin_role in interaction.user.roles
        )

        if not is_staff and not is_admin:

            await interaction.response.send_message(
                "❌ Only Staff or Administrators can close tickets.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Closing ticket...",
            ephemeral=True
        )

        await interaction.channel.delete(
            reason=f"Ticket closed by {interaction.user}"
        )


# ============================================================
# APPLICATION DECISION VIEW
# ============================================================

class ApplicationDecisionView(discord.ui.View):

    def __init__(
        self,
        applicant_id: int,
        role_id: int,
        ticket_channel_id: int
    ):

        super().__init__(timeout=None)

        self.applicant_id = applicant_id
        self.role_id = role_id
        self.ticket_channel_id = ticket_channel_id

    # --------------------------------------------------------
    # STAFF CHECK
    # --------------------------------------------------------

    def is_staff(self, member):

        staff_role = member.guild.get_role(
            STAFF_ROLE_ID
        )

        admin_role = member.guild.get_role(
            ADMIN_ROLE_ID
        )

        return (
            (staff_role is not None and staff_role in member.roles)
            or
            (admin_role is not None and admin_role in member.roles)
        )

    # ========================================================
    # ACCEPT
    # ========================================================

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="kazmod_application_accept"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.is_staff(interaction.user):

            await interaction.response.send_message(
                "❌ Only Staff or Administrators can accept applications.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # ACKNOWLEDGE IMMEDIATELY
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild

        if guild is None:
            await interaction.followup.send(
                "❌ Server not found.",
                ephemeral=True
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
                    ephemeral=True
                )
                return

            except discord.HTTPException:

                await interaction.followup.send(
                    "❌ Discord could not find the applicant.",
                    ephemeral=True
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
                "❌ Role could not be found.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # ADD ROLE
        # ----------------------------------------------------

        try:

            await member.add_roles(
                role,
                reason=f"Application accepted by {interaction.user}"
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ I cannot give this role.\n\n"
                "Make sure KazMod's highest role is above "
                "the Staff/Administrator role.",
                ephemeral=True
            )
            return

        except discord.HTTPException as e:

            print(f"Role error: {e}")

            await interaction.followup.send(
                "❌ Discord could not give the role.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # UPDATE LOG EMBED
        # ----------------------------------------------------

        if interaction.message.embeds:

            embed = interaction.message.embeds[0]

            embed.description = (
                f"**Applicant:** {member.mention}\n"
                "**Status:** 🟢 ACCEPTED\n"
                f"**Approved by:** {interaction.user.mention}\n"
                f"**Role:** {role.mention}"
            )

            embed.color = discord.Color.green()

            try:

                await interaction.message.edit(
                    embed=embed,
                    view=None
                )

            except discord.HTTPException:
                pass

        # ----------------------------------------------------
        # DM USER
        # ----------------------------------------------------

        try:

            await member.send(
                f"🎉 Your **{role.name}** application in "
                f"**{guild.name}** was accepted!\n\n"
                f"You have received the **{role.name}** role."
            )

        except discord.Forbidden:

            pass

        except discord.HTTPException:

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
                    f"🎉 {member.mention}, your application was "
                    f"**accepted** by {interaction.user.mention}!"
                )

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        await interaction.followup.send(
            "✅ Application accepted.",
            ephemeral=True
        )

    # ========================================================
    # DENY
    # ========================================================

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="kazmod_application_deny"
    )
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.is_staff(interaction.user):

            await interaction.response.send_message(
                "❌ Only Staff or Administrators can deny applications.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # ACKNOWLEDGE IMMEDIATELY
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild

        if guild is None:

            await interaction.followup.send(
                "❌ Server not found.",
                ephemeral=True
            )
            return

        # ----------------------------------------------------
        # FIND MEMBER
        # ----------------------------------------------------

        member = guild.get_member(
            self.applicant_id
        )

        # ----------------------------------------------------
        # UPDATE EMBED
        # ----------------------------------------------------

        if interaction.message.embeds:

            embed = interaction.message.embeds[0]

            if member:

                embed.description = (
                    f"**Applicant:** {member.mention}\n"
                    "**Status:** 🔴 DENIED\n"
                    f"**Denied by:** {interaction.user.mention}"
                )

            else:

                embed.description = (
                    f"**Applicant ID:** `{self.applicant_id}`\n"
                    "**Status:** 🔴 DENIED\n"
                    f"**Denied by:** {interaction.user.mention}"
                )

            embed.color = discord.Color.red()

            try:

                await interaction.message.edit(
                    embed=embed,
                    view=None
                )

            except discord.HTTPException:

                pass

        # ----------------------------------------------------
        # DM USER
        # ----------------------------------------------------

        if member:

            try:

                await member.send(
                    f"❌ Your application in "
                    f"**{guild.name}** was denied."
                )

            except discord.Forbidden:

                pass

            except discord.HTTPException:

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
                        f"❌ {member.mention}, your application was "
                        f"**denied** by {interaction.user.mention}."
                    )

                except discord.HTTPException:

                    pass

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        await interaction.followup.send(
            "❌ Application denied.",
            ephemeral=True
        )


# ============================================================
# COG
# ============================================================

class Tickets(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):

        # Persistent views
        self.bot.add_view(
            TicketPanelView()
        )

        self.bot.add_view(
            TicketControlView()
        )

    # --------------------------------------------------------
    # READY
    # --------------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):

        if getattr(
            self.bot,
            "ticket_panel_created",
            False
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
        # CHECK EXISTING PANEL
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
                "Select an application below to create "
                "a private ticket.\n\n"
                "🔧 **Staff Application**\n"
                "Apply to become Staff.\n\n"
                "🛡️ **Administrator Application**\n"
                "Apply to become an Administrator."
            ),
            color=discord.Color.blurple()
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
                view=TicketPanelView()
            )

            print(
                "✅ Ticket panel created."
            )

        except discord.Forbidden:

            print(
                "❌ KazMod cannot send messages in "
                "the ticket panel channel."
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
