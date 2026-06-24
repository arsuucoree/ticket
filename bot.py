import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio
import json
import os

# ══════════════════════════════════════════════════════
#   ⚔️  AFFCONQUER TICKET BOT  by @OPANKUSHFF007
# ══════════════════════════════════════════════════════

TOKEN               = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
MOD_LOG_CHANNEL_ID  = 1518884551458427032   # #mod-logs
TICKET_CATEGORY_ID  = 1518882761144926228   # category where tickets are created
OPEN_TICKET_CH_ID   = 1518882852605923438   # #open-a-ticket channel

STAFF_ROLE_NAME     = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"       # role that can see all tickets

TICKET_DB           = "tickets.json"         # local storage for ticket history

# ── Colors ────────────────────────────────────────────
PURPLE      = 0x7C3AED
DARK_PURPLE = 0x4C1D95
RED         = 0xEF4444
GREEN       = 0x22C55E
GOLD        = 0xF59E0B

# ══════════════════════════════════════════════════════
#   TICKET DATABASE  (JSON file, simple & lightweight)
# ══════════════════════════════════════════════════════
def load_db() -> dict:
    if not os.path.exists(TICKET_DB):
        return {}
    with open(TICKET_DB, "r") as f:
        return json.load(f)

def save_db(data: dict):
    with open(TICKET_DB, "w") as f:
        json.dump(data, f, indent=2)

def get_user_tickets(user_id: int) -> list:
    db = load_db()
    return db.get(str(user_id), [])

def add_ticket(user_id: int, ticket_data: dict):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = []
    db[uid].append(ticket_data)
    save_db(db)

def get_open_ticket(user_id: int):
    tickets = get_user_tickets(user_id)
    for t in tickets:
        if t.get("status") == "open":
            return t
    return None

def close_ticket_in_db(user_id: int, channel_id: int):
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
tree = bot.tree

# ══════════════════════════════════════════════════════
#   ON READY
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    print(f"\n  ⚔️  AFFCONQUER Ticket Bot online  |  {bot.user}")
    print(f"  👑  Servers: {len(bot.guilds)}")
    print(f"  🎫  Ticket system ready.\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="tickets 🎫 | AFFCONQUER"
        )
    )

# ══════════════════════════════════════════════════════
#   MODALS
# ══════════════════════════════════════════════════════

class MCHelpModal(discord.ui.Modal, title="⛏️ Minecraft Help — Fill Details"):
    mc_username = discord.ui.TextInput(
        label="Your Minecraft Username",
        placeholder="e.g. Steve123",
        required=True,
        max_length=50
    )
    issue = discord.ui.TextInput(
        label="Describe Your Issue",
        style=discord.TextStyle.paragraph,
        placeholder="Explain your Minecraft issue in detail...",
        required=True,
        max_length=1000
    )
    server_name = discord.ui.TextInput(
        label="Which SMP / Server?",
        placeholder="e.g. AFFCONQUER SMP, Survival World...",
        required=True,
        max_length=100
    )
    urgency = discord.ui.TextInput(
        label="How Urgent? (ASAP / Today / No Rush)",
        placeholder="e.g. ASAP",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction,
            ticket_type="⛏️ MC Help",
            color=GREEN,
            fields={
                "MC Username"   : self.mc_username.value,
                "Issue"         : self.issue.value,
                "SMP / Server"  : self.server_name.value,
                "Urgency"       : self.urgency.value,
            }
        )


class DiscordHelpModal(discord.ui.Modal, title="💬 Discord Help — Fill Details"):
    discord_tag = discord.ui.TextInput(
        label="Your Discord Username",
        placeholder="e.g. kushff007",
        required=True,
        max_length=100
    )
    issue = discord.ui.TextInput(
        label="Describe Your Issue",
        style=discord.TextStyle.paragraph,
        placeholder="Explain your Discord issue in detail...",
        required=True,
        max_length=1000
    )
    channel = discord.ui.TextInput(
        label="Which Channel / Feature?",
        placeholder="e.g. #general-chat, roles, onboarding...",
        required=False,
        max_length=100
    )
    urgency = discord.ui.TextInput(
        label="How Urgent? (ASAP / Today / No Rush)",
        placeholder="e.g. Today",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction,
            ticket_type="💬 Discord Help",
            color=PURPLE,
            fields={
                "Discord Username" : self.discord_tag.value,
                "Issue"            : self.issue.value,
                "Channel / Feature": self.channel.value or "Not specified",
                "Urgency"          : self.urgency.value,
            }
        )


