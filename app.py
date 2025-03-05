from discord import Intents, Client, Message, Reaction, ChannelType, Thread
import discord
from discord.ext import tasks
from discord.ui import Button, View, Modal

import config
import helpers
import leaderboard

intents: Intents = Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

@tasks.loop(minutes=5)
async def keep_alive():
    print("Checking bot status...")
    if not client.is_ready():
        print("Bot is not ready, reconnecting...")
        client.run(config.TOKEN)

client: Client = Client(intents=intents)

# Initialize leaderboard
ldb = leaderboard.Leaderboard(config.CONN)

class NicknameModal(Modal, title='Change your nickname!'):
    nickname = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label='nickname',
        required=True,
        placeholder="what's your new nickname?",
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        if ldb.set_username(interaction.user.id, self.nickname.value):
            await interaction.response.send_message('Changed nickname!', ephemeral=True)
            return True
        else:
            return False

class GoalsModal(Modal, title='Set your goals!'):
    goal1 = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label='goal1',
        required=True,
        placeholder="what's your first goal for this week?",
        max_length=50
    )

    goal2 = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label='goal2',
        required=True,
        placeholder="what's your second goal for this week?",
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        goal = True
        output = ""

        if not (self.goal1.value.isspace()):
            if ldb.set_goal(interaction.user.id, 1, self.goal1.value):
                goal = True
                output += "Updated goal 1!\n"
        if not (self.goal2.value.isspace()):
            if ldb.set_goal(interaction.user.id, 2, self.goal2.value):
                goal = True
                output += "Updated goal 2!\n"

        try:
            if goal:
                await interaction.response.send_message(output, ephemeral=True)
                return True
            return False
        except:
            return False

def buttons_view():
    thread_id = ldb.get_working_thread()
    working_thread = client.get_channel(thread_id) if thread_id else None

    buttons = View(timeout=None)

    set_goals_button = Button(style=discord.ButtonStyle.blurple, label="Set Goals", row=1)
    goal1_button = Button(style=discord.ButtonStyle.success, label="Finished Goal 1", row=1)
    goal2_button = Button(style=discord.ButtonStyle.success, label="Finished Goal 2", row=1)
    nickname_button = Button(style=discord.ButtonStyle.secondary, label="Set Nickname", row=2)
    help_button = Button(style=discord.ButtonStyle.secondary, label="Help", row=2)
    ping_button = Button(style=discord.ButtonStyle.secondary, label="Check Status", row=2)

    async def set_goals_callback(interaction):
        await interaction.response.send_modal(GoalsModal())

    async def goal1_callback(interaction):
        if not ldb.set_status(interaction.user.id, 1, True):
            await interaction.response.send_message(
                'Oopsies! Did you do your goal already?', ephemeral=True)
            return

        await working_thread.send(
            f'{interaction.user} has just completed their first goal! Give them a round of applause!')

        await interaction.response.send_message('Done!', ephemeral=True)

    async def goal2_callback(interaction):
        if not ldb.set_status(interaction.user.id, 2, True):
            await interaction.response.send_message(
                'Oopsies! Did you do your goal already?', ephemeral=True)
            return

        await working_thread.send(
            f'{interaction.user} has just completed their second goal! Give them a round of applause!')

        await interaction.response.send_message('Done!', ephemeral=True)

    async def nickname_callback(interaction):
        await interaction.response.send_modal(NicknameModal())

    async def help_callback(interaction):
        await interaction.response.send_message(
            'Welcome to ChallengesBot, programmed by yours truly Izanyoi. Most of the interaction should be done via the'
            ' buttons provided to you, although there are commands you might want to be privy to.\n'
            '/SHAME: Shames all the slackers!\n'
            '/USERS: Adds all writing-check-in into the database if not present\n'
            '/STATUS: Displays everyone\'s progress with this week\'s goals', ephemeral=True)
        return

    async def status_callback(interaction):
        if ldb.check_connection():
            await interaction.response.send_message('MongoDB is fine',
                                                    ephemeral=True)
        else:
            await interaction.response.send_message('MongoDB is down',
                                                    ephemeral=True)

    set_goals_button.callback = set_goals_callback
    goal1_button.callback = goal1_callback
    goal2_button.callback = goal2_callback
    nickname_button.callback = nickname_callback
    help_button.callback = help_callback
    ping_button.callback = status_callback

    buttons.add_item(set_goals_button)
    buttons.add_item(goal1_button)
    buttons.add_item(goal2_button)
    buttons.add_item(nickname_button)
    buttons.add_item(help_button)
    buttons.add_item(ping_button)

    return buttons

