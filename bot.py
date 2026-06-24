import discord
from discord.ext import commands
from datetime import datetime
import asyncio
import json
import os

# ══════════════════════════════════════════════════════
#   ⚔️  AFFCONQUER TICKET BOT  by @OPANKUSHFF007
# ══════════════════════════════════════════════════════

TOKEN               = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
MOD_LOG_CHANNEL_ID  = 1518884551458427032
TICKET_CATEGORY_ID  = 1518882761144926228
OPEN_TICKET_CH_ID   = 1518882852605923438

STAFF_ROLE_NAME     = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"

TICKET_DB           = "tickets.json"

PURPLE      = 0x7C3AED
DARK_PURPLE = 0x4C1D95
RED         = 0xEF4444
GREEN       = 0x22C55E

# ══════════════════════════════════════════════════════
#   DATABASE
# ══════════════════════════════════════════════════════
def load_db():
    if not os.path.exists(TICKET_DB):
        return {}
    with open(TICKET_DB, "r") as f:
        return json.load(f)

def save_db(data):
    with open(TICKET_DB, "w") as f:
        json.dump(data, f, indent=2)

def get_open_ticket(user_id):
    db = load_db()
    for t in db.get(str(user_id), []):
        if t.get("status") == "open":
            return t
    return None

def add_ticket(user_id, ticket_data):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = []
    db[uid].append(ticket_data)
    save_db(db)

def get_user_tickets(user_id):
    return load_db().get(str(user_id), [])

def close_ticket_in_db(user_id, channel_id):
    db = load_db()
    uid = str(user_id)
    if uid in db:
        for t in db[uid]:
            if t.get("channel_id") == channel_id and t.get("status") == "open":
                t["status"] = "closed"
                t["closed_at"] = datetime.utcnow().isoformat()
        save_db(db)

# ── Bot Setup ─────────────────────────────────────────
intents = discord.Intents.default()
intents.members         = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════════════
#   MODALS
# ══════════════════════════════════════════════════════
class MCHelpModal(discord.ui.Modal, title="⛏️ Minecraft Help"):
    mc_username = discord.ui.TextInput(label="Your Minecraft Username", placeholder="e.g. Steve123", required=True, max_length=50)
    issue       = discord.ui.TextInput(label="Describe Your Issue", style=discord.TextStyle.paragraph, placeholder="Explain in detail...", required=True, max_length=1000)
    server_name = discord.ui.TextInput(label="Which SMP / Server?", placeholder="e.g. AFFCONQUER SMP", required=True, max_length=100)
    urgency     = discord.ui.TextInput(label="Urgency (ASAP / Today / No Rush)", placeholder="e.g. ASAP", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "⛏️ MC Help", GREEN, {
            "MC Username" : self.mc_username.value,
            "Issue"       : self.issue.value,
            "SMP / Server": self.server_name.value,
            "Urgency"     : self.urgency.value,
        })

class DiscordHelpModal(discord.ui.Modal, title="💬 Discord Help"):
    discord_tag = discord.ui.TextInput(label="Your Discord Username", placeholder="e.g. kushff007", required=True, max_length=100)
    issue       = discord.ui.TextInput(label="Describe Your Issue", style=discord.TextStyle.paragraph, placeholder="Explain in detail...", required=True, max_length=1000)
    channel     = discord.ui.TextInput(label="Which Channel / Feature?", placeholder="e.g. #general-chat, roles...", required=False, max_length=100)
    urgency     = discord.ui.TextInput(label="Urgency (ASAP / Today / No Rush)", placeholder="e.g. Today", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "💬 Discord Help", PURPLE, {
            "Discord Username" : self.discord_tag.value,
            "Issue"            : self.issue.value,
            "Channel / Feature": self.channel.value or "Not specified",
            "Urgency"          : self.urgency.value,
        })

class SOSModal(discord.ui.Modal, title="🆘 SOS Emergency"):
    your_name = discord.ui.TextInput(label="Your Username (MC or Discord)", placeholder="e.g. kushff007", required=True, max_length=100)
    emergency = discord.ui.TextInput(label="What Is the Emergency?", style=discord.TextStyle.paragraph, placeholder="Describe fast and clearly...", required=True, max_length=1000)
    proof     = discord.ui.TextInput(label="Proof / Evidence (link or describe)", placeholder="screenshot link, video...", required=False, max_length=500)
    accused   = discord.ui.TextInput(label="Who Is Involved?", placeholder="e.g. griefer username", required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "🆘 SOS Emergency", RED, {
            "Reporter" : self.your_name.value,
            "Emergency": self.emergency.value,
            "Proof"    : self.proof.value or "None provided",
            "Involved" : self.accused.value or "Not specified",
        })

