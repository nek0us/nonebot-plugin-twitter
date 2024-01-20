import json
import random
import sys
import typing
import httpx
import os
from typing import Optional,Literal
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageSegment,Message
from playwright.async_api import async_playwright,Browser
from nonebot_plugin_sendmsg_by_bots import tools
from .config import config_dev,twitter_post,twitter_login,nitter_head,nitter_foot,SetCookieParam

# Path
dirpath = Path() / "data" / "twitter"
dirpath.mkdir(parents=True, exist_ok=True)
dirpath = Path() / "data" / "twitter" / "cache"
dirpath.mkdir(parents=True, exist_ok=True)
dirpath = Path() / "data" / "twitter" / "twitter_list.json"
dirpath.touch()
if not dirpath.stat().st_size:
    dirpath.write_text("{}")
linkpath = Path() / "data" / "twitter" / "twitter_link.json"
linkpath.touch()
if not linkpath.stat().st_size:
    linkpath.write_text("{}")
    
header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

async def get_user_info(user_name:str) -> dict:
    '''通过 user_name 获取信息详情,
    return:
    result["status"],
    result["user_name"],
    result["screen_name"],
    result["bio"]
    '''
    result ={}
    result["status"] = False
    try:
        async with httpx.AsyncClient(proxies=config_dev.twitter_proxy,http2=True,timeout=120) as client:
            res = await client.get(url=f"{config_dev.twitter_url}/{user_name}",headers=header)
            
            if res.status_code ==200:
                result["status"] = True
                result["user_name"] = user_name
                soup = BeautifulSoup(res.text,"html.parser")
                result["screen_name"] = match[0].text if (match := soup.find_all('a', class_='profile-card-fullname')) else ""
                result["bio"] = match[0].text if (match := soup.find_all('p')) else ""
            else:
                logger.warning(f"通过 user_name {user_name} 获取信息详情失败：{res.status_code} {res.text} ")
                result["status"] = False
    except Exception as e:
        logger.warning(f"通过 user_name {user_name} 获取信息详情出错：{e}")

    return result

async def get_user_timeline(user_name:str,since_id: str = "0"):
    async with httpx.AsyncClient(proxies=config_dev.twitter_proxy,http2=True,timeout=120) as client:
        res = await client.get(url=f"{config_dev.twitter_url}/{user_name}",headers=header)
        if res.status_code ==200:
            soup = BeautifulSoup(res.text,"html.parser")
            timeline_list = soup.find_all('a', class_='tweet-link')
            new_line =[]
            for x in timeline_list:
                if user_name in x.attrs["href"]:
                    tweet_id = x.attrs["href"].split("/").pop().replace("#m","")
                    if since_id != "0":
                        if int(tweet_id) > int(since_id):
                            logger.trace(f"通过 user_name {user_name} 获取时间线成功：{tweet_id}")
                            new_line.append(tweet_id)
                    else:
                        new_line.append(tweet_id)
                        
        else:
            logger.warning(f"通过 user_name {user_name} 获取时间线失败：{res.status_code} {res.text}")
            new_line = ["not found"]
        return new_line

async def get_user_newtimeline(user_name:str,since_id: str = "0") -> str:
    ''' 通过 user_name 获取推文id列表,
    有 since_id return 最近的新的推文id,
    无 since_id return 最新的推文id'''
    try:
        new_line = await get_user_timeline(user_name, since_id)
        if since_id == "0":
            if new_line == []:
                new_line.append("1")
            else:
                new_line = [str(max(map(int,new_line)))]
        if new_line == []:
            new_line = ["not found"]
        return new_line[-1]
    except Exception as e:
        logger.warning(f"通过 user_name {user_name} 获取时间线失败：{e}")
        raise e
    
async def get_timeline_screen(browser: Browser,user_name: str,length: int = 5):
    url=f"{config_dev.twitter_url}/{user_name}"
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url,timeout=60000)
    await page.wait_for_load_state("load",timeout=60000)
    await page.wait_for_selector('.timeline-item')

    tweets = await page.query_selector_all('.timeline-item')
    first_five_tweets = tweets[:5]

    if len(first_five_tweets) > 0:
        first_bbox = await first_five_tweets[0].bounding_box()
        fifth_bbox = await first_five_tweets[4].bounding_box()
        if first_bbox and fifth_bbox:
        # 计算前五个推文所占的总高度
            total_height = fifth_bbox['y'] + fifth_bbox['height'] - first_bbox['y']

            # 调整浏览器视口的高度
            await page.set_viewport_size({'width': 1280, 'height': total_height})

            # 再次计算第一个推文的位置和尺寸，因为视口大小变化后位置可能会有所变动
            first_bbox = await first_five_tweets[0].bounding_box()

            # 截图
            screen = await page.screenshot(clip={
                'x': first_bbox['x'],
                'y': first_bbox['y'],
                'width': first_bbox['width'],
                'height': total_height
            })

            return screen
    return None
    
