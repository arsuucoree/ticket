import discord
from discord.ext import commands
import os
import asyncio

# 1. Gateway Intents Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration Constants
STAFF_ROLE_NAME = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"
PURPLE_COLOR = discord.Color.purple()

# ----------------------------------------------------
# 2. Main Ticket Panel View (Jo !setup chalane par dikhega)
# ----------------------------------------------------
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="📩 Open Support Ticket", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # User ko 3 choices (suggestions) dene ke liye dropdown menu bhejega
        dropdown_view = TicketDropdownView()
        await interaction.response.send_message("Please select the department for your ticket:", view=dropdown_view, ephemeral=True)

# ----------------------------------------------------
# 3. Dropdown Menu for 3 Ticket Department Options
# ----------------------------------------------------
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="For general queries and assistance.", emoji="💬"),
            discord.SelectOption(label="Billing & Purchase", description="For store or donation related issues.", emoji="💳"),
            discord.SelectOption(label="Report Player/Bug", description="Report a cheater or a technical bug.", emoji="🐛")
        ]
        super().__init__(placeholder="Choose the ticket category...", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        selected_option = self.values[0]
        
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        
        # Private channel permissions configuration
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)

        # Selected category ke mutabik channel prefix change hoga
        prefix = "general"
        if "Billing" in selected_option:
            prefix = "billing"
        elif "Report" in selected_option:
            prefix = "report"

        channel_name = f"{prefix}-{member.name.lower()}"
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        await interaction.response.send_message(f"✅ Your {selected_option} ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
        # Triple-quotes use kiya hai multi-line bug fix karne ke liye
        embed = discord.Embed(
            title=f"⚔️ {selected_option.upper()} TICKET OPENED",
            description=f"""Welcome {member.mention},
Our staff ({STAFF_ROLE_NAME}) will assist you shortly. Please describe your issue in detail.""",
            color=PURPLE_COLOR
        )
        embed.set_footer(text="AFFCONQUER Ticket Management")
        
        inside_view = InsideTicketView()
        await ticket_channel.send(content=f"{member.mention} | Support Team", embed=embed, view=inside_view)

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(TicketDropdown())

# ----------------------------------------------------
# 4. Inside Ticket View Controls (Lock, Unlock, Close)
# ----------------------------------------------------
class InsideTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Lock Chat", style=discord.ButtonStyle.secondary, custom_id="lock_ticket_btn")
    async def lock_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        for target in interaction.channel.overwrites:
            if isinstance(target, discord.Member) and target != interaction.guild.me:
                await interaction.channel.set_permissions(target, send_messages=False, view_channel=True)
        await interaction.response.send_message("🔒 **Ticket Locked.** Member can no longer send messages.", ephemeral=False)

    @discord.ui.button(label="🔓 Unlock Chat", style=discord.ButtonStyle.success, custom_id="unlock_ticket_btn")
    async def unlock_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        for target in interaction.channel.overwrites:
            if isinstance(target, discord.Member) and target != interaction.guild.me:
                await interaction.channel.set_permissions(target, send_messages=True, view_channel=True)
        await interaction.response.send_message("🔓 **Ticket Unlocked.** Member can send messages again.", ephemeral=False)

    @discord.ui.button(label="❌ Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ Closing this ticket in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ----------------------------------------------------
# 5. Bot Events & Setup Command
# ----------------------------------------------------
@bot.event
async def on_ready():
    # Persistent views registration
    bot.add_view(TicketControlView())
    bot.add_view(InsideTicketView())
    print(f"⚔️  AFFCONQUER Ticket Bot online  |  {bot.user.name}#{bot.user.discriminator if bot.user.discriminator != '0' else ''}")
    print(f"👑  Servers: {len(bot.guilds)}")
    print("🎫  Ready and listening for commands.")

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_panel(ctx):
    await ctx.message.delete()
    
    embed = discord.Embed(
        title="⚔️ AFFCONQUER SUPPORT TICKET",
        description=f"""Click the button below to open a support ticket.
Our staff will assist you shortly!""",
        color=PURPLE_COLOR
    )
    embed.set_footer(text="ᴄᴏɴǫᴜᴇʀ TICKET SYSTEM")
    
    view = TicketControlView()
    await ctx.send(embed=embed, view=view)

# Error handling for missing permissions
@setup_panel.error
async def setup_panel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have Administrator permissions to run this command.", delete_after=5)

# Token loading - update via Environment Variable or insert here safely
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Please replace 'YOUR_BOT_TOKEN_HERE' with your real Discord Bot Token, or set it via Railway Environment Variables.")
    bot.run(TOKEN)
