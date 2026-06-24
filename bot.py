import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import asyncio
import json
import os

# ══════════════════════════════════════════════════════
#   ⚔️  AFFCONQUER TICKET BOT  by @OPANKUSHFF007
# ══════════════════════════════════════════════════════

TOKEN              = os.getenv("DISCORD_TOKEN", "")
MOD_LOG_CHANNEL_ID = 1518884551458427032
TICKET_CATEGORY_ID = 1518882761144926228
OPEN_TICKET_CH_ID  = 1518882852605923438
STAFF_ROLE_NAME    = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"
TICKET_DB          = "tickets.json"

PURPLE      = 0x7C3AED
DARK_PURPLE = 0x4C1D95
RED         = 0xEF4444
GREEN       = 0x22C55E

# ══════════════════════════════════════════════════════
#   DATABASE SYSTEM
# ══════════════════════════════════════════════════════
def load_db():
    if not os.path.exists(TICKET_DB):
        return {}
    with open(TICKET_DB, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_db(data):
    with open(TICKET_DB, "w") as f:
        json.dump(data, f, indent=2)

def get_open_ticket(user_id):
    for t in load_db().get(str(user_id), []):
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
                t["closed_at"] = datetime.now(timezone.utc).isoformat()
        save_db(db)

# ── Bot Setup ─────────────────────────────────────────
intents = discord.Intents.default()
intents.members         = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════════════
#   DYNAMIC CUSTOM MODALS
# ══════════════════════════════════════════════════════
class MCHelpModal(discord.ui.Modal, title="⛏️ Minecraft Help"):
    mc_username = discord.ui.TextInput(label="Your Minecraft Username", placeholder="e.g. Steve123", max_length=50)
    issue       = discord.ui.TextInput(label="Describe Your Issue", style=discord.TextStyle.paragraph, placeholder="Explain in detail...", max_length=1000)
    server_name = discord.ui.TextInput(label="Which SMP / Server?", placeholder="e.g. AFFCONQUER SMP", max_length=100)
    urgency     = discord.ui.TextInput(label="Urgency (ASAP / Today / No Rush)", placeholder="e.g. ASAP", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "⛏️ MC Help", GREEN, {
            "MC Username" : self.mc_username.value,
            "Issue"       : self.issue.value,
            "SMP / Server": self.server_name.value,
            "Urgency"     : self.urgency.value,
        })

class DiscordHelpModal(discord.ui.Modal, title="💬 Discord Help"):
    discord_tag = discord.ui.TextInput(label="Your Discord Username", placeholder="e.g. kushff007", max_length=100)
    issue       = discord.ui.TextInput(label="Describe Your Issue", style=discord.TextStyle.paragraph, placeholder="Explain in detail...", max_length=1000)
    channel     = discord.ui.TextInput(label="Which Channel / Feature?", placeholder="e.g. #general-chat, roles...", required=False, max_length=100)
    urgency     = discord.ui.TextInput(label="Urgency (ASAP / Today / No Rush)", placeholder="e.g. Today", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "💬 Discord Help", PURPLE, {
            "Discord Username" : self.discord_tag.value,
            "Issue"            : self.issue.value,
            "Channel / Feature": self.channel.value or "Not specified",
            "Urgency"          : self.urgency.value,
        })

class SOSModal(discord.ui.Modal, title="🆘 SOS Emergency"):
    your_name = discord.ui.TextInput(label="Your Username (MC or Discord)", placeholder="e.g. kushff007", max_length=100)
    emergency = discord.ui.TextInput(label="What Is the Emergency?", style=discord.TextStyle.paragraph, placeholder="Describe fast and clearly...", max_length=1000)
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
#   CREATE TICKET FUNCTION (WITH AUTO TAGGING)
# ══════════════════════════════════════════════════════
async def create_ticket(interaction, ticket_type, color, fields):
    await interaction.response.defer(ephemeral=True)
    guild  = interaction.guild
    member = interaction.user

    # Anti-spam: check if already has an open ticket
    existing = get_open_ticket(member.id)
    if existing:
        ch = guild.get_channel(existing["channel_id"])
        mention = ch.mention if ch else f"channel {existing['channel_id']}"
        await interaction.followup.send(f"⚠️ You already have an open ticket: {mention}\nClose it first.", ephemeral=True)
        return

    staff_role  = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
    safe_name   = member.display_name.lower().replace(" ", "-")[:20]
    type_prefix = ticket_type.split()[1].lower()
    ch_name     = f"ticket-{type_prefix}-{safe_name}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member:             discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
        guild.me:           discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True, attach_files=True, embed_links=True)

    category  = guild.get_channel(TICKET_CATEGORY_ID)
    ticket_ch = await guild.create_text_channel(
        name=ch_name, category=category, overwrites=overwrites,
        topic=f"Ticket by {member} | {ticket_type} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
    )

    add_ticket(member.id, {
        "channel_id": ticket_ch.id,
        "type"      : ticket_type,
        "opened_at" : datetime.now(timezone.utc).isoformat(),
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
        color=color, timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url if member.display_avatar else None)
    for k, v in fields.items():
        embed.add_field(name=k, value=f"```\n{v}\n```", inline=False)
    embed.set_footer(text="⚔️ AFFCONQUER  •  Use button below to close",
                     icon_url=guild.icon.url if guild.icon else None)

    # Automatically mentions/tags the User and Staff Role upon creation
    tag_content = f"{member.mention} {staff_role.mention if staff_role else ''}"
    await ticket_ch.send(
        content=tag_content,
        embed=embed,
        view=CloseTicketView()
    )

    # Log inside mod logs channel
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(title="🎫 New Ticket Opened", color=color, timestamp=datetime.now(timezone.utc))
        log_embed.add_field(name="User",    value=member.mention,   inline=True)
        log_embed.add_field(name="Type",    value=ticket_type,       inline=True)
        log_embed.add_field(name="Channel", value=ticket_ch.mention, inline=True)
        log_embed.set_footer(text=f"User ID: {member.id}")
        await log_ch.send(embed=log_embed)

    await interaction.followup.send(f"✅ Ticket created: {ticket_ch.mention}", ephemeral=True)
    print(f"[TICKET] {member} opened {ticket_type} → {ticket_ch.name}")

# ══════════════════════════════════════════════════════
#   CLOSE TICKET CONTROL PANEL
# ══════════════════════════════════════════════════════
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild      = interaction.guild
        member     = interaction.user
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        is_staff   = staff_role in member.roles if staff_role else False

        # Dynamic validation via database checks to safely allow owner or management to close
        db = load_db()
        owner_id = None
        for uid, tickets in db.items():
            for t in tickets:
                if t.get("channel_id") == interaction.channel_id and t.get("status") == "open":
                    owner_id = int(uid)
                    break

        if owner_id and member.id != owner_id and not is_staff and not interaction.permissions.manage_channels:
            await interaction.response.send_message("❌ Only the ticket owner or staff can close this.", ephemeral=True)
            return

        await interaction.response.defer()
        close_embed = discord.Embed(
            title="🔒 Ticket Closing",
            description=f"Closed by {member.mention}\nDeleting in **5 seconds.**",
            color=RED, timestamp=datetime.now(timezone.utc)
        )
        await interaction.channel.send(embed=close_embed)
        
        if owner_id:
            close_ticket_in_db(owner_id, interaction.channel.id)

        log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            log_embed = discord.Embed(title="🔒 Ticket Closed", color=RED, timestamp=datetime.now(timezone.utc))
            log_embed.add_field(name="Channel",   value=interaction.channel.name, inline=True)
            log_embed.add_field(name="Closed By", value=member.mention,           inline=True)
            if owner_id:
                log_embed.set_footer(text=f"Owner ID: {owner_id}")
            await log_ch.send(embed=log_embed)

        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {member}")
        except discord.NotFound:
            pass

# ══════════════════════════════════════════════════════
#   TICKET SELECTION PANEL
# ══════════════════════════════════════════════════════
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⛏️ MC Help", style=discord.ButtonStyle.success, custom_id="ticket_mc")
    async def mc_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MCHelpModal())

    @discord.ui.button(label="💬 Discord Help", style=discord.ButtonStyle.primary, custom_id="ticket_discord")
    async def discord_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DiscordHelpModal())

    @discord.ui.button(label="🆘 SOS", style=discord.ButtonStyle.danger, custom_id="ticket_sos")
    async def sos(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SOSModal())