# ══════════════════════════════════════════════════════
#   CREATE TICKET
# ══════════════════════════════════════════════════════
async def create_ticket(interaction, ticket_type, color, fields):
    await interaction.response.defer(ephemeral=True)
    guild  = interaction.guild
    member = interaction.user

    existing = get_open_ticket(member.id)
    if existing:
        ch = guild.get_channel(existing["channel_id"])
        ch_mention = ch.mention if ch else f"channel ID {existing['channel_id']}"
        await interaction.followup.send(
            f"⚠️ You already have an open ticket: {ch_mention}\nClose it first before opening a new one.",
            ephemeral=True
        )
        return

    staff_role  = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
    safe_name   = member.display_name.lower().replace(" ", "-")[:20]
    type_prefix = ticket_type.split()[1].lower()
    ch_name     = f"🎫│{type_prefix}-{safe_name}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member:             discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me:           discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

    category  = guild.get_channel(TICKET_CATEGORY_ID)
    ticket_ch = await guild.create_text_channel(name=ch_name, category=category, overwrites=overwrites,
        topic=f"Ticket by {member} | {ticket_type} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")

    add_ticket(member.id, {
        "channel_id": ticket_ch.id,
        "type"      : ticket_type,
        "opened_at" : datetime.utcnow().isoformat(),
        "closed_at" : None,
        "status"    : "open",
        "fields"    : fields,
        "user_tag"  : str(member),
    })

    embed = discord.Embed(
        title       = f"{ticket_type} Ticket",
        description = (
            f"Welcome {member.mention}!\n"
            f"Staff will be with you shortly. **Do not ping staff repeatedly.**\n\n"
            f"```ansi\n\u001b[1;35m⚔️  AFFCONQUER Support\u001b[0m\n```"
        ),
        color     = color,
        timestamp = datetime.utcnow()
    )
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    for k, v in fields.items():
        embed.add_field(name=k, value=f"```{v}```", inline=False)
    embed.set_footer(text="⚔️ AFFCONQUER  •  Use button below to close", icon_url=guild.icon.url if guild.icon else None)

    await ticket_ch.send(
        content=f"{member.mention} {staff_role.mention if staff_role else ''}",
        embed=embed,
        view=CloseTicketView(member.id)
    )

    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(title="🎫 New Ticket Opened", color=color, timestamp=datetime.utcnow())
        log_embed.add_field(name="User",    value=member.mention,    inline=True)
        log_embed.add_field(name="Type",    value=ticket_type,        inline=True)
        log_embed.add_field(name="Channel", value=ticket_ch.mention,  inline=True)
        log_embed.set_footer(text=f"User ID: {member.id}")
        await log_ch.send(embed=log_embed)

    await interaction.followup.send(f"✅ Ticket created: {ticket_ch.mention}", ephemeral=True)
    print(f"[TICKET] {member} opened {ticket_type} → {ticket_ch.name}")

# ══════════════════════════════════════════════════════
#   CLOSE BUTTON
# ══════════════════════════════════════════════════════
class CloseTicketView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        guild      = interaction.guild
        member     = interaction.user
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        is_staff   = staff_role in member.roles if staff_role else False

        if member.id != self.owner_id and not is_staff and not member.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only the ticket owner or staff can close this.", ephemeral=True)
            return

        await interaction.response.defer()
        close_embed = discord.Embed(
            title       = "🔒 Ticket Closing",
            description = f"Closed by {member.mention}\nDeleting in **5 seconds.**",
            color       = RED,
            timestamp   = datetime.utcnow()
        )
        await interaction.channel.send(embed=close_embed)
        close_ticket_in_db(self.owner_id, interaction.channel.id)

        log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            log_embed = discord.Embed(title="🔒 Ticket Closed", color=RED, timestamp=datetime.utcnow())
            log_embed.add_field(name="Channel",    value=interaction.channel.name, inline=True)
            log_embed.add_field(name="Closed By",  value=member.mention,           inline=True)
            log_embed.set_footer(text=f"Owner ID: {self.owner_id}")
            await log_ch.send(embed=log_embed)

        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket closed by {member}")

