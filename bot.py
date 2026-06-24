import discord
from discord.ext import commands
import os
import asyncio

# 1. Intents config (Takki bot commands aur members track kar sake)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Settings (Tumhare server ki configuration)
STAFF_ROLE_NAME = "🎖️ ᴄᴏɴǫᴜᴇʀᴏʀ"
PURPLE_COLOR = discord.Color.purple()

# 3. Ticket Button Panel View
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view taaki bot restart hone par bhi buttons kaam karein

    @discord.ui.button(label="📩 Create Ticket", style=discord.ButtonStyle.secondary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        # Staff role check karega
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        
        # Private channel ki permissions setup
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        }
        
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)

        # Dynamic Ticket Channel Create karega bina purani hardcoded IDs ke
        channel_name = f"ticket-{member.name.lower()}"
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        await interaction.response.send_message(f"✅ Your ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
        # Ticket ke andar ka Welcome Embed
        embed = discord.Embed(
            title="⚔️ TICKET OPENED",
            description=f"Welcome {member.mention},\nOur staff will assist you shortly. Please describe your issue in detail.",
            color=PURPLE_COLOR
        )
        embed.set_footer(text="AFFCONQUER Ticket Management")
        
        inside_view = InsideTicketView()
        await ticket_channel.send(content=f"{member.mention} | Support Team", embed=embed, view=inside_view)

# 4. Ticket ke andar ka Close Button View
class InsideTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ Closing this ticket in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# 5. Bot Events
@bot.event
async def on_ready():
    # Dono Views ko register karna zaroori hai reload compatibility ke liye
    bot.add_view(TicketControlView())
    bot.add_view(InsideTicketView())
    print(f"⚔️  AFFCONQUER Ticket Bot online  |  {bot.user.name}")
    print(f"👑  Servers: {len(bot.guilds)}")
    print("🎫  Ready.")

# 6. Setup Command (Jis channel me chaloge wahan create ticket panel bhej dega)
@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_panel(ctx):
    await ctx.message.delete()
    
    embed = discord.Embed(
        title="⚔️ AFFCONQUER SUPPORT TICKET",
        description="Click the button below to open a support ticket.\nOur staff will assist you shortly!",
        color=PURPLE_COLOR
    )
    embed.set_footer(text="ᴄᴏɴǫᴜᴇʀ TICKET SYSTEM")
    
    view = TicketControlView()
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have Admin permissions to use this command.", delete_after=5)

# 7. Token Connection
TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

if __name__ == "__main__":
    bot.run(TOKEN)