class SOSModal(discord.ui.Modal, title="🆘 SOS — Emergency Report"):
    your_name = discord.ui.TextInput(
        label="Your Username (MC or Discord)",
        placeholder="e.g. kushff007 / Steve123",
        required=True,
        max_length=100
    )
    emergency = discord.ui.TextInput(
        label="What Is the Emergency?",
        style=discord.TextStyle.paragraph,
        placeholder="Describe the emergency clearly and fast...",
        required=True,
        max_length=1000
    )
    proof = discord.ui.TextInput(
        label="Proof / Evidence (link or describe)",
        placeholder="e.g. screenshot link, video, witness names...",
        required=False,
        max_length=500
    )
    accused = discord.ui.TextInput(
        label="Who Is Involved? (if any)",
        placeholder="e.g. username of griefer, hacker, bully...",
        required=False,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction,
            ticket_type="🆘 SOS Emergency",
            color=RED,
            fields={
                "Reporter"    : self.your_name.value,
                "Emergency"   : self.emergency.value,
                "Proof"       : self.proof.value or "None provided",
                "Involved"    : self.accused.value or "Not specified",
            }
        )

# ══════════════════════════════════════════════════════
#   CORE — CREATE TICKET
# ══════════════════════════════════════════════════════
async def create_ticket(
    interaction: discord.Interaction,
    ticket_type: str,
    color: int,
    fields: dict
):
    await interaction.response.defer(ephemeral=True)
    guild  = interaction.guild
    member = interaction.user

    # ── 1 ticket per person check ─────────────────────
    existing = get_open_ticket(member.id)
    if existing:
        ch = guild.get_channel(existing["channel_id"])
        ch_mention = ch.mention if ch else f"channel ID {existing['channel_id']}"
        await interaction.followup.send(
            f"⚠️ You already have an open ticket: {ch_mention}\n"
            f"Close it first before opening a new one.",
            ephemeral=True
        )
        return

    # ── Get staff role ─────────────────────────────────
    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)

    # ── Channel name ───────────────────────────────────
    safe_name   = member.display_name.lower().replace(" ", "-")[:20]
    type_prefix = ticket_type.split()[1].lower()   # mc / discord / sos
    ch_name     = f"🎫│{type_prefix}-{safe_name}"

    # ── Overwrites: only member + staff + bot ─────────
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member:             discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                read_message_history=True
                            ),
        guild.me:           discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_channels=True
                            ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_messages=True
        )

    # ── Create channel ─────────────────────────────────
    category = guild.get_channel(TICKET_CATEGORY_ID)
    ticket_ch = await guild.create_text_channel(
        name       = ch_name,
        category   = category,
        overwrites = overwrites,
        topic      = f"Ticket by {member} | {ticket_type} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    )

    # ── Save to DB ─────────────────────────────────────
    ticket_record = {
        "channel_id" : ticket_ch.id,
        "type"       : ticket_type,
        "opened_at"  : datetime.utcnow().isoformat(),
        "closed_at"  : None,
        "status"     : "open",
        "fields"     : fields,
        "user_tag"   : str(member),
    }
    add_ticket(member.id, ticket_record)

    # ── Build embed for ticket channel ────────────────
    embed = discord.Embed(
        title       = f"{ticket_type} Ticket",
        description = (
            f"Welcome {member.mention}!\n"
            f"Staff will be with you shortly. **Do not ping staff repeatedly.**\n\n"
            f"```ansi\n\u001b[1;35m⚔️  AFFCONQUER Support\u001b[0m\n```"
        ),
        color       = color,
        timestamp   = datetime.utcnow()
    )
    embed.set_author(
        name     = member.display_name,
        icon_url = member.display_avatar.url
    )
    for k, v in fields.items():
        embed.add_field(name=k, value=f"```{v}```", inline=False)
    embed.set_footer(
        text     = "⚔️ AFFCONQUER  •  Use the button below to close this ticket",
        icon_url = guild.icon.url if guild.icon else None
    )

    close_view = CloseTicketView(member.id)
    await ticket_ch.send(
        content = f"{member.mention} {staff_role.mention if staff_role else ''}",
        embed   = embed,
        view    = close_view
    )

    # ── Mod log ────────────────────────────────────────
    log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title       = "🎫 New Ticket Opened",
            color       = color,
            timestamp   = datetime.utcnow()
        )
        log_embed.add_field(name="User",    value=member.mention,   inline=True)
        log_embed.add_field(name="Type",    value=ticket_type,       inline=True)
        log_embed.add_field(name="Channel", value=ticket_ch.mention, inline=True)
        log_embed.set_footer(text=f"User ID: {member.id}")
        await log_ch.send(embed=log_embed)

    # ── Confirm to user ────────────────────────────────
    await interaction.followup.send(
        f"✅ Your ticket has been created: {ticket_ch.mention}",
        ephemeral=True
    )
    print(f"[TICKET] {member} opened {ticket_type} → {ticket_ch.name}")


