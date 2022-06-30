from tools import *
from random import randint
from bisect import bisect_left
from os import listdir
import datetime as dt

command_handler = CommandHandler()


class Basic:
    def __call__(self, *args):
        function = args[0]

        if self.sid is not None:
            if args[0] in self.database.servers[self.sid].aliases:
                function = self.database.servers[self.sid].real_aliases[args[0]]

        if function not in command_handler.commands:
            return "this command does not exist", None, dict(err=True)

        try:
            return getattr(self, function)(*args[1:])
        except AttributeError:
            return "this command does not exist", None, dict(err=True)

    def __init__(self, uid: int, database: object, sid=None):
        self.uid = uid
        self.database = database
        self.sid = sid

    def is_authorized(self, level: int):
        return level <= self.database.servers[self.sid].get_authorization_level(self.uid)


class Alias(Basic):
    color = 0x66d9ff

    @command_handler.command(help_message="used to make aliases",
                             server_command=True)
    def make(self, command, alias):
        if command not in command_handler.commands:
            raise Exception("this command does not exist")
        if alias in self.database.servers[self.sid].aliases:
            raise Exception("this alias is already registered")
        if " " in alias and not alias:
            raise Exception("this alias is invalid")

        self.database.servers[self.sid].aliases.append(alias)
        self.database.servers[self.sid].real_aliases[alias] = command
        return [str(), f"new alias ({command}: {alias}) was successfully created", self.color]

    @command_handler.command(help_message="used to remove aliases",
                             server_command=True)
    def remove(self, alias):
        if alias not in self.database.servers[self.sid].aliases:
            raise Exception("this alias does not exist")
        self.database.servers[self.sid].aliases.discard(alias)
        return [str(), f"alias ({alias}) was successfully deleted", self.color]

    @command_handler.command(help_message="used to display a list of aliases",
                             server_command=True)
    def view(self):
        aliases = dict()
        real_aliases = self.database.servers[self.sid].real_aliases

        for alias in real_aliases:
            command = real_aliases[alias]
            if command in aliases:
                aliases[command].append(alias)
            else:
                aliases[command] = [alias]

        return ["list of current aliases:", str(), self.color,
                list(map(lambda x: (x[0], ', '.join(x[1]), True), aliases.items()))]


class Authorization(Basic):

    @command_handler.command(help_message="used to set an authorization level",
                             server_command=True)
    def set(self, user, level):
        level = int(level)
        tag = Tag(user)
        if tag == self.uid:
            raise Exception("you cannot set an authorization level to yourself")
        if tag not in self.database.servers[self.sid].members:
            raise Exception("this user is not on this server")
        if self.is_authorized(level):
            self.database.servers[self.sid].set_authorization_level(tag, level)
            return [str(), f"{tag} was successfully authorized to level {level}"]
        raise Exception(f"your authorization level is is too low "
                        f"({self.database.servers[self.sid].get_authorization_level(self.uid)})")

    @command_handler.command(help_message="used to view authorization level",
                             server_command=True)
    def view(self, *args):
        if len(args) == 0:
            tag = Tag(self.uid)
        else:
            tag = Tag(args[0])
        if tag not in self.database.servers[self.sid].members:
            raise Exception("this user is not on this server")
        return [str(), f"{tag}'s authorization level is: "
                       f"`{self.database.servers[self.sid].get_authorization_level(tag)}`"]


