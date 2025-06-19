import os
import sys
from nonebot import on_regex, require,on_command,get_driver
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import Message,MessageEvent,Bot,GroupMessageEvent,MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,RegexStr
from nonebot.log import logger
from nonebot.adapters.onebot.v11.adapter import Adapter
from nonebot.exception import FinishedException
from nonebot.plugin import PluginMetadata
from pathlib import Path
from importlib.metadata import version
import json
import random
from httpx import AsyncClient,Client
import asyncio
from playwright.async_api import async_playwright
from .config import Config, get_plugin_config, plugin_config,website_list
from .api import *


__plugin_meta__ = PluginMetadata(
    name="twitter 推特订阅",
    description="订阅 twitter 推文",
    usage="""
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| 关注推主 | 无 | 否 | 群聊/私聊 | 关注，指令格式：“关注推主 <推主id> [r18] [媒体]”|
| 取关推主 | 无 | 否 | 群聊/私聊 | 取关切割 |
| 推主列表 | 无 | 否 | 群聊/私聊 | 展示列表 |
| 推文列表 | 无 | 否 | 群聊/私聊 | 展示最多5条时间线推文，指令格式：“推文列表 <推主id>” |
| 推文推送关闭 | 无 | 否 | 群聊/私聊 | 关闭推送 |
| 推文推送开启 | 无 | 否 | 群聊/私聊 | 开启推送 |
| 推文链接识别关闭 | 无 | 否 | 群聊 | 关闭链接识别 |
| 推文链接识别开启 | 无 | 否 | 群聊 | 开启链接识别 |
    """,
    type="application",
    config=Config,
    homepage="https://github.com/nek0us/nonebot-plugin-twitter",
    supported_adapters={"~onebot.v11"},
    extra={
        "author":"nek0us",
        "version": version("nonebot_plugin_twitter"),
        "priority":plugin_config.command_priority
    }
)

web_list = []
if plugin_config.twitter_website:
    logger.info("使用自定义 website")
    web_list.append(plugin_config.twitter_website)
web_list += website_list

get_driver = get_driver()
@get_driver.on_startup
async def pywt_init():
    if plugin_config.twitter_htmlmode:
        if not await is_firefox_installed():
            logger.info("Firefox browser is not installed, installing...")
            install_firefox()
            logger.info("Firefox browser has been successfully installed.")
        
async def create_browser():
    playwright_manager = async_playwright()
    playwright = await playwright_manager.start()
    browser = await playwright.firefox.launch(slow_mo=50,proxy={"server": plugin_config.twitter_proxy})
    return playwright,browser
        

with Client(proxies=plugin_config.twitter_proxy,http2=True) as client:
    for url in web_list:
        try:
            full_url = f"{url}/elonmusk/status/1741087997410660402"
            res = client.get(full_url, timeout=60)  # 添加超时
            if res.status_code == 200:
                logger.info(f"website: {url} ok!")
                plugin_config.twitter_url = url
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

    
        
if plugin_config.plugin_enabled:
    if not plugin_config.twitter_url:
        logger.debug(f"website 推文服务器为空，跳过推文定时检索")
    else:
        @scheduler.scheduled_job("interval", minutes=3, id="twitter", misfire_grace_time=179)
        async def now_twitter():
            playwright, browser = await create_browser()
            twitter_list = json.loads(dirpath.read_text("utf8"))
            results = []
            try:
                for user_name in twitter_list:
                    # 检查单个用户状态
                    result = await get_status(user_name, twitter_list, browser)
                    results.append(result)
                    # 检查完一个用户后等待5秒再检查下一个
                    await asyncio.sleep(5)
                    
                if plugin_config.twitter_website == "":
                    true_count = sum(1 for elem in results if elem)
                    if true_count < len(results) / 2:
                        plugin_config.twitter_url = get_next_element(website_list, plugin_config.twitter_url)
                        logger.debug(f"检测到当前镜像站出错过多，切换镜像站至：{plugin_config.twitter_url}")
            except Exception as e:
                logger.warning(f"twitter 任务出错{e}")
            finally:
                await browser.close()
                await playwright.stop()
                
async def get_status(user_name,twitter_list,browser:Browser) -> bool:
    # 获取推文
    try:
        line_new_tweet_id = await get_user_newtimeline(user_name,twitter_list[user_name]["since_id"])
        if line_new_tweet_id and line_new_tweet_id != "not found":
            # update tweet
            tweet_info = await get_tweet(browser,user_name,line_new_tweet_id)
            return await tweet_handle(tweet_info,user_name,line_new_tweet_id,twitter_list)
        return True
    except Exception as e:
        logger.debug(f"获取 {user_name} 的推文出现异常：{e}")
        return False


