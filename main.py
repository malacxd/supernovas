import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

STAFF_CHANNEL_ID = 1516159145869574265
LOG_CHANNEL_ID = 1516159164274180268
STAFF_ROLE_ID = 1516156178395172985

GUILD_ROLES = {
    "TDbD": 1516166981550866644,
    "SELK": 1516167002828570764,
    "GLN": 1516167020847042580
}


# ---------- UI ELEMENTS ----------

class UsernameModal(discord.ui.Modal, title="Guild Application"):
    mc_username = discord.ui.TextInput(
        label="Minecraft Username",
        required=True,
        max_length=16
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Select your guild:",
            view=GuildSelectView(self.mc_username.value),
            ephemeral=True
        )


class GuildSelect(discord.ui.Select):
    def __init__(self, username):
        self.username = username

        options = [
            discord.SelectOption(label="TDbD"),
            discord.SelectOption(label="SELK"),
            discord.SelectOption(label="GLN")
        ]

        super().__init__(placeholder="Choose your guild", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild_name = self.values[0]
        member = interaction.user

        staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)

        embed = discord.Embed(title="📥 New Verification", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Minecraft Name", value=self.username, inline=False)
        embed.add_field(name="Guild", value=guild_name, inline=False)

        await staff_channel.send(
            content=f"<@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=ReviewView(member.id, self.username, guild_name)
        )

        await interaction.response.send_message("Submitted!", ephemeral=True)


class GuildSelectView(discord.ui.View):
    def __init__(self, username):
        super().__init__(timeout=300)
        self.add_item(GuildSelect(username))


class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UsernameModal())


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

        if member:
            await member.edit(nick=self.mc_name)
            await member.add_roles(role)

        await interaction.message.delete()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()


# ---------- EVENTS ----------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ---------- START BOT ----------

bot.run(os.getenv("DISCORD_TOKEN"))