class Backup(Basic):
    backup_dir = "backups\\"  # path.abspath("backups") + "\\"
    color = 0xfdfe03
    last_interval = 0  # in minutes

    @command_handler.command(help_message="used to adjust time intervals (minutes) for bot backups",
                             server_command=True, authorization_level=4)
    def interval(self, *args):
        """
        this command is used to view and set time intervals in which is bot backed up
        |:__parameter__ [...]: `[none]` - this will display current interval|n|
                               `[time]` - this will set interval for automatic backups, [time] has to be interval
                                          between 30 and 720 minutes
        """
        if len(args) == 0:
            return [str(),
                    f"current time interval for bot backups is `{self.database.auto_save_interval}` minutes",
                    self.color]
        time = int(args[0])
        if 30 <= int(time) <= 720:
            self.database.auto_save_interval = time
            return [str(),
                    f"time interval for bot backups was successfully changed to`{time}` minutes",
                    self.color]
        else:
            raise Exception("this interval value is invalid")

    @command_handler.command(help_message="used to immediately load previous bot data",
                             server_command=True, authorization_level=4)
    def load(self, *args):
        """
        this command is used to immediately load specified or previous bot data
        |:parameter [...]: `[none]` - this will display 5 recent saves|n|
                           `[positive integer]` - this will display [inputted number] recent saves|n|
                           `auto` - this will load last saved bot data|n|
                           `[exact path]` - this will load specified bot data
        """
        depth = 0
        if len(args) == 0:
            depth = 5
        elif args[0].isdigit():
            depth = int(args[0])
        if depth != 0:
            return ["recent saves", "\n".join(listdir(self.backup_dir)[-depth:]), self.color]

        if args[0].lower() == "auto":
            self.database.load(self.backup_dir, latest=True)

        self.database.load(self.backup_dir + args[0])
        return [str(), "datas were loaded successfully", self.color]

    @command_handler.command(help_message="used to turn on or off automatic backups",
                             server_command=True, authorization_level=4)
    def manual(self, *args):
        """
        this command is used to turn on or off automatic backups or to view the current type of operation of backups
        (manual or automatic)
        |:parameter [...]: `[none]` - this will show the current type of operation of backups|n|
                           `true` - this will *disable* automatic backups|n|
                           `false` - this will *enable* automatic backups
        """
        state = "enabled" if self.database.auto_save_interval else "disabled"
        if len(args) == 0:
            return [str(), f"automatic backups are currently `{state}`", self.color]

        if args[0].lower() == "true":
            self.last_interval = self.database.auto_save_interval
            self.database.auto_save_interval = 0
            state = "disabled"
        elif args[0].lower() == "false":
            self.database.auto_save_interval = self.last_interval
            state = "enabled"
        else:
            raise Exception("unrecognized command")
        return [str(), f"automatic backups were `{state}`", self.color]

    @command_handler.command(help_message="used to immediately save current bot data",
                             server_command=True, authorization_level=4)
    def save(self):
        """
        this command is used to immediately save current bot data
        """
        time_stamp = dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
        self.database.save(f"{self.backup_dir}{time_stamp}.pkl")
        return [str(), f"datas were saved successfully with time stamp `{time_stamp}`", self.color]


# TODO: make class developer for some upgrade stuff


