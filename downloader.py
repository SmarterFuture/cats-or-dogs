import aiofiles
import aiohttp
import asyncpraw
import os

from PIL import Image


async def download_image(name, path, url):

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"{path}{name}r.jpg", mode='wb') as f:
                    await f.write(await resp.read())
    while True:
        try:
            await compress(name, path, f"{path}{name}r.jpg")
        except Exception:
            pass
        finally:
            break


async def compress(name, path, source):
    q = 85

    img = Image.open(source)
    if os.path.getsize(source) > 500000:
        q = 70

    h, w = img.size
    if (h + w) >= 5000:
        h, w = (2000, w * 2000 // h) if h >= w else (h * 2000 // w, 2000)
        img = img.resize((h, w), Image.ANTIALIAS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(f"{path}{name}.jpg", quality=q, optimize=True)

    if os.path.getsize(f"{path}{name}.jpg") > os.path.getsize(source):
        os.replace(source, f"{path}{name}.jpg")


async def get_images(amount, path, theme):

    reddit = asyncpraw.Reddit(
        client_id="i4Dyb-SMacLBbw",
        client_secret="9x_o0dfsLcJYdCBapYPcBZCHulwIhw",
        user_agent="bot123", )

    subreddit = await reddit.subreddit(theme)
    count = 0

    async for submission in subreddit.new(limit=None):
        url = str(submission.url)
        if url.endswith("jpg") or url.endswith("jpeg") or url.endswith("png"):
            await download_image(count, path, url)
            count += 1

        if count == amount:
            return
