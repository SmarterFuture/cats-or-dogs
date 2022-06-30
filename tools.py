class CList:

    def __contains__(self, item):
        return self.fast.__contains__(item)

    def __init__(self, real: list, length: int):
        real_length = len(real)
        self.real = list(real) + [None] * (length - real_length)
        self.fast = set(real)
        self.__pointer = real_length
        self.__length = length

    def __iter__(self):
        self.__i = 0
        return iter(self.real)

    def __next__(self):
        if self.__i < self.__length:
            self.__i += 1
            return self.real[(self.__pointer + self.__i - 1) % self.__length]
        else:
            self.__i = 0
            raise StopIteration()

    def append(self, item):
        self.fast.discard(self.real[self.__pointer])
        self.real[self.__pointer] = item
        self.__pointer = (self.__pointer + 1) % self.__length
        self.fast.add(item)

    def discard(self, item):
        self.fast.discard(item)


class CommandHandler:

    def __init__(self):
        self.commands = set()
        self.help = dict()

    def command(self, help_message=None, authorization_level=0, server_command=False):
        def real(function):
            self.commands.add(function.__name__)

            if help_message is not None:
                doc = function.__doc__
                if function.__doc__ is None:
                    doc = "detailed help preview is not available"
                doc = " ".join(map(lambda x: x.strip().replace("|n|", "\n"), doc.split("\n")))
                temp_help_message = [authorization_level, help_message, doc, server_command]

                self.help[function.__qualname__.lower().replace("function.",
                                                                str()).replace(".", " ")] = temp_help_message

            def wrap(main: object, *args):
                if server_command:
                    if main.sid is None:
                        return "this command works only on servers", None, dict(err=True)
                if authorization_level > 0:
                    if not main.is_authorized(authorization_level):
                        return "user is not authorized to run this command", None, dict(err=True)
                try:
                    special = dict(err=False)
                    out = function(main, *args)
                    if type(out) == list:
                        out += [0x00a428, []][len(out) - 2:]
                        out = [out]
                        special["embed"] = True
                    if type(out) == str:
                        out = [out]
                    return *out, *[None, special][len(out) - 1:]
                except Exception as e:
                    return str(e), None, dict(err=True)

            return wrap

        return real


class Tag:

    def __bool__(self):
        return bool(self.id)

    def __eq__(self, item):
        return self.id == int(item)

    def __hash__(self):
        return hash(self.id)

    def __init__(self, n):
        try:
            self.id = int(str(n).replace("<@", "").replace(">", "").replace("!", ""))
        except ValueError:
            self.id = 0

    def __int__(self):
        return self.id

    def __repr__(self):
        return f"<@{self.id}>" if self.id else ""