class Function(Basic):
    max_image_number = 100
    images = ["images\\dogs\\", "images\\cats\\"]
    # images = [path.abspath("images\\dogs") + "\\", path.abspath("images\\cats") + "\\"]

    leaderboard_dir = "leaderboards\\"
    # path.abspath("leaderboards") + "\\"

    @command_handler.command(server_command=True)
    def alias(self, *args):
        return Alias(self.uid, self.database, self.sid)(*args)

    @command_handler.command(server_command=True)
    def authorization(self, *args):
        return Authorization(self.uid, self.database, self.sid)(*args)

    @command_handler.command(server_command=True, authorization_level=4)
    def backup(self, *args):
        return Backup(self.uid, self.database, self.sid)(*args)

    @command_handler.command(help_message="used to delete message to which is this message referencing")
    def delete(self):
        """
        this command is used to delete messages to which is this (current) message replying,
        it is not server restricted, so you can clean up your dms
        """
        return [str(), "*message was successfully deleted*", 0xffffff, []], None, dict(embed=True, delete=True)

    @command_handler.command(help_message="used to get cat or dog images")
    def get(self, number):
        """
        this command will get you cat or dog images"
        |:parameter number: it needs number in order to get you your picture
        |:return: it will send picture to your dms
        """
        number = int(int(number) % self.max_image_number)
        return f"{Tag(self.uid)} check your dms for your cat or dog image :cat: :dog:", \
               None, \
               dict(dm=[f"{Tag(self.uid)}",
                        f"{self.images[self.database.everyone[self.uid].get_cat(number)]}{number}.jpg"])

    @command_handler.command()
    def help(self, *args):
        prefix = str()
        on_server = False
        authorization_level = 0
        if self.sid is not None:
            prefix = self.database.servers[self.sid].prefix + " "
            on_server = True
            authorization_level = self.database.servers[self.sid].get_authorization_level(self.uid)

        if len(args) > 0:
            args = ' '.join(args)
            if args not in command_handler.help:
                raise Exception("this command either does not exist or does not have its own help message or is only "
                                "command spliter meaning that it is only there to make commands neatly organized")
            raw = command_handler.help[args]
            if raw[0] > authorization_level or raw[3] and not on_server:
                return self.__call__(*args.split(" "))

            raw = raw[2].split("|")
            title = f"{args} [...]"
            description = raw[0]
            message = list(map(lambda x: x.strip()[1:].split(":") + [False], raw[1:]))
        else:
            title = "this is help"
            description = ""
            message = []
            for key, raw in command_handler.help.items():
                if raw[0] > authorization_level or raw[3] and not on_server:
                    continue
                message.append([f"{prefix}{key}", raw[1], False])
        return [title, description, 0x9a25c1, message]

    @command_handler.command(help_message="used to display leaderboard",
                             server_command=True)
    def leaderboard(self):
        board = list()
        file = f"{self.leaderboard_dir}leaderboard - {self.sid}.txt"
        for i in self.database.servers[self.sid].members:
            i = self.database.everyone[i]
            board.insert(bisect_left(board, i.score(), key=lambda x: x[1]), [i.name, i.score()])

        with open(file, "wb") as f:
            f.write("\n".join(map(lambda x: f"{x[0] + 1}. {x[1][0]} - {x[1][1]}",
                                  enumerate(board[::-1]))).encode("utf-16"))
        return "this is leaderboard", file

    @command_handler.command(server_command=True)
    def prefix(self, *args):
        return Prefix(self.uid, self.database, self.sid)(*args)

    @command_handler.command(help_message="picks random number and call 'get' command")
    def random(self):
        number = list(set(range(100)).difference(self.database.everyone[self.uid].history))
        return self.get(number[randint(0, len(number) - 1)])

    @command_handler.command(server_command=True, authorization_level=4)
    def refreshimages(self, *args):
        return RefreshImages(self.uid, self.database, self.sid)(*args)

    @command_handler.command()
    def statistics(self, *args):
        return Statistics(self.uid, self.database, self.sid)(*args)


# TODO: make class History


class Prefix(Basic):

    @command_handler.command(help_message="used to restore the default prefix *('img')*",
                             server_command=True)
    def default(self):
        return self.set("cat")

    @command_handler.command(help_message="used to set server prefix",
                             server_command=True)
    def set(self, prefix):
        if " " in prefix or not prefix:
            return "this prefix is invalid"
        self.database.servers[self.sid].prefix = prefix
        return [str(), f"prefix was successfully changed to: `{prefix}`"]

    @command_handler.command(help_message="used to view current server prefix",
                             server_command=True)
    def view(self):
        return [str(), f"current prefix is: `{self.database.servers[self.sid].prefix}`"]


