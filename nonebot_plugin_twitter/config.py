from pydantic import BaseModel,validator
from typing import Optional
from nonebot.log import logger
import sys

if sys.version_info < (3, 10):
    from importlib_metadata import version
else:
    from importlib.metadata import version

try:
    __version__ = version("nonebot_plugin_bilichat")
except Exception:
    __version__ = None

class Config(BaseModel):
    Bearer_Token: Optional[str]
    Proxy: Optional[str]
    command_priority: int = 10
    plugin_enabled: bool = True
    
    @validator("Bearer_Token")
    def check_bearer_token(cls,v):
        if isinstance(str,v):
            logger.info("Bearer_Token 读取成功")
            return v
    @validator("Proxy")
    def check_proxy(cls,v):
        if isinstance(str,v):
            logger.info("Proxy 读取成功")
            return v
        
    @validator("command_priority")
    def check_command_priority(cls,v):
        if isinstance(str,v):
            logger.info("command_priority 读取成功")
            return v
