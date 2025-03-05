import leaderboard
from discord import Client

import config


async def recalculate_slackers(client: Client, ldb: leaderboard.Leaderboard):
    #GET SLACKERS
    slackers = ldb.get_users({"streak": {"$lt": 0}})
    guild = client.get_guild(config.SERVER_ID)
    slacker_role = guild.get_role(config.SLACKER_ROLE_ID)
    members = [
        member async for member in guild.fetch_members(limit=None)
    ]

    output = []

    for member in members:
        #Is a slacker
        if member.id in slackers:
            output.append(member)
            #Doesn't have role
            if member.get_role(config.SLACKER_ROLE_ID) is None:
                await member.add_roles(slacker_role)
        #Not a slacker
        else:
            #Has role
            if member.get_role(config.SLACKER_ROLE_ID):
                await member.remove_roles(slacker_role)

    return output


async def get_message(client: Client, channel_id: int, message_id: int):
    channel = await client.fetch_channel(channel_id)
    message = await channel.fetch_message(message_id)
    return message