# ══════════════════════════════════════════════════════
#   TICKET PANEL VIEW
# ══════════════════════════════════════════════════════
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⛏️ MC Help", style=discord.ButtonStyle.success, custom_id="ticket_mc")
    async def mc_help(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(MCHelpModal())

    @discord.ui.button(label="💬 Discord Help", style=discord.ButtonStyle.primary, custom_id="ticket_discord")
    async def discord_help(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(DiscordHelpModal())

    @discord.ui.button(label="🆘 SOS", style=discord.ButtonStyle.danger, custom_id="ticket_sos")
    async def sos(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SOSModal())

# ══════════════════════════════════════════════════════
#   SETUP COMMAND
# ══════════════════════════════════════════════════════
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    channel = ctx.guild.get_channel(OPEN_TICKET_CH_ID)
    if not channel:
        await ctx.send("❌ open-a-ticket channel not found.", delete_after=5)
        return
    embed = discord.Embed(
        title       = "🎫 AFFCONQUER Support",
        description = (
            "```ansi\n\u001b[1;35m⚔️  A F F C O N Q U E R\u001b[0m\n```\n"
            "Need help? Open a ticket below.\n"
            "Spamming tickets = **permanent ban.**\n\n"
            "⛏️ **MC Help** — Minecraft issues, SMP problems\n"
            "💬 **Discord Help** — Roles, channels, server issues\n"
            "🆘 **SOS** — Emergency, hacker, griefer, abuse\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1 ticket per person.** Close yours before opening a new one."
        ),
        color     = DARK_PURPLE,
        timestamp = datetime.utcnow()
    )
    embed.set_footer(text="⚔️ AFFCONQUER  •  The grind never stops",
                     icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    await channel.send(embed=embed, view=TicketPanelView())
    await ctx.message.delete()
    print(f"[SETUP] Ticket panel sent.")

# ══════════════════════════════════════════════════════
#   /info  SLASH COMMAND  (py-cord style)
# ══════════════════════════════════════════════════════
@bot.slash_command(name="info", description="[DEV] View past tickets of a user")
@commands.has_permissions(manage_guild=True)
async def info_cmd(ctx, username: str):
    await ctx.defer(ephemeral=True)
    guild  = ctx.guild
    member = None

    if username.isdigit():
        member = guild.get_member(int(username))
    if not member:
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower() or m.display_name.lower() == username.lower(),
            guild.members
        )
    if not member:
        await ctx.respond(f"❌ User `{username}` not found.", ephemeral=True)
        return

    tickets = get_user_tickets(member.id)
    if not tickets:
        await ctx.respond(f"📭 No ticket history for **{member.display_name}**.", ephemeral=True)
        return

    embed = discord.Embed(
        title       = f"🎫 Ticket History — {member.display_name}",
        description = f"Total tickets: **{len(tickets)}**",
        color       = PURPLE,
        timestamp   = datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    for i, t in enumerate(tickets[-10:], 1):
        icon   = "🟢" if t["status"] == "open" else "🔴"
        opened = t["opened_at"][:10]
        closed = t.get("closed_at") or "—"
        if closed != "—":
            closed = closed[:10]
        embed.add_field(name=f"{icon} #{i} — {t['type']}", value=f"Opened: `{opened}` | Closed: `{closed}`", inline=False)
    embed.set_footer(text=f"User ID: {member.id}  •  Last 10 tickets")
    await ctx.respond(embed=embed, ephemeral=True)

# ══════════════════════════════════════════════════════
#   ON READY
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(CloseTicketView(owner_id=0))
    print(f"\n  ⚔️  AFFCONQUER Ticket Bot online  |  {bot.user}")
    print(f"  👑  Servers: {len(bot.guilds)}")
    print(f"  🎫  Ready.\n")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="tickets 🎫 | AFFCONQUER")
    )

# ══════════════════════════════════════════════════════
#   RUN
# ══════════════════════════════════════════════════════
bot.run(TOKEN)
