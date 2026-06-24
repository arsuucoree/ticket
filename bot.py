import discord
from discord.ext import commands
import os

# Intense / Gateway setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration Constants
STAFF_ROLE_NAME = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"
PURPLE_COLOR = discord.Color.purple()

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label="📩 Create Ticket", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        # Check if staff role exists, if not create/handle or use defaults safely
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        
        # Overwrites for the new private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)

        # Create ticket channel under a clean format
        channel_name = f"ticket-{-member.name.lower()}"
        # Look for existing channel to avoid spam if preferred, or just create it
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        await interaction.response.send_message(f"✅ Your ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
        # Send greeting embed inside the ticket channel
        embed = discord.Embed(
            title="⚔️ TICKET OPENED",
            description=f"Welcome {member.mention},
Our staff ({STAFF_ROLE_NAME}) will assist you shortly. Please describe your issue in detail.",
            color=PURPLE_COLOR
        )
        embed.set_footer(text="AFFCONQUER Ticket Management")
        
        # Inside ticket control buttons (Close)
        inside_view = InsideTicketView()
        await ticket_channel.send(content=f"{member.mention} | Support Team", embed=embed, view=inside_view)

class InsideTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ Closing this ticket in 5 seconds...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.event
async def on_ready():
    # Registering persistent view so buttons work even after restart
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
        description="Click the button below to open a support ticket.
Our staff will assist you shortly!",
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
