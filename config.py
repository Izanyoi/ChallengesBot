import os
from dotenv import load_dotenv

load_dotenv()

CONN = os.getenv('MONGO_CONN') #FROM .ENV, your MongoDB link
TOKEN = os.getenv('DISCORD_TOKEN') #FROM .ENV, your discord bot token
SERVER_ID = #YOUR SERVER ID
MAIN_CHANNEL = #THE CHANNEL YOU WANT YOUR BOT TO OPERATE IN
ROLE_REACT_MSG = #THE MESSAGE WHERE PEOPLE GET THE ROLE WHEN THEY REACT, USED FOR ADDING PEOPLE TO THE DB AS SOON AS THEY GET THE ROLE
WW_ROLE_ID = #THE ROLEID OF THE ROLE FOR WHOEVER IS PARTICIPATING
SLACKER_ROLE_ID = #THE ROLE BEING SHAMED
