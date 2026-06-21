import os
import discord
from discord.ext import commands
import asyncio
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
RAID_PANEL_CHANNEL_ID = 1516508845902397521
RAID_ROLE_ID = 1517150536615592138
ADMIN_ROLE_ID = 1516156178395172985
pending_closures = {}

GUILD_ROLES = {
    "TDbD": 1516166981550866644,
    "SELK": 1516167002828570764,
    "GLN": 1516167020847042580
}

DATA_FILE = "stats.json"
PARTY_FILE = "parties.json"
last_activity = "idle"

def is_full(party):
    return len(party["members"]) >= 4

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
        super().__init__(timeout=180)
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

        print("SELECT WORKED")
        print(self.values)

        try:
            await interaction.response.defer(ephemeral=True)

            guild_name = self.values[0]

            staff_channel = interaction.guild.get_channel(STAFF_CHANNEL_ID)

            if staff_channel is None:
                await interaction.followup.send("Staff channel not found.", ephemeral=True)
                return

            embed = discord.Embed(
                title="📥 New Application",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(name="User", value=interaction.user.mention, inline=False)
            embed.add_field(name="MC Name", value=self.username, inline=False)
            embed.add_field(name="Guild", value=guild_name, inline=False)

            await staff_channel.send(
                content=f"<@&{STAFF_ROLE_ID}>",
                embed=embed,
                view=ReviewView(
                    interaction.user.id,
                    self.username,
                    guild_name
                )
            )

            await interaction.followup.send(
                "✅ Application submitted successfully!",
                ephemeral=True
            )

        except Exception as e:
            print("❌ GuildSelect crash:", e)
# ----------------- APPLY PANEL -----------------
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 Apply", style=discord.ButtonStyle.green, custom_id="apply_button")
    async def apply(self, interaction, button):
        await interaction.response.send_modal(UsernameModal())

    @discord.ui.button(label="📜 ToS", style=discord.ButtonStyle.blurple, custom_id="tos_button")
    async def tos(self, interaction, button):
        await interaction.response.send_message(
            embed=discord.Embed(title="ToS", description=TOS_TEXT),
            ephemeral=True
        )

    @discord.ui.button(label="🔐 Privacy", style=discord.ButtonStyle.gray, custom_id="privacy_button")
    async def privacy(self, interaction, button):
        await interaction.response.send_message(
            embed=discord.Embed(title="Privacy", description=PRIVACY_TEXT),
            ephemeral=True
        )

# ----------------- REVIEW SYSTEM -----------------
class ReviewView(discord.ui.View):
    def __init__(self, member_id, mc_name, guild_name):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.mc_name = mc_name
        self.guild_name = guild_name

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

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
            except:
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

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.red
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):

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
            except:
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

    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
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

# ----------------- RAID FINDER -----------------

