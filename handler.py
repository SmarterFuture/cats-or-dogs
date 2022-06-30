import random as r
import os
from tools import CList
import pickle as pk
import datetime as dt


class UserHandler:
    auto_save_interval = 30      # in minutes
    image_update_interval = 60   # in minutes
    banner_update_interval = 5   # in seconds

    def __init__(self, save=None):
        if save is not None:
            self.load(save, latest=True)
        else:
            self.everyone = dict()  # uid, User(object)
            self.servers = dict()   # sid, Server(object)

    def handle(self, uid, name: str, sid=None):
        if uid not in self.everyone:
            self.everyone[uid] = self.User(uid, name)

        if sid is not None:
            if sid not in self.servers:
                self.servers[sid] = self.Server(sid)
            if uid not in self.servers[sid].members:
                self.servers[sid].add_user(uid)

        self.everyone[uid].name = name

    def load(self, path, latest=False):
        if latest:
            path += max(os.listdir(path), key=lambda x: os.path.getctime(path + x))
        with open(path, 'rb') as f:
            self.__dict__.update(pk.load(f).__dict__)
        print("there was an attempt to load data from", path)

    def save(self, path):
        with open(path, 'wb') as f:
            pk.dump(self, f, -1)
        print("there was an attempt to save data to", path)

    class Server:
        last_used_time = dt.datetime.fromisoformat('2011-11-04')

        def __eq__(self, other: int):
            return int(other) == self.id

        def __init__(self, sid: int):
            self.__length = 20
            self.aliases = CList([], 20)
            self.real_aliases = dict()
            self.authorization_level = [set(), set(), set(), set(), set()]
            # 0 - no extra permissions
            # 1 - ?
            # 2 - ?
            # 3 - ?
            # 4 - all permissions
            self.id = sid
            self.members = set()
            self.prefix = "img"

        def __int__(self):
            return int(self.id)

        def __ne__(self, other: int):
            return not self.__eq__(other)

        def add_user(self, uid: int):
            self.members.add(uid)
            self.authorization_level[0].add(uid)

        def get_authorization_level(self, uid: int):
            for i, v in enumerate(self.authorization_level):
                if uid in v:
                    return i

        def set_authorization_level(self, uid: int, level: int):
            for i in self.authorization_level:
                i.discard(uid)
            self.authorization_level[level].add(uid)

        def set_length(self, length: int):
            if 0 < length <= 1000:
                self.aliases = CList(list(self.aliases), length)

    class Streak:
        def __init__(self):
            self.all = 0        # all items
            self.count = 0      # count of specified items
            self.max = 0        # greatest streak
            self.n = 0          # streak
            self.score = 0      # current score
            self.st = 0         # overall streak for statistical purposes only

        def __int__(self):
            return int(self.n)

        def add(self, item: bool):
            self.n = self.n * item + item
            self.all += 1
            self.count += item
            self.score += self.n * (self.n + 1) * (2 * self.n + 1) / 6
            self.st += self.n

            if self.n > self.max:
                self.max = self.n

        def mean(self):
            if self.all == 0:
                return 0
            return round(self.st / self.all, 3)

    class User:
        last_used_time = dt.datetime.fromisoformat('2011-11-04')

        def __eq__(self, other: int):
            return int(other) == self.id

        def __init__(self, uid: int, name: str):
            self.__length = 10                      # depth of history
            self.history = CList([], 10)            # history
            self.id = uid                           # user id
            self.name = name                        # username real one
            self.dog = UserHandler.Streak()         # streak statistics for dogs
            self.cat = UserHandler.Streak()         # streak statistics for cats
            self.probability = 0.5                  # probability of not getting a cat

        def __int__(self):
            return self.id

        def __ne__(self, other: int):
            return not self.__eq__(other)

        # this will decide whether the item that was chosen by user is cat or not
        def get_cat(self, item: int):
            if item in self.history:
                raise Exception("this number was used recently")
            is_cat = r.random() < self.probability
            self.history.append(item)
            self.cat.add(is_cat)
            self.dog.add(not is_cat)
            return is_cat

        # this will display current score
        def score(self):
            return int(self.cat.score)

        # this will set depth of history
        def set_length(self, length: int):
            if 0 < length <= 50:
                self.history = CList(list(self.history), length)

        # this will return stats for further handling
        def stats(self):
            return self.history, self.cat, self.dog
