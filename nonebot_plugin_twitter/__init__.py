import os
from nonebot import require,get_driver,get_bot,on_command
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN,GROUP_OWNER
from nonebot.adapters.onebot.v11 import Message,MessageEvent,Bot,GroupMessageEvent,MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.log import logger
import nonebot
from nonebot.adapters.onebot.v11.adapter import Adapter
from nonebot.exception import MatcherException
from nonebot.plugin import PluginMetadata
from pathlib import Path
import json
import time
from httpx import AsyncClient
import asyncio
import tweepy
from .config import Config,__version__

config_dev = Config.parse_obj(get_driver().config)

__plugin_meta__ = PluginMetadata(
    name="twitter 推特订阅",
    description="订阅 twitter 推文",
    usage="""
    """,
    type="application",
    config=Config,
    homepage="https://github.com/nek0us/nonebot-plugin-twitter",
    supported_adapters={"~onebot.v11"},
    extra={
        "author":"nek0us",
        "version":__version__,
        "priority":config_dev.command_priority
    }
)

if not config_dev.Bearer_Token:
    logger.warning("Bearer_Token 未配置")
    config_dev.plugin_enabled = False
        
if config_dev.plugin_enabled:
    # Path
    dirpath = Path() / "data" / "twitter"
    dirpath.mkdir(parents=True, exist_ok=True)
    dirpath = Path() / "data" / "twitter" / "cache"
    dirpath.mkdir(parents=True, exist_ok=True)
    dirpath = Path() / "data" / "twitter" / "group_list.json"
    dirpath.touch()
    if not dirpath.stat().st_size:
        dirpath.write_text("{}")
    
    # Twitter token
    client = tweepy.Client(
        bearer_token=config_dev.Bearer_Token
    )     
    if config_dev.Proxy:
        # Proxy
        client.session.proxies = {
            "http":config_dev.Proxy,
            "https":config_dev.Proxy
        }
    
    @scheduler.scheduled_job("interval",minutes=15,id="twitter",misfire_grace_time=600)
    async def now_twitter():
        task_list = []
        group_list = json.loads(dirpath.read_text("utf8"))
        for group_num in group_list:
            if group_num and group_list[group_num]["status"] == "on":
                task_list.extend(
                    get_status(group_list, group_num, user_id, group_list[group_num][str(user_id)][1])
                    for user_id in group_list[group_num]
                    if user_id != "status"
                )
        asyncio.gather(*task_list)


# 数据结构

# {
#     group_num[str]:{
#         user_id[str]:[
#             user_name[str],
#             since_id[int],
#             r18[bool]
#             ],
#         status:"on/off",
        
#     }
# }

        
async def get_status(group_list, group_num, user_id,since_id):
    try:
        ne = client.get_users_tweets(
        id=user_id,
        max_results = 5,
        since_id = since_id
        )
        if ne.data:
            path_res = await get_tweet_for_id(user_id,group_list[group_num][user_id][2],group_list[group_num][user_id][0])
            task_res = [msg_type(2854196310, path,name=group_list[group_num][user_id][0]) for path in path_res]
            bots = nonebot.get_adapter(Adapter).bots
            # 发送异步后的数据
            for bot in bots:
                try:
                    await bots[bot].send_group_forward_msg(group_id=int(group_num), messages=task_res)
                except Exception:
                    pass
                    #await bot.send_group_forward_msg(group_id=event.group_id, messages=task_res)
            # else:
            #     await bot.send_private_forward_msg(user_id=event.user_id, messages=aio_task_res)

            # 清除垃圾
            for path in path_res:
                os.unlink(path)
    except Exception as e:
        pass
    