class RefreshImages(Basic):
    color = 0xff7392
    last_interval = 0  # in minutes

    @command_handler.command(help_message="used to adjust time intervals (minutes) for images refresh",
                             server_command=True, authorization_level=4)
    def interval(self, *args):
        """
        this command is used to view and set time intervals in which are images refreshed
        |:__parameter__ [...]: `[none]` - this will display current interval|n|
                               `[time]` - this will set interval for automatic refresh of images, [time]
                                          has to be interval between 30 and 720 minutes
        """
        if len(args) == 0:
            return [str(),
                    f"current time interval for refresh of images is `{self.database.image_update_interval}` minutes",
                    self.color]
        time = int(args[0])
        if 30 <= int(time) <= 720:
            self.database.image_update_interval = time
            return [str(),
                    f"time interval for refresh of images was successfully changed to `{time}` minutes",
                    self.color]
        else:
            raise Exception("this interval value is invalid")

    @command_handler.command(help_message="used to turn on or off automatic refresh of images",
                             server_command=True, authorization_level=4)
    def manual(self, *args):
        """
        this command is used to turn on or off automatic images refresh or to view the current type of operation
        of refresh of images (manual or automatic)
        |:parameter [...]: `[none]` - this will show the current type of operation of refreshes|n|
                           `true` - this will *disable* automatic refresh of images|n|
                           `false` - this will *enable* automatic refresh of images
        """
        state = "enabled" if self.database.image_update_interval else "disabled"
        if len(args) == 0:
            return [str(), f"automatic refresh of images is currently `{state}`", self.color]

        if args[0].lower() == "true":
            self.last_interval = self.database.image_update_interval
            self.database.image_update_interval = 0
            state = "disabled"
        elif args[0].lower() == "false":
            self.database.image_update_interval = self.last_interval
            state = "enabled"
        return [str(), f"automatic refresh of images was `{state}`", self.color]

    @command_handler.command(help_message="used to immediately initiate refresh of images",
                             server_command=True, authorization_level=4)
    def now(self):
        """
        this command will immediately initiate refresh of images
        """
        return [str(), "refreshing images...", self.color, []], None, dict(embed=True, refreshimages=True)


class Statistics(Basic):
    color = 0x1f8eed

    def __init__(self, uid: int, database: object, sid=None):
        super().__init__(uid, database, sid=sid)
        self.history, self.cat_stats, self.dog_stats = database.everyone[uid].stats()

    @command_handler.command(help_message="used to display all user statistics")
    def all(self, *args):
        self.get_user(*args)
        cat = self.get_stats(True, tag=False)
        dog = self.get_stats(False, tag=False)
        return ["your current stats", f"{Tag(self.uid)}", self.color,
                [("all images received", f"total - {self.cat_stats.all}", True),
                 cat[0], dog[0],
                 ("current score", f"total - {int(self.cat_stats.score)}", True),
                 cat[1], dog[1]]]

    def get_stats(self, is_cat: bool, tag=True):
        item = ["dog", "cat"][is_cat]
        stats = [self.dog_stats, self.cat_stats][is_cat]
        tag = [[], [f"your current {item} stats:\n", f"<@{self.uid}>", self.color]][tag]
        message = [(f"{item}s received", f"total - {stats.count}", not tag),
                   (f"{item} streak stats", f"current - {stats.n}\n"
                                            f"maximal - {stats.max}\n"
                                            f"average - {stats.mean()}", not tag)]
        if tag:
            message = [message]
        return tag + message

    def get_user(self, *args):
        if len(args) > 0:
            tag = Tag(args[0])
            if tag in self.database.servers[self.sid].members:
                self.__init__(int(tag), self.database, sid=self.sid)
            else:
                raise Exception("this user has not used this bot yet")

    @command_handler.command(help_message="used to display all user's dog statistics")
    def dog(self, *args):
        self.get_user(*args)
        return self.get_stats(False)

    @command_handler.command(help_message="used to display all user's cat statistics")
    def cat(self, *args):
        self.get_user(*args)
        return self.get_stats(True)

    @command_handler.command(help_message="used to display score")
    def score(self, *args):
        self.get_user(*args)
        return [str(), f"{Tag(self.uid)}'s current score is {self.database.everyone[self.uid].score()}", self.color]