async def get_tweet(browser: Browser,user_name:str,tweet_id: str = "0") -> dict:
    '''通过 user_name 和 tweet_id 获取推文详情,
    return:
    result["status"],
    result["text"],
    result["pic_url_list"],
    result["video_url"],
    result["r18"]
    result["html"]
    '''
    try:
        result = {}
        result["status"] = False
        result["html"] = b""
        result["media"] = False
        url=f"{config_dev.twitter_url}/{user_name}/status/{tweet_id}"

        if config_dev.twitter_htmlmode:
            context = await browser.new_context()
            page = await context.new_page()
            cookie: typing.List[SetCookieParam] = [{
                "url": config_dev.twitter_url,
                "name": "hlsPlayback",
                "value": "on"}]
            await context.add_cookies(cookie)
            if config_dev.twitter_original:
                # 原版 twitter
                url=f"https://twitter.com/{user_name}/status/{tweet_id}"
                await page.goto(url,timeout=60000)
                await page.wait_for_load_state("load",timeout=60000)
                await page.evaluate(twitter_login)
                await page.evaluate(twitter_post)
                screenshot_bytes = await page.locator("xpath=/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[1]").screenshot()
            else:
                await page.goto(url,timeout=60000)
                await page.wait_for_load_state("load",timeout=60000)
                await page.evaluate(nitter_head)
                await page.evaluate(nitter_foot)
                screenshot_bytes = await page.locator("xpath=/html/body/div[1]/div").screenshot()
            logger.info(f"使用浏览器截图获取 {url} 推文信息成功")
            result["html"] = screenshot_bytes
            await page.close()
            await context.close()


        async with httpx.AsyncClient(proxies=config_dev.twitter_proxy,http2=True,timeout=120) as client:
            res = await client.get(url,cookies={"hlsPlayback": "on"},headers=header)
            if res.status_code ==200:
                soup = BeautifulSoup(res.text,"html.parser")

                # text && pic && video
                result["text"] = []
                result["pic_url_list"] = []
                result["video_url"] = ""
                if main_thread_div := soup.find('div', class_='main-thread'):
                    # pic
                    if pic_list := main_thread_div.find_all('a', class_='still-image'): # type: ignore
                        result["pic_url_list"] = [x.attrs["href"] for x in pic_list]
                    # video
                    if video_list := main_thread_div.find_all('video'): # type: ignore
                        # result["video_url"] = video_list[0].attrs["data-url"]
                        try:
                            video_url = video_list[0].parent.parent.parent.parent.parent.contents[1].attrs["href"].replace("#m","")
                        except Exception as e:
                            logger.info(f"获取视频推文链接出错，转为获取自身链接，{e}")
                            video_url = url.split(config_dev.twitter_url)[1]
                        result["video_url"] = f"https://twitter.com{video_url}"
                    # text
                    if match := main_thread_div.find_all('div', class_='tweet-content media-body'): # type: ignore
                        for x in match:
                            if x.parent.attrs["class"] == "replying-to":
                                continue
                            result["text"].append(x.text)
                # r18
                result["r18"] = bool(r18 := soup.find_all('div', class_='unavailable-box'))
                if result["video_url"] or result["pic_url_list"]:
                    result["media"] = True
                    logger.info(f"推主 {user_name} 的推文 {tweet_id} 存在媒体")
                result["status"] = True
                logger.info(f"推主 {user_name} 的推文 {tweet_id} 获取成功")
            else:
                logger.warning(f"获取 {user_name} 的推文 {tweet_id} 失败：{res.status_code} {res.text}")
        return result
    except Exception as e:
        logger.warning(f"获取 {user_name} 的推文 {tweet_id} 异常：{e}")
        raise e


