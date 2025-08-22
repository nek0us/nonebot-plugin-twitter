from pydantic import BaseModel, root_validator,validator
from typing import Literal, Optional
from typing_extensions import TypedDict
from nonebot.log import logger
from nonebot import get_driver, get_plugin_config
import sys


class Config(BaseModel):
    # 自定义镜像站
    twitter_website: Optional[str] = ""
    # 代理
    twitter_proxy: Optional[str] = None
    # 内部当前使用url
    twitter_url: Optional[str] = ""
    # 自定义转发消息来源qq
    twitter_qq: int = 2854196310
    # 自定义事件响应等级
    command_priority: int = 10
    # 插件开关
    plugin_enabled: bool = True
    # 网页截图模式
    twitter_htmlmode: bool = False
    # 截取源地址网页
    twitter_original: bool = False
    # 媒体无文字
    twitter_no_text: bool = False
    # 使用转发消息
    twitter_node: bool = True
           
plugin_config = get_plugin_config(Config)

website_list = [
    "https://nitter.net", # 403
    "https://nitter.poast.org",
    
]

twitter_post = '''() => {
            const elementXPath = '/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div[1]/div/div/div/div';
            const element = document.evaluate(elementXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            
            if (element) {
                element.remove();
            }
        }'''
twitter_login = '''() => {
            const elementXPath = '/html/body/div[1]/div/div/div[1]/div/div[1]/div';
            const element = document.evaluate(elementXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            
            if (element) {
                element.remove();
            }
        }'''
        
nitter_head = '''() => {
            const elementXPath = '/html/body/nav';
            const element = document.evaluate(elementXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            
            if (element) {
                element.remove();
            }
        }'''
        
nitter_foot = '''() => {
            const elementXPath = '/html/body/div[1]/div/div[3]/div';
            const element = document.evaluate(elementXPath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            
            if (element) {
                element.remove();
            }
        }'''
        
class SetCookieParam(TypedDict, total=False):
    name: str
    value: str
    url: Optional[str]
    domain: Optional[str]
    path: Optional[str]
    expires: Optional[float]
    httpOnly: Optional[bool]
    secure: Optional[bool]
    sameSite: Optional[Literal["Lax", "None", "Strict"]]
