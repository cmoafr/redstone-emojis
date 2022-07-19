from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands

from utils.config import get_config

async def setup(bot):
    await bot.add_cog(Roles(bot))

class Roles(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    roles = app_commands.Group(name="roles", description="Manage your roles")

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Cog roles ready!")



    @roles.command(name="list", description="List all possibles roles")
    async def list(self, interaction):
        # Reloading each time to prevent having to reload just to change the roles
        ids = get_config("roles").get(str(interaction.guild.id), None)
        L = [role for role in interaction.guild.roles if role.id in ids]
        if L:
            await interaction.response.send_message(f"Available roles: {self._roles_to_str(L)}")
        else:
            await interaction.response.send_message("No roles available.")
    
    @roles.command(name="add", description="Add yourself roles")
    @app_commands.describe(roles="Roles you want to get")
    async def add(self, interaction, roles:str):
        added = await self.process_roles(interaction, roles, interaction.user.add_roles)
        if added is None:
            return
        if added:
            await interaction.response.send_message(f"Added roles: {self._roles_to_str(added)}", ephemeral=True)
        else:
            await interaction.response.send_message("No roles added.", ephemeral=True)
    
    @roles.command(name="remove", description="Remove yourself roles")
    @app_commands.describe(roles="Roles you want to remove")
    async def remove(self, interaction, roles:str):
        removed = await self.process_roles(interaction, roles, interaction.user.remove_roles)
        if removed is None:
            return
        if removed:
            await interaction.response.send_message(f"Removed roles: {self._roles_to_str(removed)}", ephemeral=True)
        else:
            await interaction.response.send_message("No roles removed.", ephemeral=True)



    def available_roles(self, guild, wanted, negate=False):
        ids = get_config("roles").get(str(guild.id), None)
        keep = lambda role: role.id in ids and (negate ^ (role.name.lower() in wanted))
        return [role.name.lower() for role in guild.roles if keep(role)]

    async def process_roles(self, interaction, roles, action):
        L = [] # List of roles added/removed
        wanted = sorted(list(set(role.strip().lower() for role in roles.split(","))))

        def get_role(name):
            for role in interaction.guild.roles:
                if role.name.lower() == name:
                    return role
            return None

        for name in wanted:
            try:
                role = get_role(name)
                if role is not None:
                    await action(role)
                    L.append(role)
            except Forbidden:
                await interaction.response.send_message("It appears I am not strong enough. Ask an admin to give me permission and try again later.")
                return None
            except HTTPException:
                pass
        return L



    @add.autocomplete("roles")
    @remove.autocomplete("roles")
    async def roles_autocomplete(self, interaction, current):
        wanted = current.lower().split(", ")
        availables = sorted(self.available_roles(interaction.guild, wanted, negate=True))
        
        # Get all the possible matches for the last role
        last = wanted.pop()
        possibles = [role for role in availables if role.startswith(last)]
        if len(possibles) == 0 and availables:
            wanted.append(last)
            last = ""
            possibles = availables

        # Format and return the list of possible roles
        choices = [", ".join(wanted + [possible]) for possible in possibles]
        return [app_commands.Choice(name=choice, value=choice) for choice in choices]

    def _roles_to_str(self, roles):
        names = [f"`{role.name}`" for role in roles]
        if len(names) >= 3:
            return ", ".join(names[:-1]) + " and " + names[-1]
        return ", ".join(names)