def load_parties():
    try:
        with open(PARTY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

parties = load_parties()

def save_parties():
    with open(PARTY_FILE, "w") as f:
        json.dump(parties, f, indent=4)

class RaidFinderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ---------------- CREATE PARTY ----------------
    @discord.ui.button(
        label="⚔️ Create Party",
        style=discord.ButtonStyle.green,
        custom_id="create_party"
    )
    async def create_party(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            f"🎮 Creating a raid party...\n"
            f"⚠️ Parties automatically close after **30 minutes**.",
            view=RaidSelectView(),
            ephemeral=True
        )

    # ---------------- RAIDER ROLE TOGGLE ----------------
    @discord.ui.button(
        label="🛡️ Raider Role",
        style=discord.ButtonStyle.blurple,
        custom_id="raider_role_toggle"
    )
    async def toggle_raider(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(RAID_ROLE_ID)
        if not role:
            return await interaction.response.send_message("Role not found.", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("❌ Raider role removed.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Raider role added.", ephemeral=True)
    
class RaidSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="TCC"),
            discord.SelectOption(label="NOL"),
            discord.SelectOption(label="NOTG"),
            discord.SelectOption(label="TNA"),
            discord.SelectOption(label="WTP")
        ]

        super().__init__(
            placeholder="Select raid",
            options=options
        )

    async def callback(self, interaction):
        raid = self.values[0]

        await interaction.response.send_message(
            f"Selected {raid}. Choose your class:",
            view=ClassSelectView(raid),
            ephemeral=True
        )

class RaidSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(RaidSelect())

class ClassSelect(discord.ui.Select):
    def __init__(self, raid):
        self.raid = raid

        options = [
            discord.SelectOption(label="Warrior", emoji="🛡️"),
            discord.SelectOption(label="Archer", emoji="🏹"),
            discord.SelectOption(label="Mage", emoji="🪄"),
            discord.SelectOption(label="Shaman", emoji="🌿"),
            discord.SelectOption(label="Assassin", emoji="🗡️")
        ]

        super().__init__(
            placeholder="Select class",
            options=options
        )
    async def callback(self, interaction):

        player_class = self.values[0]

        party_id = str(len(parties) + 1)

        parties[party_id] = {
            "raid": self.raid,
            "leader": interaction.user.id,
            "members": [
                {
                    "user": interaction.user.id,
                    "class": player_class
                }
            ],
            "created_at": discord.utils.utcnow().timestamp(),
            "message_id": None,
            "notified_full": False
        }

        save_parties()

        party_channel = interaction.guild.get_channel(RAID_PANEL_CHANNEL_ID)

        embed = build_party_embed(party_id)

        msg = await party_channel.send(
            content=f"<@&{RAID_ROLE_ID}>",
            embed=build_party_embed(party_id),
            view=PartyView(),
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        parties[party_id]["message_id"] = msg.id
        save_parties()

        await interaction.response.send_message(
            "Party created!",
            ephemeral=True
        )

async def handle_party_full(guild, party_id):
    party = parties.get(party_id)
    if not party:
        return

    if len(party["members"]) < 4:
        return

    if party.get("notified_full"):
        return

    party["notified_full"] = True
    save_parties()

    channel = guild.get_channel(RAID_PANEL_CHANNEL_ID)
    if not channel:
        return

    mentions = " ".join(f"<@{m['user']}>" for m in party["members"])

    await channel.send(
        content=f"🔥 RAID PARTY FULL!\n{mentions}",
        allowed_mentions=discord.AllowedMentions(users=True)
    )

async def start_close_confirmation(interaction, party_id):

    pending_closures[party_id] = interaction.user.id

    view = ClosePartyView(party_id)

    await interaction.response.send_message(
        "⚠️ You are the leader. Closing will delete the party.\nAre you sure?",
        view=view,
        ephemeral=True
    )

class ClassSelectView(discord.ui.View):
    def __init__(self, raid):
        super().__init__(timeout=300)
        self.add_item(ClassSelect(raid))

def build_party_embed(party_id):

    party = parties[party_id]

    full = len(party["members"]) >= 4

    embed = discord.Embed(
        title=f"⚔️ Raid Party • {party['raid']} #{party_id}",
        color=discord.Color.green() if full else discord.Color.gold()
    )
    embed.add_field(
        name="👑 Leader",
        value=f"<@{party['leader']}>",
        inline=False
    )

    members = []
    for m in party["members"]:
        members.append(f"**{m['class']}** — <@{m['user']}>")

    embed.add_field(
        name=f"👥 Members ({len(party['members'])}/4)",
        value="\n".join(members),
        inline=False
    )

    # visual capacity bar
    filled = "🟩" * len(party["members"])
    empty = "⬛" * (4 - len(party["members"]))
    embed.add_field(
        name="📊 Capacity",
        value=f"{filled}{empty}",
        inline=False
    )

    # 🕒 IMPORTANT: lifetime warning
    embed.add_field(
        name="⏳ Lifetime",
        value="This party will automatically close after **15 minutes**.",
        inline=False
    )

    if full:
        embed.add_field(
            name="🔥 STATUS",
            value="**THIS PARTY IS FULL — READY TO START RAID!**",
            inline=False
        )
    else:
        embed.add_field(
            name="🟡 STATUS",
            value="Waiting for players...",
            inline=False
        )

    embed.set_footer(text="Use Join to enter • Leave to exit • Leader can close")

    return embed


class ClosePartyView(discord.ui.View):
    def __init__(self, party_id):
        super().__init__(timeout=30)
        self.party_id = party_id

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):

        party = parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("Party already closed.", ephemeral=True)

        if interaction.user.id != party["leader"]:
            return await interaction.response.send_message("Only leader can close.", ephemeral=True)

        await delete_party(self.party_id, reason="manual close")

        await interaction.response.edit_message(
            content="❌ Party closed.",
            view=None
        )

        pending_closures.pop(self.party_id, None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):

        pending_closures.pop(self.party_id, None)

        await interaction.response.edit_message(
            content="Cancelled.",
            view=None
        )

class JoinClass(discord.ui.Select):
    def __init__(self, party_id):
        self.party_id = party_id

        options = [
            discord.SelectOption(label="Warrior", emoji="🛡️"),
            discord.SelectOption(label="Archer", emoji="🏹"),
            discord.SelectOption(label="Mage", emoji="🪄"),
            discord.SelectOption(label="Shaman", emoji="🌿"),
            discord.SelectOption(label="Assassin", emoji="🗡️")
        ]

        super().__init__(placeholder="Select class", options=options)

    async def callback(self, interaction):

        party = parties.get(self.party_id)
        if not party:
            return await interaction.response.send_message("Party not found.", ephemeral=True)

        # prevent duplicate join
        if any(m["user"] == interaction.user.id for m in party["members"]):
            return await interaction.response.send_message("Already in party.", ephemeral=True)

        if len(party["members"]) >= 4:
            return await interaction.response.send_message("Party full.", ephemeral=True)

        party["members"].append({
            "user": interaction.user.id,
            "class": self.values[0]
        })

        save_parties()
        await refresh_party(interaction.guild, self.party_id)

        await handle_party_full(interaction.guild, self.party_id)

        await interaction.response.send_message("Joined party!", ephemeral=True)

class JoinClassView(discord.ui.View):
    def __init__(self, party_id):
        super().__init__(timeout=120)
        self.add_item(JoinClass(party_id))

async def refresh_party(guild, party_id):
    party = parties.get(party_id)

    if not party:
        return

    message_id = party.get("message_id")
    if not message_id:
        return

    channel = guild.get_channel(RAID_PANEL_CHANNEL_ID)
    if not channel:
        return

    try:
        msg = await channel.fetch_message(message_id)
    except:
        return

    embed = build_party_embed(party_id)

    await msg.edit(
        embed=embed,
        view=PartyView()
    )

async def party_cleanup_task():
    await bot.wait_until_ready()

    while not bot.is_closed():
        now = discord.utils.utcnow().timestamp()

        to_delete = []

        for party_id, party in list(parties.items()):

            created = party.get("created_at", now)
            age = now - created

            if age >= 1800:
                to_delete.append(party_id)

        for party_id in to_delete:
            await delete_party(party_id, reason="expired")

        await asyncio.sleep(30)

async def delete_party(party_id, reason="closed"):
    party = parties.get(party_id)
    if not party:
        return

    channel = bot.get_channel(RAID_PANEL_CHANNEL_ID)

    message_id = party.get("message_id")

    if channel and message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.delete()
        except Exception as e:
            print("Delete message failed:", e)

    # IMPORTANT: remove FIRST from memory BEFORE anything else
    parties.pop(party_id, None)
    save_parties()

    print(f"Party {party_id} deleted ({reason})")

class PartyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Join",
        style=discord.ButtonStyle.green,
        custom_id="party_join"
    )
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        party_id = None

        # find party by message_id
        for pid, party in parties.items():
            if party.get("message_id") == interaction.message.id:
                party_id = pid
                break

        if not party_id:
            return await interaction.response.send_message("Party not found.", ephemeral=True)

        party = parties[party_id]

        if any(m["user"] == interaction.user.id for m in party["members"]):
            return await interaction.response.send_message("Already in party.", ephemeral=True)

        if len(party["members"]) >= 4:
            return await interaction.response.send_message("Party is full.", ephemeral=True)

        await interaction.response.send_message(
            "Choose your class:",
            view=JoinClassView(party_id),
            ephemeral=True
        )

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
    async def leave(self, interaction, button):

        if self.party_id not in parties:
            return await interaction.response.send_message("This party is closed.", ephemeral=True)

        party = self.get_party()
        if not party:
            return await interaction.response.send_message("Party not found.", ephemeral=True)

        user_id = interaction.user.id

        is_member = any(m["user"] == user_id for m in party["members"])
        if not is_member:
            return await interaction.response.send_message("You're not in this party.", ephemeral=True)

        # 🔥 LEADER LOGIC
        if user_id == party["leader"]:
            return await start_close_confirmation(interaction, self.party_id)

        # normal member leave
        party["members"] = [
            m for m in party["members"] if m["user"] != user_id
        ]

        save_parties()
        await refresh_party(interaction.guild, self.party_id)

        await interaction.response.send_message("You left the party.", ephemeral=True)

