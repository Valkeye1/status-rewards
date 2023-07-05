
intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = discord.Bot(command_prefix=">", intents=intents)

using_code = {
    "userid": {"balance": 0, "last_checked": time.time()}
}

using_code = json.load(open("balances.json"))

class SimpleView(discord.ui.View):
    foo : bool = None

    def __init__(self, game_cost = 0, game_creator=None):
        super().__init__(timeout=None)
        self._game_cost = game_cost
        self._game_creator = game_creator
        self.value = None

    joined_clicked = None
    cancelled_clicked = False

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    def set_cost(self, cost):
        self._game_cost = cost

    def get_cost(self):
        return self._game_cost
    
    def set_creator(self, creator):
        self._game_creator = creator

    def get_creator(self):
        return self._game_creator

    @discord.ui.button(label="Join", row=1, style=discord.ButtonStyle.green)
    async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != SimpleView.get_creator(self):
            if using_code[str(interaction.user.id)]["balance"] >= int(SimpleView.get_cost(self)):
                await interaction.response.send_message(f"Successfully joined coinflip!", ephemeral=True)
                self.joined_clicked = interaction.user.id
                using_code[str(interaction.user.id)]["balance"] -= SimpleView.get_cost(self)
                self.stop()
            else:
                await interaction.response.send_message(f"You don\'t have enough balance to join this game!", ephemeral=True)
        else:
            await interaction.response.send_message(f"You can\'t join your own coinflip!!", ephemeral=True)
        self.foo = False

    @discord.ui.button(label="Cancel", 
    style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == SimpleView.get_creator(self):
            self.cancelled_clicked = True
            await interaction.response.send_message("Successfully cancelled coinflip!", ephemeral=True)
            self.foo = False
            self.stop()
        else:
            await interaction.response.send_message("You cant cancel someone else's coinflip!", ephemeral=True)
            self.foo = False


@bot.event
async def on_ready():
    while True:
        for guild in bot.guilds:
            whale = discord.utils.get(guild.roles, name="Whale")
            highroller = discord.utils.get(guild.roles, name="High Roller")
            for member in guild.members:
                if str(member.id) in using_code:
                    if time.time() - using_code[str(member.id)]['last_checked'] >= 120:
                        if str(member.id) in using_code:
                            using_code[str(member.id)]["last_checked"] = time.time() 

                            for a in member.activities:
                                if isinstance(a, discord.CustomActivity):
                                    if whale in member.roles:
                                        if "bloxybet" in str(a).lower():
                                            using_code[str(member.id)]['balance'] += 3
                                    elif highroller in member.roles:
                                        if "bloxybet" in str(a).lower():
                                            using_code[str(member.id)]['balance'] += 2
                                    else:
                                        if "bloxybet" in str(a).lower():
                                            using_code[str(member.id)]['balance'] += 1
                else:
                    using_code[str(member.id)] = {"balance": 0, "last_checked": time.time()}
                    for a in member.activities:
                            if isinstance(a, discord.CustomActivity):
                                if whale in member.roles:
                                    if "bloxybet" in str(a).lower():
                                        using_code[str(member.id)]['balance'] += 3
                                elif highroller in member.roles:
                                    if "bloxybet" in str(a).lower():
                                        using_code[str(member.id)]['balance'] += 2
                                else:
                                    if "bloxybet" in str(a).lower():
                                        using_code[str(member.id)]['balance'] += 1
                    
        with open('balances.json', 'w') as fp:
            json.dump(using_code, fp)  
        await asyncio.sleep(60)

@bot.slash_command(guild_ids=[1014936516130242580], description='create a coinflip')
async def coinflip(ctx, amount):
    if ctx.channel.id != 1080007678308392981:
        return await ctx.respond(f'This command can only be used within <#1080007678308392981> :rage:', ephemeral=True)
    
    try:
        int(amount)
    except:
        return await ctx.respond(f'Input must be a number :rage:', ephemeral=True)
    amount = int(amount)
    if int(amount) < 1 :
        return await ctx.respond(f'Coinflip amount must be at least 1 :gem: !', ephemeral=True)
    
    if using_code[str(ctx.user.id)]["balance"] < amount:
        return await ctx.respond(f'You don\'t have enough :gem: to create this coinflip! :rage:', ephemeral=True)
    
    using_code[str(ctx.user.id)]["balance"] -= amount


    view = SimpleView()
    view.set_cost(amount)
    view.set_creator(ctx.author.id)
    embed = discord.Embed(
        title="Coinflip Open", color=0x58b9ff
    )
    embed.add_field(name="Amount", value=f"{amount} :gem:")
    embed.add_field(name="Creator", value=f"{ctx.author.mention}")
    message = await ctx.respond("Successfully created coinflip!", ephemeral=True)
    message = await ctx.send(view=view, embed=embed)
    await view.wait()
    while not view.joined_clicked and not view.cancelled_clicked:
        await asyncio.sleep(1)
    if view.cancelled_clicked:
        #add da gems back
        using_code[str(ctx.author.id)]["balance"] += amount
        return await message.delete()
    
    if view.joined_clicked:
        await view.disable_all_items()
        embednew = discord.Embed(
            title="Coinflip Concluded", color=0x58b9ff
        )

        winner = random.choice([ctx.author.id, view.joined_clicked])

        using_code[str(winner)]["balance"] += (amount*2)

        if winner == ctx.author.id:
            loser = view.joined_clicked
        else:
            loser = ctx.author.id

        embednew.add_field(name="Amount", value=f"{amount} :gem:")
        embednew.add_field(name="Winner", value=f"<@{winner}>")
        embednew.add_field(name="Loser", value=f"<@{loser}>")
        return await message.edit(embed=embednew)

 
@bot.slash_command(guild_ids=[1014936516130242580], description='check the gem leaderboard')
async def leaderboard(ctx):
    if ctx.channel.id != 1080007678308392981:
        return await ctx.respond(f'This command can only be used within <#1080007678308392981> :rage:', ephemeral=True)
    
    await ctx.respond("Fetching leaderboard, this may take a few moments.", ephemeral=True)
    
    
    user_as_list = []

    fancytext = ''

    for user in using_code:
        user_as_list.append({"discord_id": user, "gems": using_code[str(user)]['balance']})
    
    leaderboard = sorted(user_as_list, key=lambda x: x['gems'], reverse=True)

    for user in leaderboard[0:10]:
        fancytext += f'``{leaderboard.index(user) + 1}-`` <@{user["discord_id"]}> **{user["gems"]}** :gem:\n'

    embed = discord.Embed(
        title="Leaderboard", description=fancytext, color=0x58b9ff
    )
    message = await ctx.followup.send(embed=embed)
 
@bot.slash_command(guild_ids=[1014936516130242580], description='check your status reward balance')
async def balance(ctx):
    if ctx.channel.id != 1080007678308392981:
        return await ctx.respond(f'This command can only be used within <#1080007678308392981> :rage:', ephemeral=True)
    
    payout = 0

    whale = discord.utils.get(ctx.guild.roles, name="Whale")
    highroller = discord.utils.get(ctx.guild.roles, name="High Roller")
    for a in ctx.author.activities:
        if isinstance(a, discord.CustomActivity):
            if "bloxybet" in str(a).lower():
                if whale in ctx.author.roles:
                    payout = 3
                elif highroller in ctx.author.roles:
                    payout = 2
                else:
                    payout = 1
    
    if payout > 0:
        await ctx.respond(f"You have ``{using_code[str(ctx.author.id)]['balance']}`` :gem: Thanks for supporting **bloxy.bet**, your current payout rate is ``{payout*30}`` :gem: / hour")
    else:
        await ctx.respond(f"You have ``{using_code[str(ctx.author.id)]['balance']}`` :gem: Start earning gems by adding ``discord.gg/bloxybet`` to your discord status! :tada:")

@bot.slash_command(guild_ids=[1014936516130242580], description='check your status reward balance')
async def tip(ctx, mention: Option(
        discord.SlashCommandOptionType.mentionable,
        name="user",
        description="user you want to tip",
        required=True
    ), amount):
    if int(amount) < 1:
        return await ctx.respond(f'Tip must be at least 1 :gem: !', ephemeral=True) 
    if using_code[str(ctx.author.id)]['balance'] < int(amount):
        return await ctx.respond(f'You don\'t have enough :gem: to send that tip!', ephemeral=True)
    else:
        using_code[str(ctx.author.id)]['balance'] -= int(amount)
    using_code[str(mention.id)]['balance'] += int(amount)
    return await ctx.respond(f'Successfully sent a ``{amount}`` :gem: tip to {mention.mention}!', ephemeral=False)
  
bot.run('token_here')
