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
        fields_dict = {
            "MC Username" : self.mc_username.value,
            "Issue"       : self.issue.value,
            "SMP / Server": self.server_name.value,
            "Urgency"     : self.urgency.value
        }
        await create_ticket(interaction, "⛏️ MC Help", GREEN, fields_dict)

class DiscordHelpModal(discord.ui.Modal, title="💬 Discord Help"):
    discord_tag = discord.ui.TextInput(label="Your Discord Username", placeholder="e.g. kushff007", max_length=100)
    issue       = discord.ui.TextInput(label="Describe Your Issue", style=discord.TextStyle.paragraph, placeholder="Explain in detail...", max_length=1000)
    channel     = discord.ui.TextInput(label="Which Channel / Feature?", placeholder="e.g. #general-chat, roles...", required=False, max_length=100)
    urgency     = discord.ui.TextInput(label="Urgency (ASAP / Today / No Rush)", placeholder="e.g. Today", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        fields_dict = {
            "Discord Username" : self.discord_tag.value,
            "Issue"            : self.issue.value,
            "Channel / Feature": self.channel.value or "Not specified",
            "Urgency"          : self.urgency.value
        }
        await create_ticket(interaction, "💬 Discord Help", PURPLE, fields_dict)

class SOSModal(discord.ui.Modal, title="🆘 SOS Emergency"):
    your_name = discord.ui.TextInput(label="Your Username (MC or Discord)", placeholder="e.g. kushff007", max_length=100)
    emergency = discord.ui.TextInput(label="What Is the Emergency?", style=discord.TextStyle.paragraph, placeholder="Describe fast and clearly...", max_length=1000)
    proof     = discord.ui.TextInput(label="Proof / Evidence (link or describe)", placeholder="screenshot link, video...", required=False, max_length=500)
    accused   = discord.ui.TextInput(label="Who Is Involved?", placeholder="e.g. griefer username", required=False, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        fields_dict = {
            "Reporter" : self.your_name.value,
            "Emergency": self.emergency.value,
            "Proof"    : self.proof.value or "None provided",
            "Involved" : self.accused.value or "Not specified"
        }
        await