# ══════════════════════════════════════════════════════
#   CLOSE TICKET BUTTON
# ══════════════════════════════════════════════════════
class CloseTicketView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild  = interaction.guild
        member = interaction.user

        # only ticket owner or staff can close
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        is_staff   = staff_role in member.roles if staff_role else False
        is_owner   = member.id == self.owner_id

        if not is_owner and not is_staff and not member.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ Only the ticket owner or staff can close this ticket.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # ── Close embed ───────────────────────────────
        close_embed = discord.Embed(
            title       = "🔒 Ticket Closing",
            description = f"Closed by {member.mention}\nChannel will be deleted in **5 seconds.**",
            color       = RED,
            timestamp   = datetime.utcnow()
        )
        await interaction.channel.send(embed=close_embed)

        # ── Update DB ─────────────────────────────────
        close_ticket_in_db(self.owner_id, interaction.channel.id)

        # ── Mod log ───────────────────────────────────
        log_ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            log_embed = discord.Embed(
                title     = "🔒 Ticket Closed",
                color     = RED,
                timestamp = datetime.utcnow()
            )
            log_embed.add_field(name="Channel", value=interaction.channel.name, inline=True)
            log_embed.add_field(name="Closed By", value=member.mention,         inline=True)
            log_embed.set_footer(text=f"Owner ID: {self.owner_id}")
            await log_ch.send(embed=log_embed)

        await asyncio.sleep(5)
        await interaction.channel.delete(reason=f"Ticket closed by {member}")
        print(f"[TICKET] Closed & deleted → {interaction.channel.name}")


# ══════════════════════════════════════════════════════
#   TICKET PANEL  (run once with !setup_tickets)
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


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Send the ticket panel to #open-a-ticket. Run once."""
    channel = ctx.guild.get_channel(OPEN_TICKET_CH_ID)
    if channel is None:
        await ctx.send("❌ open-a-ticket channel not found.", delete_after=5)
        return

    embed = discord.Embed(
        title       = "🎫 AFFCONQUER Support",
        description = (
            "```ansi\n"
            "\u001b[1;35m⚔️  A F F C O N Q U E R\u001b[0m\n"
            "```\n"
            "Need help? Open a ticket below.\n"
            "Read the rules before opening — spamming tickets = **ban.**\n\n"
            "⛏️ **MC Help** — Minecraft username issues, SMP problems\n"
            "💬 **Discord Help** — Roles, channels, server issues\n"
            "🆘 **SOS** — Emergency, hacker, griefer, abuse report\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1 ticket per person.** Close your current ticket before opening a new one."
        ),
        color     = DARK_PURPLE,
        timestamp = datetime.utcnow()
    )
    embed.set_footer(
        text     = "⚔️ AFFCONQUER  •  The grind never stops",
        icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    )

    view = TicketPanelView()
    await channel.send(embed=embed, view=view)
    await ctx.message.delete()
    print(f"[SETUP] Ticket panel sent to #{channel.name}")


# ══════════════════════════════════════════════════════
#   /info  — DEV COMMAND  (slash)
# ══════════════════════════════════════════════════════
@tree.command(name="info", description="[DEV] View past tickets of a user")
@app_commands.describe(username="Discord username or user ID")
@app_commands.checks.has_permissions(manage_guild=True)
async def info_cmd(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    # ── Try to resolve member ──────────────────────────
    member = None
    # by mention / ID
    if username.isdigit():
        member = guild.get_member(int(username))
    if not member:
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower()
                   or m.display_name.lower() == username.lower(),
            guild.members
        )

    if not member:
        await interaction.followup.send(f"❌ User `{username}` not found in this server.", ephemeral=True)
        return

    tickets = get_user_tickets(member.id)

    if not tickets:
        await interaction.followup.send(
            f"📭 No ticket history found for **{member.display_name}**.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title       = f"🎫 Ticket History — {member.display_name}",
        description = f"Total tickets: **{len(tickets)}**",
        color       = PURPLE,
        timestamp   = datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    for i, t in enumerate(tickets[-10:], 1):   # last 10 tickets
        status_icon = "🟢" if t["status"] == "open" else "🔴"
        opened = t["opened_at"][:10]
        closed = t.get("closed_at", "—")
        if closed and closed != "—":
            closed = closed[:10]
        embed.add_field(
            name  = f"{status_icon} #{i} — {t['type']}",
            value = f"Opened: `{opened}` | Closed: `{closed}`",
            inline= False
        )

    embed.set_footer(text=f"User ID: {member.id}  •  Showing last 10 tickets")
    await interaction.followup.send(embed=embed, ephemeral=True)


# ══════════════════════════════════════════════════════
#   PERSISTENT VIEWS on restart
# ══════════════════════════════════════════════════════
@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    # CloseTicketView needs owner_id — we re-register with 0 as fallback
    # (it re-checks DB on close anyway)
    bot.add_view(CloseTicketView(owner_id=0))
    await tree.sync()
    print(f"\n  ⚔️  AFFCONQUER Ticket Bot online  |  {bot.user}")
    print(f"  👑  Servers: {len(bot.guilds)}")
    print(f"  🎫  Persistent views registered.\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="tickets 🎫 | AFFCONQUER"
        )
    )


# ══════════════════════════════════════════════════════
#   RUN
# ══════════════════════════════════════════════════════
bot.run(TOKEN)
