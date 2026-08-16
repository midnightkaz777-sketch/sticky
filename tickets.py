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
# TICKET SELECT
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
            return

        # ====================================================
        # CATEGORY
        # ====================================================

        category = guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            await interaction.response.send_message(
                "❌ Ticket category was not found.",
                ephemeral=True
            )
            return

        # ====================================================
        # EXISTING TICKET
        # ====================================================

        for channel in guild.text_channels:

            if channel.topic == f"ticket_owner:{member.id}":

                await interaction.response.send_message(
                    f"❌ You already have a ticket: {channel.mention}",
                    ephemeral=True
                )

                return

        # ====================================================
        # ROLES
        # ====================================================

        staff_role = guild.get_role(STAFF_ROLE_ID)

        if staff_role is None:

            await interaction.response.send_message(
                "❌ Staff role was not found.",
                ephemeral=True
            )

            return

        ticket_info = TICKET_TYPES[ticket_type]

        # ====================================================
        # PERMISSIONS
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
                    read_message_history=True
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True
                )
        }

        # ====================================================
        # CREATE CHANNEL
        # ====================================================

        try:

            channel = await guild.create_text_channel(

                name=f"{ticket_type}-{member.name}",

                category=category,

                topic=f"ticket_owner:{member.id}",

                overwrites=overwrites
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I don't have permission to create ticket channels.",
                ephemeral=True
            )

            return

        # ====================================================
        # TICKET EMBED
        # ====================================================

        embed = discord.Embed(

            title=f"{ticket_info['emoji']} {ticket_info['name']}",

            description=(
                f"Welcome {member.mention}!\n\n"

                f"**Application:** {ticket_info['name']}\n"
                f"**Applicant:** {member.mention}\n\n"

                "Please explain why you would be a good "
                f"{ticket_info['name'].replace(' Application', '')}.\n\n"

                "A Staff member will review your application."
            ),

            color=discord.Color.blurple()
        )

        await channel.send(

            content=member.mention,

            embed=embed,

            view=TicketControlView()
        )

        # ====================================================
        # LOG
        # ====================================================

        log_channel = guild.get_channel(
            TICKET_LOG_CHANNEL_ID
        )

        if log_channel:

            log_embed = discord.Embed(

                title="📋 New Staff Application",

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

            await log_channel.send(

                embed=log_embed,

                view=ApplicationDecisionView(

                    applicant_id=member.id,

                    role_id=ticket_info["role_id"],

                    ticket_channel_id=channel.id
                )
            )

        await interaction.response.send_message(

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

        self.add_item(TicketSelect())


# ============================================================
# TICKET CONTROL
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

        staff_role = interaction.guild.get_role(
            STAFF_ROLE_ID
        )

        if staff_role is None:

            await interaction.response.send_message(
                "❌ Staff role was not found.",
                ephemeral=True
            )

            return

        if staff_role not in interaction.user.roles:

            await interaction.response.send_message(
                "❌ Only Staff can close tickets.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔒 Closing ticket...",
            ephemeral=True
        )

        await interaction.channel.delete()


# ============================================================
# APPLICATION DECISION
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

    def is_staff(self, member):

        staff_role = member.guild.get_role(
            STAFF_ROLE_ID
        )

        return (
            staff_role is not None
            and staff_role in member.roles
        )

    # ========================================================
    # ACCEPT
    # ========================================================

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.is_staff(interaction.user):

            await interaction.response.send_message(
                "❌ Only Staff can accept applications.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            self.applicant_id
        )

        role = interaction.guild.get_role(
            self.role_id
        )

        if member is None:

            await interaction.response.send_message(
                "❌ Applicant could not be found.",
                ephemeral=True
            )

            return

        if role is None:

            await interaction.response.send_message(
                "❌ Role could not be found.",
                ephemeral=True
            )

            return

        try:

            await member.add_roles(
                role,
                reason="Staff application accepted"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ I cannot give this role. "
                "Move the bot's role above the role "
                "it is trying to give.",
                ephemeral=True
            )

            return

        # ====================================================
        # UPDATE LOG
        # ====================================================

        embed = interaction.message.embeds[0]

        embed.description = (

            f"**Applicant:** {member.mention}\n"
            "**Status:** 🟢 ACCEPTED\n"
            f"**Approved by:** {interaction.user.mention}\n"
            f"**Role:** {role.mention}"
        )

        embed.color = discord.Color.green()

        await interaction.message.edit(
            embed=embed,
            view=None
        )

        # ====================================================
        # DM
        # ====================================================

        try:

            await member.send(

                f"🎉 Your **{role.name}** application in "
                f"**{interaction.guild.name}** was accepted!\n\n"

                f"You have received the **{role.name}** role."
            )

        except discord.Forbidden:
            pass

        # ====================================================
        # TICKET
        # ====================================================

        ticket_channel = interaction.guild.get_channel(
            self.ticket_channel_id
        )

        if ticket_channel:

            await ticket_channel.send(

                f"🎉 {member.mention}, your application was "
                f"**accepted** by {interaction.user.mention}!"
            )

        await interaction.response.send_message(
            "✅ Application accepted.",
            ephemeral=True
        )

    # ========================================================
    # DENY
    # ========================================================

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.is_staff(interaction.user):

            await interaction.response.send_message(
                "❌ Only Staff can deny applications.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            self.applicant_id
        )

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

        await interaction.message.edit(
            embed=embed,
            view=None
        )

        if member:

            try:

                await member.send(

                    f"❌ Your application in "
                    f"**{interaction.guild.name}** was denied."
                )

            except discord.Forbidden:
                pass

            ticket_channel = interaction.guild.get_channel(
                self.ticket_channel_id
            )

            if ticket_channel:

                await ticket_channel.send(

                    f"❌ {member.mention}, your application was "
                    f"**denied** by {interaction.user.mention}."
                )

        await interaction.response.send_message(
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

        self.bot.add_view(
            TicketPanelView()
        )

        self.bot.add_view(
            TicketControlView()
        )

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
    # CREATE PANEL ONCE
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

        await channel.send(

            embed=embed,

            view=TicketPanelView()
        )

        print(
            "✅ Ticket panel created."
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Tickets(bot)
    )