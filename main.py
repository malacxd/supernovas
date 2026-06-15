import discord
import os
from discord import role
from discord.ext import commands

bot.run(os.getenv("DISCORD_TOKEN"))
STAFF_CHANNEL_ID = 1516159145869574265  # your admin review channel
LOG_CHANNEL_ID = 1516159164274180268    # logs channel
STAFF_ROLE_ID = 1516156178395172985     # role to ping

# Replace these with your actual role IDs
GUILD_ROLES = {
    "TDbD": 1516166981550866644,
    "SELK": 1516167002828570764,
    "GLN": 1516167020847042580
}

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)


class UsernameModal(discord.ui.Modal, title="Guild Application"):

    mc_username = discord.ui.TextInput(
        label="Minecraft Username",
        placeholder="Enter your Minecraft username",
        required=True,
        max_length=16
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Select your guild:",
            view=GuildSelectView(str(self.mc_username)),
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
            title="📥 New Verification",
            color=discord.Color.orange()
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
            "Your application has been submitted for review!",
            ephemeral=True
        )

class GuildSelectView(discord.ui.View):

    def __init__(self, username):
        super().__init__(timeout=300)
        self.add_item(GuildSelect(username))


class ApplyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Apply",
        style=discord.ButtonStyle.green,
        emoji="📋",
        custom_id="apply_button"
    )
    async def apply_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            UsernameModal()
        )


@bot.event
async def on_ready():
    bot.add_view(ApplyView())

    guild = discord.Object(id=1516146879967002724)

    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} guild commands.")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")


@discord.app_commands.guilds(discord.Object(id=1516146879967002724))
@bot.tree.command(
    name="setup_application",
    description="Create the application panel"
)
async def setup_application(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Guild Application",
        description=(
            "Welcome!\n\n"
            "Click **Apply** below and answer the questions.\n\n"
            "Your Minecraft username will become your server nickname "
            "and you'll receive the role for your selected guild."
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(text="TDbD • SELK • GLN")

    await interaction.channel.send(
        embed=embed,
        view=ApplyView()
    )

    await interaction.response.send_message(
        "Application panel created.",
        ephemeral=True
    )

class ReviewView(discord.ui.View):
    def __init__(self, member_id: int, mc_name: str, guild_name: str):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.mc_name = mc_name
        self.guild_name = guild_name

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defuse interaction right away so it doesn't time out or show "Interaction Failed"
        await interaction.response.defer(ephemeral=True)

        member = interaction.guild.get_member(self.member_id)
        role = interaction.guild.get_role(GUILD_ROLES[self.guild_name])
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if member is None:
            await interaction.followup.send("Member not found in server.", ephemeral=True)
            return

        # Handle Nickname
        try:
            await member.edit(nick=self.mc_name)
        except Exception as e:
            await interaction.followup.send(f"Nickname failed: {e}", ephemeral=True)
            return
        
        # Handle Role Assignment
        try:
            if role is None:
                await interaction.followup.send("Role not found.", ephemeral=True)
                return

            await member.add_roles(role)

        except Exception as e:
            await interaction.followup.send(f"Role failed: {e}", ephemeral=True)
            return

        # Send full log to the log channel
        if log_channel:
            embed = discord.Embed(
                title="✅ Application Accepted",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=member.mention, inline=False)
            embed.add_field(name="Minecraft Name", value=self.mc_name, inline=False)
            embed.add_field(name="Guild Assigned", value=self.guild_name, inline=False)
            embed.set_footer(text=f"Approved by {interaction.user.name}")
            
            await log_channel.send(embed=embed)

        # Delete the original application message from the staff channel
        try:
            await interaction.message.delete()
        except discord.Forbidden:
            await interaction.followup.send("Bot doesn't have permission to delete this message.", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        # Send full log to the log channel
        if log_channel:
            embed = discord.Embed(
                title="❌ Application Denied",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=f"<@{self.member_id}>", inline=False)
            embed.add_field(name="Minecraft Name", value=self.mc_name, inline=False)
            embed.add_field(name="Guild Intended", value=self.guild_name, inline=False)
            embed.set_footer(text=f"Denied by {interaction.user.name}")
            
            await log_channel.send(embed=embed)

        # Delete the original application message from the staff channel
        try:
            await interaction.message.delete()
        except discord.Forbidden:
            await interaction.followup.send("Bot doesn't have permission to delete this message.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
