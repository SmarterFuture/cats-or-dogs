import discord
import asyncio
from downloader import *
from functions import *
from handler import *
import datetime as dt

bot_id = 0
banner = 0
banners = [discord.Game(name="img random"),
           discord.Activity(type=discord.ActivityType.watching, name="through this new images")]
client = discord.Client()
cooldown = 2  # in seconds
database = UserHandler()
images_refresh_cooldown = 5  # in minutes
last_save_time = dt.datetime.now()
last_update_time = dt.datetime.fromisoformat('2011-11-04')
path = "backups\\"
temp_database = dict()
token = 'OTkxODA1NTA4NDk3NDUzMDk2.G0NKDj.u_8QNwR6O_Ux8JStj_7VibFX6GUrJRD7lY3PI0'
updated = True


async def auto_save():
    global database, last_save_time, temp_database
    await client.wait_until_ready()
    while not client.is_closed():
        time_delta = (dt.datetime.now() - last_save_time).total_seconds() / 60
        if database.auto_save_interval and time_delta >= database.auto_save_interval:
            database.save(f"{path}{dt.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.pkl")
            last_save_time = dt.datetime.now()
            print(f"data were saved successfully at {dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
            temp_database = dict()
        await asyncio.sleep(30)


async def banner_update():
    global banner, banners, database, last_update_time, updated
    await client.wait_until_ready()
    while not client.is_closed():
        time_delta = (dt.datetime.now() - last_update_time).total_seconds() / 60

        if updated:
            banners[1] = discord.Activity(type=discord.ActivityType.watching, name="through this new images")

        if time_delta < 10 and not updated:
            banners[1] = discord.Activity(type=discord.ActivityType.watching, name="over the images updating")

        if time_delta > database.image_update_interval // 5:
            updated = False
            banners[1] = discord.Activity(type=discord.ActivityType.watching,
                                          name=f"for new images in "
                                               f"{round(database.image_update_interval - time_delta)} minutes")

        try:
            await client.change_presence(activity=banners[banner])
            banner = (banner + 1) % len(banners)
            await asyncio.sleep(database.banner_update_interval)
        except ConnectionError:
            pass


async def send_message(content, embed, file, function):
    if content is None and file is None and embed is None:
        return
    if file is not None:
        with open(os.path.abspath(file), 'rb') as f:
            file = discord.File(f)
    await function(content, embed=embed, file=file, mention_author=False)


async def update_images():
    global database, last_update_time, updated
    await client.wait_until_ready()
    while not client.is_closed():
        time_delta = (dt.datetime.now() - last_update_time).total_seconds() / 60
        if database.image_update_interval and time_delta >= database.image_update_interval:
            print("   started to update images")
            last_update_time = dt.datetime.now()
            await get_images(Function.max_image_number, "images\\cats\\", "cats")
            await get_images(Function.max_image_number, "images\\dogs\\", "dogpictures")
            updated = True
            print(f"images were updated (total upgrade time {(dt.datetime.now() - last_update_time).total_seconds()})")
        await asyncio.sleep(30)


@client.event
async def on_ready():
    global bot_id, database
    print(f"bot booted at: {dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    bot_id = client.user.id
    try:
        database.load(path, latest=True)
        print(f"data were loaded successfully at {dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    except Exception as e:
        print(f"previous data could not be loaded because of error: {e}")
    finally:
        await client.change_presence(activity=discord.Game(name="img random"))


@client.event
async def on_message(msg):
    global bot_id, cooldown, temp_database, last_update_time, updated
    uid = msg.author.id

    try:
        sid = msg.guild.id
    except AttributeError:
        sid = None

    if bot_id == uid:
        return

    # formatting message content
    content = list(map(lambda x: x.lower(), msg.content.strip().split()))

    # checking length of message
    if len(content) == 0:
        return

    # validating prefix
    if sid is not None:
        if sid not in database.servers:
            owner_id = msg.guild.owner_id
            database.handle(owner_id, "owner", sid=sid)
            database.servers[sid].set_authorization_level(owner_id, 4)

        prefix = database.servers[sid].prefix
        if content[0] != prefix and Tag(content[0]) != bot_id:
            return
        content = content[1:]

    if len(content) == 0:
        return

    # handling user
    database.handle(uid, msg.author.name, sid=sid)

    # handling cooldown
    if sid is not None:
        last_used_time = database.servers[sid].last_used_time
    else:
        last_used_time = database.everyone[uid].last_used_time

    time_delta = round((dt.datetime.now() - last_used_time).total_seconds(), 1)
    if time_delta < cooldown:
        embed = discord.Embed(description=f"**Error:** this session is still in cooldown "
                                          f"(~{round(cooldown - time_delta, 1)} seconds)", color=0xff0000)
        await send_message(None, embed, None, msg.reply)
        return

    # setting time of last use in session
    if sid is not None:
        database.servers[sid].last_used_time = dt.datetime.now()
    else:
        database.everyone[uid].last_used_time = dt.datetime.now()

    # creating local database for faster operation
    if uid not in temp_database:
        temp_database[uid] = Function(uid, database, sid)
    functions = temp_database[uid]
    functions.sid = sid

    # handling request
    output, file, special = functions(*content)

    # handling delete message
    if "delete" in special:
        if msg.reference is None:
            special["err"] = True
            output = "this message is not pointing to anything"
        else:
            try:
                channel_id, message_id = msg.reference.channel_id, msg.reference.message_id
                tmp = await client.get_channel(int(channel_id)).fetch_message(int(message_id))
                await tmp.delete()
            except Exception:
                special["err"] = True
                output = "this message is not owned by this bot"

    # handling error messages
    if "err" in special:
        if special["err"]:
            embed = discord.Embed(description=f"**Error:** {output}", color=0xff0000)
            await send_message(None, embed, None, msg.reply)
            return

    # handling embed
    embed = None
    if "embed" in special:
        if special["embed"]:
            embed = discord.Embed(title=output[0], description=output[1], color=output[2])
            for i in output[3]:
                embed.add_field(name=i[0], value=i[1], inline=i[2])
            output = None

    # handling immediate refresh of images
    if "refreshimages" in special:
        time_delta = round((dt.datetime.now() - last_update_time).total_seconds() / 60, 1)
        if time_delta < images_refresh_cooldown:
            embed = discord.Embed(description=f"**Error:** this command is still in cooldown "
                                              f"(~{round(images_refresh_cooldown - time_delta, 1)} minutes)",
                                  color=0xff0000)
            await send_message(None, embed, None, msg.reply)
            return
        last_update_time = dt.datetime.fromisoformat('2011-11-04')
        updated = False
        await send_message(None, embed, None, msg.reply)
        await update_images()
        return

    # sending result to server
    await send_message(output, embed, file, msg.reply)

    # sending to tmp
    if "dm" in special:
        output, file = special["dm"]
        await send_message(output, None, file, msg.author.send)


client.loop.create_task(auto_save())
client.loop.create_task(update_images())
client.loop.create_task(banner_update())
client.run(token)
