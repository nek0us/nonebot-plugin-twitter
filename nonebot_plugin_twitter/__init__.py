import os
import sys
from nonebot import require,on_command,get_driver
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import Message,MessageEvent,Bot,GroupMessageEvent,MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.log import logger
from nonebot.adapters.onebot.v11.adapter import Adapter
from nonebot.exception import FinishedException
from nonebot.plugin import PluginMetadata
from pathlib import Path
import json
import random
from httpx import AsyncClient,Client
import asyncio
from playwright.async_api import async_playwright
from .config import Config,__version__,website_list,config_dev
from .api import *


__plugin_meta__ = PluginMetadata(
    name="twitter 推特订阅",
    description="订阅 twitter 推文",
    usage="""
|     指令    |权限|需要@|   范围   | 说明 |
|   关注推主   |无 | 否  | 群聊/私聊 | 关注，指令格式：“关注推主 <推主id> [r18]” r18为可选参数，不开启和默认为不推送r18推文|
|   取关推主   |无 | 否  | 群聊/私聊 | 取关切割 |
|   推主列表   |无 | 否  | 群聊/私聊 | 展示列表 |
| 推文推送关闭 |群管| 否 | 群聊/私聊 | 关闭推送 |
| 推文推送开启 |群管| 否 | 群聊/私聊 | 开启推送 |
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

web_list = []
if config_dev.twitter_website:
    logger.info("使用自定义 website")
    web_list.append(config_dev.twitter_website)
web_list += website_list

browser = ""
get_driver = get_driver()
@get_driver.on_startup
async def pywt_init():
    if config_dev.twitter_htmlmode:
        global browser
        if not await is_firefox_installed():
            logger.info("Firefox browser is not installed, installing...")
            install_firefox()
            logger.info("Firefox browser has been successfully installed.")
        playwright_manager = async_playwright()
        playwright = await playwright_manager.start()
        browser = await playwright.firefox.launch(slow_mo=50)

        

with Client(proxies=config_dev.twitter_proxy,http2=True) as client:
    for url in web_list:
        try:
            res = client.get(f"{url}/elonmusk/status/1741087997410660402")
            if res.status_code == 200:
                logger.info(f"website: {url} ok!")
                config_dev.twitter_url = url
                break
            else:
                logger.info(f"website: {url} failed!")
        except Exception as e:
            logger.debug(f"website选择异常：{e}")
            continue
        
# 清理垃圾
@scheduler.scheduled_job("cron",hour="5")
def clean_pic_cache():
    path = Path() / "data" / "twitter" / "cache"
    filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    timeline = int(datetime.now().timestamp()) - 60 * 60 * 5
    [os.remove(path / f) for f in filenames if int(f.split(".")[0]) <= timeline]

# Path
dirpath = Path() / "data" / "twitter"
dirpath.mkdir(parents=True, exist_ok=True)
dirpath = Path() / "data" / "twitter" / "cache"
dirpath.mkdir(parents=True, exist_ok=True)
dirpath = Path() / "data" / "twitter" / "twitter_list.json"
dirpath.touch()
if not dirpath.stat().st_size:
    dirpath.write_text("{}")
    
if config_dev.plugin_enabled:
    if not config_dev.twitter_url:
        logger.debug(f"website 推文服务器为空，跳过推文定时检索")
    else:
        @scheduler.scheduled_job("interval",minutes=3,id="twitter",misfire_grace_time=179)
        async def now_twitter():
            twitter_list = json.loads(dirpath.read_text("utf8"))
            twitter_list_task = [
                get_status(user_name, twitter_list) for user_name in twitter_list
            ]
            result = await asyncio.gather(*twitter_list_task)
            if config_dev.twitter_website == "":
                # 使用默认镜像站
                true_count = sum(1 for elem in result if elem)

                if true_count < len(result) / 2:
                    config_dev.twitter_url = get_next_element(website_list,config_dev.twitter_url)
                    logger.debug(f"检测到当前镜像站出错过多，切换镜像站至：{config_dev.twitter_url}")
                    
async def get_status(user_name,twitter_list) -> bool:
    # 获取推文
    try:
        line_new_tweet_id = await get_user_newtimeline(user_name,twitter_list[user_name]["since_id"])
        if line_new_tweet_id and line_new_tweet_id != "not found":
            # update tweet
            tweet_info = await get_tweet(browser,user_name,line_new_tweet_id) # type:ignore
            if not tweet_info["status"] and not tweet_info["html"]:
                # 啥都没获取到
                logger.warning(f"{user_name} 的推文 {line_new_tweet_id} 获取失败")
                return False
            elif not tweet_info["status"] and tweet_info["html"]:
                # 起码有个截图
                logger.debug(f"{user_name} 的推文 {line_new_tweet_id} 获取失败，但截图成功，准备发送截图")
                msg = []
                if config_dev.twitter_htmlmode:
                    # 有截图
                    bytes_size = sys.getsizeof(tweet_info["html"]) / (1024 * 1024)
                    msg.append(MessageSegment.image(tweet_info["html"]))
                    if config_dev.twitter_node:
                        # 合并转发
                        msg.append(MessageSegment.node_custom(
                            user_id=config_dev.twitter_qq,
                            nickname=twitter_list[user_name]["screen_name"],
                            content=Message(MessageSegment.image(tweet_info["html"]))
                        ))
                        await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg))
                    else:
                        # 直接发送
                        await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg),"direct")
                        
                    return True
                return False
            # elif tweet_info["status"] and not tweet_info["html"]:
            #     # 只没有截图？不应该啊
            #     pass
            # elif tweet_info["status"] and tweet_info["html"]:
            else:
                # 有没有截图不知道，内容信息是真有
                task = []
                all_msg = []
                
                # html模式
                if config_dev.twitter_htmlmode:
                    bytes_size = sys.getsizeof(tweet_info["html"]) / (1024 * 1024)
                    all_msg.append(MessageSegment.image(tweet_info["html"]))
                
                # 返回图片
                if tweet_info["pic_url_list"]:
                    for url in tweet_info["pic_url_list"]:
                        all_msg.append(await get_pic(url))
                        
                # 视频，返回本地视频路径
                if tweet_info["video_url"]:
                    all_msg.append(await get_video(tweet_info["video_url"]))
                    
                # 准备发送消息
                if config_dev.twitter_node:
                    # 以合并方式发送
                    msg = []
                    for value in  all_msg:
                        msg.append(
                            MessageSegment.node_custom(
                                user_id=config_dev.twitter_qq,
                                nickname=twitter_list[user_name]["screen_name"],
                                content=Message(value)
                            )
                        )
                    if not config_dev.twitter_no_text:
                        # 开启了媒体文字
                        for x in tweet_info["text"]:
                            msg.append(MessageSegment.node_custom(
                                user_id=config_dev.twitter_qq,
                                nickname=twitter_list[user_name]["screen_name"],
                                content=
                                Message(x)
                            ))
                    # 发送合并消息    
                    await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg))
                else:
                    # 以直接发送的方式
                    if all_msg[-1].type == "video":
                        # 有视频先发视频
                        video_msg = all_msg.pop()
                        # msg = []
                        # msg.append(
                        #     MessageSegment.node_custom(
                        #         user_id=config_dev.twitter_qq,
                        #         nickname=twitter_list[user_name]["screen_name"],
                        #         content=Message(video_msg)
                        #     )
                        # )
                        # await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg),"video")
                        await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(video_msg),"video")
                    if not config_dev.twitter_no_text:    
                        # 开启了媒体文字
                        all_msg.append(MessageSegment.text('\n\n'.join(tweet_info["text"])))
                    # 剩余部分直接发送
                    await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(all_msg),"direct")
                    
                    
                # 更新本地缓存
                twitter_list[user_name]["since_id"] = line_new_tweet_id
                dirpath.write_text(json.dumps(twitter_list))
                return True
        return True
    except Exception as e:
        logger.debug(f"获取 {user_name} 的推文出现异常：{e}")
        return False


save = on_command("关注推主",block=True,priority=config_dev.command_priority)
@save.handle()
async def save_handle(bot:Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    if not config_dev.twitter_url:
        await matcher.finish("website 推文服务器访问失败，请检查连通性或代理")
    data = []
    if " " in arg.extract_plain_text():
        data = arg.extract_plain_text().split(" ")
    else:
        data.append(arg.extract_plain_text())
        data.append("")
    user_info = await get_user_info(data[0])
    
    if not user_info["status"]:
        await matcher.finish(f"未找到 {data[0]}")

    tweet_id = await get_user_newtimeline(data[0])
    
    twitter_list = json.loads(dirpath.read_text("utf8"))
    if isinstance(event,GroupMessageEvent):
        if data[0] not in twitter_list:
            twitter_list[data[0]] = {
                "group":{
                    str(event.group_id):{
                        "status":True,
                        "r18":True if 'r18' in data[1:] else False,
                        "media":True if '媒体' in data[1:] else False
                    }
                },
                "private":{}
            }
        else:
            twitter_list[data[0]]["group"][str(event.group_id)] = {
                        "status":True,
                        "r18":True if 'r18' in data[1:] else False,
                        "media":True if '媒体' in data[1:] else False
                    }
    else:
        if data[0] not in twitter_list:
            twitter_list[data[0]] = {
                "group":{},
                "private":{
                    str(event.user_id):{
                        "status":True,
                        "r18":True if 'r18' in data[1:] else False,
                        "media":True if '媒体' in data[1:] else False
                    }
                }
            }
        else:
            twitter_list[data[0]]["private"][str(event.user_id)] = {
                        "status":True,
                        "r18":True if 'r18' in data[1:] else False,
                        "media":True if '媒体' in data[1:] else False
                    }
            
    twitter_list[data[0]]["since_id"] = tweet_id
    twitter_list[data[0]]["screen_name"] = user_info["screen_name"]
    dirpath.write_text(json.dumps(twitter_list))
    await matcher.finish(f"id:{data[0]}\nname:{user_info['screen_name']}\n{user_info['bio']}\n订阅成功")
        

delete = on_command("取关推主",block=True,priority=config_dev.command_priority)
@delete.handle()
async def delete_handle(bot:Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    twitter_list = json.loads(dirpath.read_text("utf8"))
    if arg.extract_plain_text() not in twitter_list:
        await matcher.finish(f"未找到 {arg}")

    if isinstance(event,GroupMessageEvent):
        if str(event.group_id) not in twitter_list[arg.extract_plain_text()]["group"]:
            await matcher.finish(f"本群未订阅 {arg}")
            
        twitter_list[arg.extract_plain_text()]["group"].pop(str(event.group_id))
        
    else:
        if str(event.user_id) not in twitter_list[arg.extract_plain_text()]["private"]:
            await matcher.finish(f"未订阅 {arg}")
            
        twitter_list[arg.extract_plain_text()]["private"].pop(str(event.user_id))
    pop_list = []
    for user_name in twitter_list:
        if twitter_list[user_name]["group"] == {} and twitter_list[user_name]["private"] == {}:
            pop_list.append(user_name)
            
    for user_name in pop_list:
        twitter_list.pop(user_name)

    dirpath.write_text(json.dumps(twitter_list))
    
    await matcher.finish(f"取关 {arg.extract_plain_text()} 成功")
    
follow_list = on_command("推主列表",block=True,priority=config_dev.command_priority)
@follow_list.handle()
async def follow_list_handle(bot:Bot,event: MessageEvent,matcher: Matcher):
    
    twitter_list = json.loads(dirpath.read_text("utf8"))
    msg = []
    
    if isinstance(event,GroupMessageEvent):
        for user_name in twitter_list:
            if str(event.group_id) in twitter_list[user_name]["group"]:
                msg += [
                    MessageSegment.node_custom(
                        user_id=config_dev.twitter_qq, nickname=twitter_list[user_name]["screen_name"], content=Message(
                            f"{user_name}  {'r18' if twitter_list[user_name]['group'][str(event.group_id)]['r18'] else ''}  {'媒体' if twitter_list[user_name]['group'][str(event.group_id)]['media'] else ''}"
                            )
                    )
                ]
        await bot.send_group_forward_msg(group_id=event.group_id, messages=msg)
    else:
        for user_name in twitter_list:
            if str(event.user_id) in twitter_list[user_name]["private"]:
                msg += [
                    MessageSegment.node_custom(
                        user_id=config_dev.twitter_qq, nickname=twitter_list[user_name]["screen_name"], content=Message(
                            f"{user_name}  {'r18' if twitter_list[user_name]['private'][str(event.user_id)]['r18'] else ''}  {'媒体' if twitter_list[user_name]['private'][str(event.user_id)]['media'] else ''}"
                            )
                    )
                ]
        await bot.send_private_forward_msg(user_id=event.user_id, messages=msg)          
    
    await matcher.finish()


async def is_rule(event:MessageEvent) -> bool:
    if isinstance(event,GroupMessageEvent):
        if event.sender.role in ["owner","admin"]:
            return True
        return False
    else:
        return True
    
twitter_status = on_command("推文推送",block=True,rule=is_rule,priority=config_dev.command_priority)
@twitter_status.handle()
async def twitter_status_handle(bot:Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    twitter_list = json.loads(dirpath.read_text("utf8"))
    try:
        if isinstance(event,GroupMessageEvent):
            for user_name in twitter_list:
                if str(event.group_id) in twitter_list[user_name]["group"]:
                    if arg.extract_plain_text() == "开启":
                        twitter_list[user_name]["group"][str(event.group_id)]["status"] = True
                    elif arg.extract_plain_text() == "关闭":
                        twitter_list[user_name]["group"][str(event.group_id)]["status"] = False
                    else:
                        await matcher.finish("错误指令")
        else:
            for user_name in twitter_list:
                if str(event.user_id) in twitter_list[user_name]["private"]:
                    if arg.extract_plain_text() == "开启":
                        twitter_list[user_name]["private"][str(event.user_id)]["status"] = True
                    elif arg.extract_plain_text() == "关闭":
                        twitter_list[user_name]["private"][str(event.user_id)]["status"] = False
                    else:
                        await matcher.finish("错误指令")
        dirpath.write_text(json.dumps(twitter_list))
        await matcher.finish(f"推送已{arg.extract_plain_text()}")
    except FinishedException:
        pass
    except Exception as e:
        await matcher.finish(f"异常:{e}")