@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

    #RECONNECT THE BUTTONS
    buttons_id = ldb.get_buttons()
    if buttons_id != 0:
        buttons = await helpers.get_message(client, config.MAIN_CHANNEL, buttons_id)
        await buttons.edit(view=buttons_view())
        print('Buttons reconnected')


@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user: return

    if (message.content.startswith('-★-')
            and message.channel.id == config.MAIN_CHANNEL):
        ldb.start_new_week()

        #Get Leaderboard
        image_path = ldb.get_leaderboard()
        if image_path == "MongoDB is not accessible currently.":
            await message.channel.send(image_path)
        else:
            await message.channel.send("Leaderboard:", file=discord.File(image_path))

        #Update thread
        thread: Thread = await message.channel.create_thread(
            name=f'WEEK {ldb.get_week()}',
            type=ChannelType.public_thread)
        old_thread_id: int = ldb.update_working_thread(thread.id)

        #Lock old thread
        if old_thread_id != 0:
            old_thread: Thread = await client.fetch_channel(old_thread_id)
            await old_thread.edit(archived=True, locked=True)

        #Create new buttons
        new_buttons: Message = await message.channel.send(view=buttons_view())
        old_buttons_id: int = ldb.update_buttons(new_buttons.id)

        #Delete old buttons
        old_buttons: Message = await helpers.get_message(client, config.MAIN_CHANNEL, old_buttons_id)
        await old_buttons.delete()

        #Recalculate helpers
        await helpers.recalculate_slackers(client, ldb)

    elif message.content.startswith('/'):

        if message.content.startswith('/STATUS'):
            image_path = ldb.get_status()
            if image_path == "MongoDB is not accessible currently.":
                await message.channel.send(image_path)
            else:
                await message.channel.send(file=discord.File(image_path))

        elif message.content.startswith('/REMOVE'):
            ldb.remove_user(int(message.content[8:]))

        elif message.content.startswith('/USERS'):
            guild = client.get_guild(config.SERVER_ID)
            members = [
                member async for member in guild.fetch_members(limit=None)
            ]

            # Filter members with the specific role
            role_members = [
                member for member in members
                if config.WW_ROLE_ID in [role.id for role in member.roles]
            ]

            for member in role_members:
                ldb.add_user(member.id, member.name)

        elif message.content.startswith('/SHAME'):
            slackers = await helpers.recalculate_slackers(client, ldb)

            if len(slackers) == 0:
                await message.channel.send(
                    "Y'all are some good hardworking folk, cause there ain't no slackers here! Good job lads")
                return

            msg = "Hey slackers! It's time to quit whining and lock in! That's right, I'm looking at you"

            for slacker in slackers:
                msg += f", {slacker.mention}"

            msg += "!"
            await message.channel.send(msg)

        elif message.content.startswith('/FORCE'):
            if message.content == '/FORCE WEEK':
                ldb.start_new_week()

            elif message.content == '/FORCE LEADERBOARD':
                image_path = ldb.get_leaderboard()
                if image_path == "MongoDB is not accessible currently.":
                    await message.channel.send(image_path)
                else:
                    await message.channel.send(file=discord.File(image_path))

            elif message.content == '/FORCE BUTTONS':
                await message.channel.send(view=buttons_view())



    return


@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == config.ROLE_REACT_MSG:
        user = await client.fetch_user(payload.user_id)
        ldb.add_user(user.id, user.name)

    return

#ACTUAL CODE
client.run(token=config.TOKEN)
keep_alive.start()