# ══════════════════════════════════════════════════════
#   !setup_tickets COMMAND SYSTEM
# ══════════════════════════════════════════════════════
@bot.command(name="setup_tickets")
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    channel = ctx.guild.get_channel(OPEN_TICKET_CH_ID)
    if not channel:
        await ctx.send("❌ open-a-ticket channel not found.", delete_after=5)
        return
        
    embed = discord.Embed(
        title="🎫 AFFCONQUER Support",
        description=(
            "```ansi\n\u001b[1;35m⚔️  A F F C O N Q U E R\u001b[0m\n```\n"
            "Need help? Open a ticket below.\n"
            "Spamming tickets = **permanent ban.**\n\n"
            "⛏️ **MC Help** — Minecraft issues, SMP problems\n"
            "💬 **Discord Help** — Roles, channels, server issues\n"
            "🆘 **SOS** — Emergency, hacker, griefer, abuse\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1 ticket per person.** Close yours before opening a new one."
        ),
        color=DARK_PURPLE, timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(text="⚔️ AFFCONQUER  •  The grind never stops",
                     icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
                     
    await channel.send(embed=embed, view=TicketPanelView())
    await ctx.message.delete()
    print("[SETUP] Ticket panel sent successfully.")

# ══════════════════════════════════════════════════════
#   SLASH COMMAND FOR DEV MODERATION (/info)
# ══════════════════════════════════════════════════════
@bot.tree.command(name="info", description="[DEV] View past tickets of a user")
@app_commands.checks.has_permissions(manage_guild=True)
async def info_cmd(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    guild  = interaction.guild
    member = None

    if username.isdigit():
        member = guild.get_member(int(username))
    if not member:
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower() or m.display_name.lower() == username.lower(),
            guild.members
        )
    if not member:
        await interaction.followup.send(f"❌ User `{username}` not found.", ephemeral=True)
        return

    tickets = get_user_tickets(member.id)
    if not tickets:
        await interaction.followup.send(f"📭 No ticket history for **{member.display_name}**.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🎫 Ticket History — {member.display_name}",
        description=f"Total tickets: **{len(tickets)}**",
        color=PURPLE, timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
    
    for i, t in enumerate(tickets[-10:], 1):
        icon   = "🟢" if t["status"] == "open" else "🔴"
        opened = t["opened_at"][:10]
        closed = t.get("closed_at") or "—"
        if closed != "—":
            closed = closed[:10]
        embed.add_field(name=f"{icon} #{i} — {t['type']}", value=f"Opened: `{opened}` | Closed: `{closed}`", inline=False)
        
    embed.set_footer(text=f"User ID: {member.id}  •  Last 10 tickets")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ══════════════════════════════════════════════════════
#   ON READY (PERSISTENT BUTTON REGISTRATION)
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(CloseTicketView()) # Restored correctly without structural initialization mismatch
    await bot.tree.sync()
    print(f"\n  ⚔️  AFFCONQUER Ticket Bot online  |  {bot.user}")
    print(f"  👑  Servers: {len(bot.guilds)}")
    print(f"  🎫  Ready.\n")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="tickets 🎫 | AFFCONQUER")
    )

bot.run(TOKEN)
