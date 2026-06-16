import os
import discord
from discord.ext import commands
import asyncio
import itertools
import json

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
STAFF_ROLE_ID = 1516487564473798806

GUILD_ROLES = {
    "TDbD": 1516166981550866644,
    "SELK": 1516167002828570764,
    "GLN": 1516167020847042580
}

# stats["app_count"]
DATA_FILE = "stats.json"
last_activity = "idle"

def load_stats():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "app_count": 0
        }

stats = load_stats()
stats.setdefault("applications", {})

def save_stats():
    with open(DATA_FILE, "w") as f:
        json.dump(stats, f)

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
class GuildSelectView(discord.ui.View):
    def __init__(self, username):
        super().__init__(timeout=300)
        self.add_item(GuildSelect(username))

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

    try:
        print("🔥 Select clicked")

        app_id = str(stats["app_count"])
        stats["app_count"] += 1

        print("App ID:", app_id)

        guild_name = self.values[0]
        print("Guild:", guild_name)

        member = interaction.user
        print("User:", member)

        staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)
        print("Staff channel:", staff_channel)

        if staff_channel is None:
            print("❌ Staff channel is NONE (wrong ID or missing access)")

        embed = discord.Embed(
            title=f"📥 New Application #{app_id}",
            color=discord.Color.orange()
        )

        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="MC Name", value=self.username)
        embed.add_field(name="Guild", value=guild_name)

        await staff_channel.send(embed=embed)

        await interaction.response.send_message(
            "Application submitted successfully!",
            ephemeral=True
        )

        print("✅ Application sent successfully")

    except Exception as e:
        print("❌ ERROR IN SELECT CALLBACK:")
        print(e)

        try:
            await interaction.response.send_message(
                "Something broke. Check bot console.",
                ephemeral=True
            )
        except:
            pass
# ----------------- APPLY PANEL -----------------
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🚀 Apply",
        style=discord.ButtonStyle.green,
        custom_id="apply_button"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UsernameModal())

    @discord.ui.button(
        label="📜 ToS",
        style=discord.ButtonStyle.blurple,
        custom_id="tos_button"
    )
    async def tos(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Terms of Service",
            description=TOS_TEXT,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="🔐 Privacy",
        style=discord.ButtonStyle.gray,
        custom_id="privacy_button"
    )
    async def privacy(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔐 Privacy Policy",
            description=PRIVACY_TEXT,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ----------------- REVIEW SYSTEM -----------------
class AppActionView(discord.ui.View):
    def __init__(self, app_id: str):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="accept_button"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = stats["applications"].get(self.app_id)

        if not data:
            await interaction.response.send_message("Application not found.", ephemeral=True)
            return

        member = interaction.guild.get_member(data["user_id"])
        role = interaction.guild.get_role(GUILD_ROLES[data["guild"]])
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if member and role:
            await member.edit(nick=data["mc_name"])
            await member.add_roles(role)

            try:
                await member.send(
                    embed=discord.Embed(
                        title="✅ Application Accepted",
                        description=f"You were accepted into **{data['guild']}**",
                        color=discord.Color.green()
                    )
                )
            except:
                pass

        if log_channel:
            embed = discord.Embed(
                title=f"✅ Accepted #{self.app_id}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=member.mention if member else "Unknown")
            embed.add_field(name="MC Name", value=data["mc_name"])
            embed.add_field(name="Guild", value=data["guild"])

            await log_channel.send(embed=embed)

        await interaction.message.delete()

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.red,
        custom_id="deny_button"
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = stats["applications"].get(self.app_id)

        if not data:
            await interaction.response.send_message("Application not found.", ephemeral=True)
            return

        member = interaction.guild.get_member(data["user_id"])
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
            except:
                pass

        if log_channel:
            embed = discord.Embed(
                title=f"❌ Denied #{self.app_id}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=f"<@{data['user_id']}>")
            embed.add_field(name="MC Name", value=data["mc_name"])
            embed.add_field(name="Guild", value=data["guild"])

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

    # register ALL possible persistent views
    bot.add_view(ApplyView())

    print("Views re-registered")

    # 🧠 recovery scan
    for app_id, data in stats.get("applications", {}).items():
        print(f"Loaded application #{app_id} for {data['mc_name']}")
    while True:

        # 1) Apps counter status
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{stats['app_count']} applications"
            )
        )
        await asyncio.sleep(30)

        # 2) General system status
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="grinding bat cave"
            )
        )
        await asyncio.sleep(30)

        # 3) Guild management
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="join tdbd"
            )
        )
        await asyncio.sleep(30)

        # 4) Staff activity vibe
        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="beating Anathema"
            )
        )
        await asyncio.sleep(30)

        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="lootrunning for nothing"
            )
        )
        await asyncio.sleep(30)


# ----------------- RUN BOT -----------------
bot.run(os.getenv("DISCORD_TOKEN"))
