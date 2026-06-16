import os
import discord
from discord.ext import commands

# ----------------- TEXTS -----------------
TOS_TEXT = """
📜 TERMS OF SERVICE

1. By using the application system, you agree to follow server rules.
2. You must provide accurate Minecraft username information.
3. Spamming or abusing the application system is not allowed.
4. Staff decisions (accept/deny) are final.
5. Your data (username + guild choice) is stored for moderation purposes.
6. Misuse may result in denial or blacklist.

Last updated: 2026-06-16
"""

PRIVACY_TEXT = """
🔐 PRIVACY POLICY

We collect:
- Discord User ID
- Minecraft username
- Selected guild
- Application decisions (accepted/denied)

We use this data only for:
- Verification
- Role assignment
- Moderation logging

We do not sell or share your data externally.

Last updated: 2026-06-16
"""

# ----------------- INTENTS -----------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- CONFIG -----------------
GUILD_ID = 1516146879967002724

STAFF_CHANNEL_ID = 1516159145869574265
LOG_CHANNEL_ID = 1516159164274180268
STAFF_ROLE_ID = 1516156178395172985

GUILD_ROLES = {
    "TDbD": 1516166981550866644,
    "SELK": 1516167002828570764,
    "GLN": 1516167020847042580
}

# ----------------- MODAL -----------------
class UsernameModal(discord.ui.Modal, title="Minecraft Verification"):

    mc_username = discord.ui.TextInput(
        label="Minecraft Username",
        required=True,
        max_length=16
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Now select your guild:",
            view=GuildSelectView(self.mc_username.value),
            ephemeral=True
        )

# ----------------- GUILD SELECT -----------------
class GuildSelect(discord.ui.Select):

    def __init__(self, username):
        self.username = username

        options = [
            discord.SelectOption(label="TDbD"),
            discord.SelectOption(label="SELK"),
            discord.SelectOption(label="GLN")
        ]

        super().__init__(
            placeholder="Choose your guild",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        guild_name = self.values[0]
        member = interaction.user

        staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)

        embed = discord.Embed(
            title="📥 New Application",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Minecraft Name", value=self.username, inline=False)
        embed.add_field(name="Guild", value=guild_name, inline=False)

        await staff_channel.send(
            content=f"<@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=ReviewView(member.id, self.username, guild_name)
        )

        await interaction.response.send_message(
            "Application submitted successfully!",
            ephemeral=True
        )

class GuildSelectView(discord.ui.View):
    def __init__(self, username):
        super().__init__(timeout=300)
        self.add_item(GuildSelect(username))

# ----------------- APPLY PANEL -----------------
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 Apply", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UsernameModal())

    @discord.ui.button(label="📜 ToS", style=discord.ButtonStyle.blurple)
    async def tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Terms of Service",
            description=TOS_TEXT,
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔐 Privacy", style=discord.ButtonStyle.gray)
    async def privacy(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔐 Privacy Policy",
            description=PRIVACY_TEXT,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------- REVIEW SYSTEM -----------------
class ReviewView(discord.ui.View):
    def __init__(self, member_id, mc_name, guild_name):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.mc_name = mc_name
        self.guild_name = guild_name

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        member = interaction.guild.get_member(self.member_id)
        role = interaction.guild.get_role(GUILD_ROLES[self.guild_name])
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if member and role:
            await member.edit(nick=self.mc_name)
            await member.add_roles(role)

            try:
                await member.send(
                    embed=discord.Embed(
                        title="✅ Application Accepted",
                        description=f"You were accepted into **{self.guild_name}**",
                        color=discord.Color.green()
                    )
                )
            except discord.Forbidden:
                pass

        if log_channel:
            embed = discord.Embed(
                title="✅ Accepted",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=member.mention if member else "Unknown")
            embed.add_field(name="MC Name", value=self.mc_name)
            embed.add_field(name="Guild", value=self.guild_name)

            await log_channel.send(embed=embed)

        await interaction.message.delete()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        member = interaction.guild.get_member(self.member_id)
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if member:
            try:
                await member.send(
                    embed=discord.Embed(
                        title="❌ Application Denied",
                        description="Your application was denied.",
                        color=discord.Color.red()
                    )
                )
            except discord.Forbidden:
                pass

        if log_channel:
            embed = discord.Embed(
                title="❌ Denied",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=f"<@{self.member_id}>")
            embed.add_field(name="MC Name", value=self.mc_name)
            embed.add_field(name="Guild", value=self.guild_name)

            await log_channel.send(embed=embed)

        await interaction.message.delete()

# ----------------- SETUP COMMAND -----------------
@bot.tree.command(name="setup_application", description="Create verification panel")
async def setup_application(interaction: discord.Interaction):

    staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

    if not any(role.id == STAFF_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🛡️ Verification Center",
        description=(
            "Welcome to the verification system.\n\n"
            "Click **Apply** to start your application.\n"
            "Read ToS and Privacy before continuing."
        ),
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    embed.set_author(
        name="Verification System",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    embed.set_thumbnail(
        url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    embed.set_footer(text="Secure system • All actions are logged")

    await interaction.channel.send(embed=embed, view=ApplyView())
    await interaction.response.send_message("Panel created!", ephemeral=True)

# ----------------- READY EVENT -----------------
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")

# ----------------- RUN BOT -----------------
bot.run(os.getenv("DISCORD_TOKEN"))
