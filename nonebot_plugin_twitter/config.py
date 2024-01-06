from pydantic import BaseModel,validator
from typing import Literal, Optional, TypedDict
from nonebot.log import logger
from nonebot import get_driver
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import version
else:
    from importlib.metadata import version

try:
    __version__ = version("nonebot_plugin_twitter")
except Exception:
    __version__ = None

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
    
    @validator("twitter_website")
    def check_twitter_website(cls,v):
        if isinstance(v,str):
            logger.info(f"twitter_website {v} 读取成功")
            return v
    @validator("twitter_proxy")
    def check_proxy(cls,v):
        if isinstance(v,str):
            logger.info(f"twitter_proxy {v} 读取成功")
            return v
    @validator("twitter_qq")
    def check_twitter_qq(cls,v):
        if isinstance(v,int):
            logger.info(f"twitter_qq {v} 读取成功")
            return v
        
    @validator("command_priority")
    def check_command_priority(cls,v):
        if isinstance(v,int) and v >= 1:
            logger.info(f"command_priority {v} 读取成功")
            return v
        
    @validator("twitter_original")
    def check_twitter_original(cls,v):
        if isinstance(v,bool):
            logger.info(f"twitter_original 使用twitter官方页面截图 {'已开启' if v else '已关闭'}")
            return v     
        
    @validator("twitter_htmlmode")
    def check_twitter_htmlmode(cls,v):
        if isinstance(v,bool):
            logger.info(f"twitter_htmlmode 网页截图模式 {'已开启' if v else '已关闭'}")
            return v             
        
    @validator("twitter_no_text")
    def check_twitter_no_text(cls,v):
        if isinstance(v,bool):
            logger.info(f"twitter_no_text 媒体无文字 {'已开启' if v else '已关闭'}")
            return v     
        
    @validator("twitter_node")
    def check_twitter_node(cls,v):
        if isinstance(v,bool):
            logger.info(f"twitter_node 合并转发消息  {'已开启' if v else '已关闭'}")
            return v           
config_dev = Config.parse_obj(get_driver().config)

website_list = [
    "https://n.opnxng.com",
    "https://nitter.uni-sonia.com",
    "https://nitter.mint.lgbt",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.salastil.com",
    "https://nitter.d420.de",
    "https://nitter.1d4.us",
    "https://nitter.moomoo.me"
    
    # "https://n.biendeo.com", # 很慢
    # "https://nitter.catsarch.com", # 很慢
    # "https://nitter.net", # 403
    # "https://nitter.dafriser.be", # 502
    # "https://nitter.woodland.cafe", # 403
    # "https://nitter.x86-64-unknown-linux-gnu.zip", # 403
    # "https://bird.trom.tf", # 寄
    # "https://nitter.unixfox.eu", # 403
    # "https://nitter.it", # 404
    # "https://twitter.owacon.moe", # 301
    
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