save = on_command("关注推主",block=True,priority=plugin_config.command_priority)
@save.handle()
async def save_handle(bot:Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    if not plugin_config.twitter_url:
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
        

delete = on_command("取关推主",block=True,priority=plugin_config.command_priority)
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
    
follow_list = on_command("推主列表",block=True,priority=plugin_config.command_priority)
@follow_list.handle()
async def follow_list_handle(bot:Bot,event: MessageEvent,matcher: Matcher):
    
    twitter_list = json.loads(dirpath.read_text("utf8"))
    msg = []
    
    if isinstance(event,GroupMessageEvent):
        for user_name in twitter_list:
            if str(event.group_id) in twitter_list[user_name]["group"]:
                msg += [
                    MessageSegment.node_custom(
                        user_id=plugin_config.twitter_qq, nickname=twitter_list[user_name]["screen_name"], content=Message(
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
                        user_id=plugin_config.twitter_qq, nickname=twitter_list[user_name]["screen_name"], content=Message(
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
    
twitter_status = on_command("推文推送",block=True,rule=is_rule,priority=plugin_config.command_priority)
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

# pat_twitter = on_regex(r'(twitter\.com|x\.com)/[a-zA-Z0-9_]+/status/\d+',priority=plugin_config.command_priority)
# @pat_twitter.handle()
# async def pat_twitter_handle(bot: Bot,event: MessageEvent,matcher: Matcher,text: str = RegexStr()):
#     logger.info(f"检测到推文链接 {text}")
#     link_list = json.loads(linkpath.read_text("utf8"))
#     playwright,browser = await create_browser()
#     try:
#         if isinstance(event,GroupMessageEvent):
#             # 是群，处理一下先
#             if str(event.group_id) not in link_list:
#                 link_list[str(event.group_id)] = {"link":True}
#                 linkpath.write_text(json.dumps(link_list))
            
#             if not link_list[str(event.group_id)]["link"]:
#                 # 关闭了链接识别
#                 logger.info(f"根据群设置，不获取推文链接内容 {text}")
#                 await matcher.finish()
#         # 处理完了 继续
        
#         # x.com/username/status/tweet_id     
#         tmp = text.split("/")
#         user_name = tmp[1]
#         tweet_id = tmp[-1]
        
#         tweet_info = await get_tweet(browser,user_name,tweet_id)
#         msg = await tweet_handle_link(tweet_info,user_name,tweet_id)
#         if plugin_config.twitter_node:
#             if isinstance(event,GroupMessageEvent):
#                 await bot.send_group_forward_msg(group_id=int(event.group_id), messages=msg)
#             else:
#                 await bot.send_private_forward_msg(user_id=int(event.user_id), messages=msg)
#         else:
#             await matcher.send(msg, reply_message=True)
#     except FinishedException:
#         pass            
#     except Exception as e:
#         await matcher.send(f"异常:{e}")
#     finally:
#         await browser.close()
#         await playwright.stop()
#         await matcher.finish()
        
# twitter_link = on_command("推文链接识别",priority=plugin_config.command_priority)
# @twitter_link.handle()
# async def twitter_link_handle(event: GroupMessageEvent,matcher: Matcher,arg: Message = CommandArg()):
#     link_list = json.loads(linkpath.read_text("utf8"))
#     if str(event.group_id) not in link_list:
#         link_list[str(event.group_id)] = {"link":True}
#         linkpath.write_text(json.dumps(link_list))
#     if "开启" in arg.extract_plain_text():
#         link_list[str(event.group_id)]["link"] = True
#     elif "关闭" in arg.extract_plain_text():
#         link_list[str(event.group_id)]["link"] = False
#     else:
#         await matcher.finish("仅支持“开启”和“关闭”操作")
#     linkpath.write_text(json.dumps(link_list))    
#     await matcher.finish(f"推文链接识别已{arg.extract_plain_text()}")
    
twitter_timeline = on_command("推文列表",priority=plugin_config.command_priority)
@twitter_timeline.handle()
async def twitter_timeline_handle(bot: Bot,event: MessageEvent,matcher: Matcher,arg: Message = CommandArg()):
    if not plugin_config.twitter_htmlmode:
        await matcher.finish(f"暂时仅支持html模式，请先联系超级管理员开启")
    
    await matcher.send(f"获取中, 请稍等一下..")
    
    user_info = await get_user_info(arg.extract_plain_text())
    
    if not user_info["status"]:
        await matcher.finish(f"未找到 {arg.extract_plain_text()}")
    new_line = await get_user_timeline(user_info["user_name"])
    if "not found" in new_line:
        await matcher.finish(f"未找到 {arg.extract_plain_text()} 存在推文时间线")
    if len(new_line) > 5:
        new_line = new_line[:5]
    playwright,browser = await create_browser()
    try:
        screen = await get_timeline_screen(browser,user_info["user_name"],len(new_line))
        if not screen:
            await matcher.finish("好像失败了...")
        await matcher.send(MessageSegment.image(file=screen))
    except FinishedException:
        pass            
    except Exception as e:
        await matcher.send(f"异常:{e}")
    finally:
        await browser.close()
        await playwright.stop()
        await matcher.finish()