async def get_video_path(url: str) -> str:
    try:
        filename = str(int(datetime.now().timestamp())) + ".mp4"
        path = Path() / "data" / "twitter" / "cache" /  filename
        path = f"{os.getcwd()}/{str(path)}"
        async with httpx.AsyncClient(proxies=config_dev.twitter_proxy) as client:
            res = await client.get(f"https://twitterxz.com/?url={url}",headers=header,timeout=120)
            if res.status_code != 200:
                raise ValueError("视频下载失败")
            soup = BeautifulSoup(res.text,"html.parser")
            script_tag = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
            tmp = script_tag.string # type: ignore
            video_url = json.loads(tmp) # type: ignore
            video_url = video_url['props']['pageProps']['twitterInfo']['videoInfos'][-1]['url']
            # return video_url
            async with client.stream("get",video_url) as s:
                if res.status_code != 200:
                    raise ValueError("视频下载失败")
            
                with open(path,'wb') as file:
                    async for chunk in s.aiter_bytes():
                        file.write(chunk)

        return path
    except Exception as e:
        logger.warning(f"下载视频异常：url {url}，{e}")
        raise e

async def get_video(url: str) -> MessageSegment:
    '修改为返回视频消息，而非合并视频消息'
    # return MessageSegment.node_custom(user_id=user_id, nickname=name,
    #                                       content=Message(MessageSegment.video(f"file:///{task}"))) 
    try:
        path = await get_video_path(url)
        # return MessageSegment.video(path)
        return MessageSegment.video(f"file:///{path}")
    except Exception as e:
        logger.debug(f"缓存视频异常：url {url}，{e}，转为返回原链接")
        return MessageSegment.text(f"获取视频出错啦，原链接：{url}")
        
async def get_pic(url: str) -> MessageSegment:
    '修改为返回图片消息，而非合并图片消息'
    
    async with httpx.AsyncClient(proxies=config_dev.twitter_proxy,http2=True) as client:
        try:
            res = await client.get(f"{config_dev.twitter_url}{url}",headers=header,timeout=120)
            if res.status_code != 200:
                logger.warning(f"图片下载失败:{config_dev.twitter_url}{url}，状态码：{res.status_code}")
                # return MessageSegment.node_custom(user_id=config_dev.twitter_qq, nickname=user_name,
                #                        content=Message(f"图片加载失败 X_X {url}"))
                return MessageSegment.text(f"图片加载失败 X_X 图片链接 {config_dev.twitter_url}{url}")
            tmp = bytes(random.randint(0,255))
            # return MessageSegment.node_custom(user_id=config_dev.twitter_qq, nickname=user_name,
            #                            content=Message(MessageSegment.image(file=(res.read()+tmp))))
            return MessageSegment.image(file=(res.read()+tmp))
        except Exception as e:
            logger.warning(f"获取图片出现异常 {config_dev.twitter_url}{url} ：{e}")
            return MessageSegment.text(f"图片加载失败 X_X 图片链接 {config_dev.twitter_url}{url}")



async def is_firefox_installed():
    '''chekc firefox install | 检测Firefox是否已经安装 '''
    try:
        playwright_manager = async_playwright()
        playwright = await playwright_manager.start()
        browser = await playwright.firefox.launch(slow_mo=50)
        await browser.close()
        return True
    except Exception as e:
        return False

# 安装Firefox
def install_firefox():
    os.system('playwright install firefox')
    
    