@bot.tree.command(
    name="setup_raidfinder",
    description="Create raid finder panel",
    guild=discord.Object(id=GUILD_ID)
)
async def setup_raidfinder(interaction: discord.Interaction):

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You don't have permission.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚔️ Raid Finder",
        description=(
            "Everything you need for raids is here.\n\n"
            "⚔️ Create parties and find teammates instantly\n"
            "🛡️ Toggle Raider role to get access\n\n"
            "• Max 4 players per party\n"
            "• Auto-disbands after 30 minutes\n"
            "• Leader controls party management"
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="📌 How it works",
        value=(
            "1. Click Create Party\n"
            "2. Choose raid\n"
            "3. Select class\n"
            "4. Join others or wait for teammates"
        ),
        inline=False
    )

    embed.set_footer(text="Wynncraft Raid System")

    await interaction.channel.send(
        embed=embed,
        view=RaidFinderView()
    )

    await interaction.response.send_message(
        "Raid Finder panel created.",
        ephemeral=True
    )



# ----------------- READY EVENT -----------------

async def presence_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():

        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="grooting my slang"
            )
        )
        await asyncio.sleep(30)

        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="grinding bat cave"
            )
        )
        await asyncio.sleep(30)

        await bot.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="join tdbd"
            )
        )
        await asyncio.sleep(30)

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

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    for party_id in parties:
        bot.add_view(PartyView())

    print(f"Logged in as {bot.user}")

    # register ALL possible persistent views
    bot.add_view(ApplyView())

    print("Views re-registered")
    bot.add_view(RaidFinderView())
    bot.loop.create_task(party_cleanup_task())
    bot.loop.create_task(presence_loop())


# ----------------- RUN BOT -----------------
bot.run(os.getenv("DISCORD_TOKEN"))