async def get_tweet_for_id(id: int,r18: bool,name: str):
    '''
    id: 推文id
    r18：是否发送r18
    name：推主name'''    
    tweet = client.get_tweet(id=id,
                            media_fields="duration_ms,height,media_key,preview_image_url,public_metrics,type,url,width,alt_text,variants".split(
                                ","),
                            expansions=[
                                'entities.mentions.username',
                                'attachments.media_keys',
                            ],
                    tweet_fields=["possibly_sensitive"])
    if tweet.data.possibly_sensitive and not r18:
        raise ValueError("该条为r18，丢弃")
        # 主要内容
    tweet_json = tweet.includes
    task = []
    # 逐个判断是照片还是视频
    task.append(MessageSegment.node_custom(
        user_id=2854196310,
        nickname=name,
        content=Message(tweet.data.text)
    ))
    for tweet_single in tweet_json['media']:
        # 图片
        if tweet_single['type'] == "photo":
            # print(tweet_single.url)
            task.append(get_pic(tweet_single.url))
            # await twit.send(Message(f"[CQ:image,file=file:///{path}]"))
            # os.unlink(f"{path}")
        # 视频
        elif tweet_single['type'] == "video":
            # print(tweet_single['variants'][0]['url'])
            task.append(get_video(tweet_single['variants'][0]['url']))
            # print(path)
            # await twit.send(Message(f"[CQ:video,file=file:///{path}]"))
            # os.unlink(f"{path}")
    path_res = await asyncio.gather(*task)
    return path_res
        
        
def msg_type(user_id:int, task: str,name: str):
    if task.endswith("jpg") or task.endswith("png"):
        print(f"file:///{task}]")
        return MessageSegment.node_custom(user_id=user_id, nickname=name,
                                   content=Message(MessageSegment.image(f"file:///{task}")))
    elif task.endswith("mp4"):
        return MessageSegment.node_custom(user_id=user_id, nickname=name,
                                          content=Message(MessageSegment.video(f"file:///{task}")))        
        
        #print("色色可不好哦~")
    # print(f"链接为小蓝鸟：{tweet.data.text}")
    
async def get_pic(url: str) -> Path:
    path = Path() / "data" / "twitter" / "cache" /  url.split('/').pop()
    if config_dev.Proxy:
        async with AsyncClient(proxies=f"http://{config_dev.Proxy}") as client:
            res = await client.get(url)
            if res.status_code != 200:
                raise ValueError("图片下载失败")
            with open(path,'wb') as file:
                file.write(res.read())
            return path
    else:
        async with AsyncClient() as client:
            res = await client.get(url)
            if res.status_code != 200:
                raise ValueError("图片下载失败")
            with open(path,'wb') as file:
                file.write(res.read())
            return path

async def get_video(url: str) -> Path:
    path = Path() / "data" / "twitter" / "cache" /  url.split('/').pop()
    if config_dev.Proxy:
        async with AsyncClient(proxies=f"http://{config_dev.Proxy}") as client:
            async with client.stream('GET',url) as res:
                if res.status_code != 200:
                    raise ValueError("视频下载失败")
                with open(path,'wb') as file:
                    async for chunk in res.aiter_bytes():
                        file.write(chunk)
                return path
    else:
        async with AsyncClient() as client:
            async with client.stream('GET',url) as res:
                if res.status_code != 200:
                    raise ValueError("视频下载失败")
                with open(path,'wb') as file:
                    async for chunk in res.aiter_bytes():
                        file.write(chunk)
                return path
    
    
save = on_command("关注推主",block=True,priority=config_dev.command_priority)
@save.handle()
async def save_handle(bot:Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    if isinstance(event,GroupMessageEvent):
        user_id = get_id(arg.extract_plain_text())
        res = client.get_users_tweets(
            id=user_id,
            max_results = 5
        )
        since_id = res.data[0].id
        if user_id == "未找到":
            group_list = json.loads(dirpath.read_text("utf8"))
            if str(event.group_id) not in group_list:
                group_list[str(event.group_id)] = {"status":"on"}
            group_list[str(event.group_id)][str(user_id)] = [arg.extract_plain_text(),since_id,True]
            dirpath.write_text(json.dumps(group_list))
            await matcher.finish(f"绑定成功了")
        
async def get_id(name: str) -> str:
    '''return user_id from user_name'''
    try:
        return client.get_user(username="nek0us").data.id
    except:
        return "未找到"
        
        

# 数据结构

# {
#     group_num[str]:{
#         user_id[str]:[
#             user_name[str],
#             since_id[int],
#             r18[bool]
#             ],
#         status:"on/off",
        
#     }
# }
