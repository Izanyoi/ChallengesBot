from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import matplotlib.pyplot as plt

class Leaderboard:
    def __init__(self, conn: str):
        self.client = MongoClient(conn, server_api=ServerApi('1'))
        self.db = self.client['leaderboard']
        self.users = self.db['users']
        self.vars = self.db['vars']

    def check_connection(self):
        try:
            self.client.admin.command('ping')
            return True

        except Exception:
            return False

    def add_user(self, user: int, username: str):
        document = {
            "_id": user,
            "username": username,
            "score": 0,
            "streak": 0,
            "goal1": "",
            "goal2": "",
            "g1status": False,
            "g2status": False
        }

        try:
            self.users.insert_one(document)
            return True
        except:
            return False

    def remove_user(self, user: int):
        try:
            self.users.delete_one({'_id': user})
            return True
        except:
            return False

    def get_users(self, query: dict):
        try:
            output = []
            users = self.users.find(query)
            for user in users:
                output.append(int(user.get('_id')))

            return output

        except:
            print('Hit Error!')
            return []

    def get_leaderboard(self):
        if not self.check_connection(): return 'MongoDB is not accessible currently.'

        columns = ['Rank', 'Nickname', 'Score', 'Streak']
        rows = []

        on_leaderboard = self.users.find({"streak": {"$gt": -3}}).sort([("score", -1), ("streak", -1)])

        prev_score = 1000 #IMPOSSIBLY HIGH VALUE
        rank = 0
        real_rank = 0

        for user in on_leaderboard:
            score = user.get('score')

            real_rank += 1
            if score < prev_score:
                rank += 1
                prev_score = score

            rows.append([rank, user.get("username"), score, user.get("streak")])

        fig, ax = plt.subplots(figsize=(5, (len(rows) + 1) * 0.1))
        ax.set_axis_off()
        table = plt.table(cellText=rows,
                          colLabels=columns,
                          loc='center', cellLoc='left',
                          colWidths=[0.15, 0.65, 0.15, 0.15])

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Remove excess margins
        plt.savefig("leaderboard.png", bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)

        return "leaderboard.png"

    def get_status(self):
        if not self.check_connection(): return 'MongoDB is not accessible currently.'

        on_leaderboard = self.users.find({"streak": {"$gt": -3}}).sort([("score", -1), ("streak", -1)])

        rows = []

        for user in on_leaderboard:
            g1stat = ''
            g2stat = ''

            if user.get('g1status'):
                g1stat = 'DONE'

            if user.get('g2status'):
                g2stat = 'DONE'

            rows.append([user.get('username'),
                         f'{user.get('goal1')}\n{'-' * 50}\n{user.get('goal2')}',
                         f'{g1stat}\n{'-' * 4}\n{g2stat}'])

        fig, ax = plt.subplots(figsize=(5, (len(rows)) * 0.25))
        ax.set_axis_off()
        table = plt.table(cellText=rows,
                          loc='center',
                          cellLoc='left',
                          colWidths=[0.3, 0.6, 0.10])

        # Set row heights manually
        for i, key in table.get_celld().items():
            key.set_height(0.25)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Remove excess margins
        plt.savefig("status.png", bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close(fig)

        return "status.png"

    def add_score(self, user: int, increment: int):
        try:
            self.users.update_one({'_id': user}, {'$inc': {'score': 1}})
            return self.users.find_one({'_id': user})
        except:
            return -1

    def calculate_streak(self, user: int, streaked: bool):
        try:
            streak = int(self.users.find_one({'_id': user}).get('streak'))

            if streaked and streak > 0:
                update = {'$inc': {'streak': 1}}
            elif streaked:
                update = {'$set': {'streak': 1}}
            elif streak > 0:
                update = {'$set': {'streak': 0}}
            else:
                update = {'$inc': {'streak': -1}}

            self.users.update_one({'_id': user}, update)

            return True
        except:
            return False

    def set_goal(self, user:int, goal_num:int, goal: str):
        try:
            self.users.update_one({'_id': user}, {'$set': {f'goal{goal_num}': goal}})
            return True
        except:
            return False

    def set_status(self, user:int, goal: int, finished: bool):
        try:
            #If status is already that, return False
            if self.users.find_one({'_id': user}).get(f'g{goal}status') == finished: return False

            self.users.update_one({'_id': user}, {'$set': {f'g{goal}status': finished}})
            return True

        except:
            return False

    def set_username(self, user: int, username: str):
        try:
            self.users.update_one({'_id': user}, {'$set': {'username': username}})
            return True
        except:
            return False

    def get_week(self):
        try:
            return int(self.vars.find_one().get('week'))
        except:
            return -1

    def update_working_thread(self, threadID: int):
        try:
            old = self.vars.find_one().get('thread')
            self.vars.update_one({}, {'$set': {'thread': threadID}})
            return old
        except:
            return -1

    def get_working_thread(self):
        try:
            return self.vars.find_one().get('thread')
        except:
            return -1

    def get_buttons(self):
        try:
            return self.vars.find_one().get('buttons')
        except:
            return False

    def update_buttons(self, buttonID: int):
        try:
            old: int = self.vars.find_one().get('buttons')
            self.vars.update_one({}, {'$set': {'buttons': buttonID}})
            return old
        except:
            return -1

    def start_new_week(self):
        try:
            self.vars.update_one({}, {'$inc' : {'week': 1}})

            on_leaderboard = self.users.find({"streak": {"$gt": -3}}).sort("streak", -1)

            for user in on_leaderboard:
                new_score = 0
                if bool(user.get('g1status')): new_score += 1
                if bool(user.get('g2status')): new_score += 1

                streak = int(user.get('streak'))

                if new_score > 0 and streak > 0:
                    update = {'$inc': {'streak': 1, 'score': new_score}}
                elif new_score > 0:
                    update = {'$set': {'streak': 1}, '$inc': {'score': new_score}}
                elif streak > 0:
                    update = {'$set': {'streak': 0}, '$inc': {'score': new_score}}
                else:
                    update = {'$inc': {'streak': -1, 'score': new_score}}

                self.users.update_one({'_id': user.get('_id')}, update)

            reset = {'$set': {'goal1': 'NONE', 'goal2': 'NONE', 'g1status': False, 'g2status': False}}
            self.users.update_many({}, reset)
            return True
        except:
            return False

    def hard_reset(self):
        try:
            self.users.update_many({}, {'$set': {'score': 0, 'streak': 0, 'goal1': '', 'goal2': '', 'g1status': False, 'g2status': False}})
            return True
        except: return False