# 发送
async def send_msg(twitter_list: dict,user_name: str,line_new_tweet_id: str,tweet_info: dict,msg: Message,mode:Optional[Literal["node","direct","video"]] = "node"):
    for group_num in twitter_list[user_name]["group"]:
        # 群聊
        if twitter_list[user_name]["group"][group_num]["status"]:
            if twitter_list[user_name]["group"][group_num]["r18"] == False and tweet_info["r18"] == True:
                logger.info(f"根据r18设置，群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")
                continue
            if twitter_list[user_name]["group"][group_num]["media"] == True and tweet_info["media"] == False:
                logger.info(f"根据媒体设置，群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")
                continue
            try:
                if mode == "node":
                    # 以合并方式发送
                    if await tools.send_group_forward_msg_by_bots(group_id=int(group_num), node_msg=msg):
                        logger.info(f"群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 合并发送成功")
                elif mode == "direct":
                    if await tools.send_group_msg_by_bots(group_id=int(group_num), msg=msg):
                        logger.info(f"群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 直接发送成功")
                elif mode == "video":
                    if await tools.send_group_msg_by_bots(group_id=int(group_num), msg=msg):
                        logger.info(f"群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 视频发送成功")
            except Exception as e:
                logger.warning(f"发送消息出现失败,目标群：{group_num},推文 {user_name}/status/{line_new_tweet_id}，发送模式 {'截图' if tweet_info['html'] else '内容'}，异常{e}")
        else:
            logger.info(f"根据通知设置，群 {group_num} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")
            
    for qq in twitter_list[user_name]["private"]:
        # 私聊
        if twitter_list[user_name]["private"][qq]["status"]:
            if twitter_list[user_name]["private"][qq]["r18"] == False and tweet_info["r18"] == True:
                logger.info(f"根据r18设置，qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")   
                continue
            if twitter_list[user_name]["private"][qq]["media"] == True and tweet_info["media"] == False:
                logger.info(f"根据媒体设置，qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")   
                continue
            try:
                if mode == "node":
                    if await tools.send_private_forward_msg_by_bots(user_id=int(qq), node_msg=msg):
                        logger.info(f"qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 合并发送成功")
                elif mode == "direct":
                    if await tools.send_private_msg_by_bots(user_id=int(qq), msg=msg):
                        logger.info(f"qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 直接发送成功")
                elif mode == "video":
                    if await tools.send_private_msg_by_bots(user_id=int(qq), msg=msg):
                        logger.info(f"qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 视频发送成功")
            except Exception as e:
                logger.warning(f"发送消息出现失败,目标qq：{qq},推文 {user_name}/status/{line_new_tweet_id}，发送模式 {'截图' if tweet_info['html'] else '内容'}，异常{e}")
        else:
            logger.info(f"根据通知设置，qq {qq} 的推文 {user_name}/status/{line_new_tweet_id} 跳过发送")                    

def get_next_element(my_list, current_element):

    # 获取当前元素在列表中的索引
    index = my_list.index(current_element)
    
    # 计算下一个元素的索引
    next_index = (index + 1) % len(my_list)
    
    # 返回下一个元素
    return my_list[next_index]


async def get_tweet_context(tweet_info: dict,user_name: str,line_new_tweet_id: str):
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
        
    return all_msg


async def tweet_handle(tweet_info: dict,user_name: str,line_new_tweet_id: str,twitter_list: dict) -> bool:
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
        all_msg = await get_tweet_context(tweet_info,user_name,line_new_tweet_id)
            
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
    
    
async def tweet_handle_link(tweet_info: dict,user_name: str,line_new_tweet_id: str):
    if not tweet_info["status"] and not tweet_info["html"]:
        # 啥都没获取到
        logger.warning(f"{user_name} 的推文 {line_new_tweet_id} 获取失败")
        return Message(f"{user_name} 的推文 {line_new_tweet_id} 获取失败")
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
                    nickname=user_name,
                    content=Message(MessageSegment.image(tweet_info["html"]))
                ))
                # await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg))
            
            return Message(msg)
        return Message("")
    # elif tweet_info["status"] and not tweet_info["html"]:
    #     # 只没有截图？不应该啊
    #     pass
    # elif tweet_info["status"] and tweet_info["html"]:
    else:
        # 有没有截图不知道，内容信息是真有
        all_msg = await get_tweet_context(tweet_info,user_name,line_new_tweet_id)
            
        # 准备发送消息
        if config_dev.twitter_node:
            # 以合并方式发送
            msg = []
            for value in  all_msg:
                msg.append(
                    MessageSegment.node_custom(
                        user_id=config_dev.twitter_qq,
                        nickname=user_name,
                        content=Message(value)
                    )
                )
            if not config_dev.twitter_no_text:
                # 开启了媒体文字
                for x in tweet_info["text"]:
                    msg.append(MessageSegment.node_custom(
                        user_id=config_dev.twitter_qq,
                        nickname=user_name,
                        content=
                        Message(x)
                    ))
            # 发送合并消息    
            # await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(msg))
            return Message(msg)
        else:
            # 以直接发送的方式
            if all_msg[-1].type == "video":
                # 有视频先发视频
                video_msg = all_msg.pop()
                # await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(video_msg),"video")
            if not config_dev.twitter_no_text:    
                # 开启了媒体文字
                all_msg.append(MessageSegment.text('\n\n'.join(tweet_info["text"])))
            # 剩余部分直接发送
            # await send_msg(twitter_list,user_name,line_new_tweet_id,tweet_info,Message(all_msg),"direct")
            return Message(all_msg)
