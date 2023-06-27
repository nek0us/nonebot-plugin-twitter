import httpx
from bs4 import BeautifulSoup
import re
import asyncio
from nonebot.adapters.onebot.v11 import Message,MessageEvent,Bot,GroupMessageEvent,MessageSegment

async def a():
    async with httpx.AsyncClient(proxies="http://127.0.0.1:1090") as client:
        res = await client.get(url="https://twitter.owacon.moe/nek0us/status/1673578737097637888",cookies={"hlsPlayback": "on"})
        result = {}
        if res.status_code ==200:
            result["status"] = True
            soup = BeautifulSoup(res.text,"html.parser")
            # text
            # result["text"] = match[0].text if (match := soup.find_all('div', class_='tweet-content media-body')) else ""
            old_match = soup.find_all("div",class_="tweet-body")
            new_match = []
            for match in old_match:
                if match.contents[3].attrs["class"] == ['tweet-content', 'media-body']:
                    new_match.append(match.contents)

            all_msg = Message()
            for message in new_match:
                msg = Message()
                message = list(set(message))
                message.remove("\n")
                for tweet in message:
                    if not tweet.attrs:
                        continue
                    if tweet.attrs["class"] == ['tweet-content', 'media-body']:
                        msg+=Message(tweet.contents[0])
                    elif tweet.attrs["class"] == ['attachments']:
                        pic = tweet.next.next.next.next.attrs["src"]
                    elif tweet.attrs["class"] == ['attachments','card']:
                        # 存在
                        a = 0
            # pic
            if pic_list := soup.find_all('a', class_='still-image'):
                result["pic_url_list"] = [x.attrs["href"] for x in pic_list]
            else:
                result["pic_url_list"] = []
            # video
            if video_list := soup.find_all('video'):
                # result["video_url"] = video_list[0].attrs["data-url"]
               #  result["video_url"] = f"https://twitter.com/{user_name}/status/{tweet_id}"
               pass
            else:
                result["video_url"] = ""
            # r18
            result["r18"] = bool(r18 := soup.find_all('div', class_='unavailable-box'))
        else:
            result["status"] = False
            
asyncio.run(a())