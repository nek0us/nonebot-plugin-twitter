<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-twitter

_✨ 推文订阅推送插件 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/nek0us/nonebot-plugin-twitter.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-twitter">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-twitter.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

~~⚠ 插件暂不可用~~

~~因推特开启登录墙，该插件暂不可用~~

## 📖 介绍

订阅推送 twitter 推文

## 💿 安装

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-twitter
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-twitter
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-twitter
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-twitter
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_twitter"]

</details>

## ⚙️ 配置

 
在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| twitter_website | 否 | 无 | 自定义website |
| twitter_proxy | 否 | 无 | proxy |
| twitter_qq | 否 | 2854196310 | 合并消息头像来源 |
| command_priority | 否 | 10 | 命令优先级 |

配置格式示例
```bash
#twitter
twitter_proxy="http://127.0.0.1:1090"
twitter_qq=2854196306
command_priority=10
```

## 🎉 使用
### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| 关注推主 | 无 | 否 | 群聊/私聊 | 关注，指令格式：“关注推主 <推主id> [r18] [媒体]”|
| 取关推主 | 无 | 否 | 群聊/私聊 | 取关切割 |
| 推主列表 | 无 | 否 | 群聊/私聊 | 展示列表 |
| 推文推送关闭 | 群管 | 否 | 群聊/私聊 | 关闭推送 |
| 推文推送开启 | 群管 | 否 | 群聊/私聊 | 开启推送 |


[] 为可选参数，

r18 : 开启r18推文推送

媒体 : 仅推送媒体消息

### 效果图
[![pCPuhWV.png](https://s1.ax1x.com/2023/06/05/pCPuhWV.png)](https://imgse.com/i/pCPuhWV)
[![pCPu4zT.png](https://s1.ax1x.com/2023/06/05/pCPu4zT.png)](https://imgse.com/i/pCPu4zT)
### 注意事项
1.推主id：
[![pCPMu36.png](https://s1.ax1x.com/2023/06/05/pCPMu36.png)](https://imgse.com/i/pCPMu36)

2.消息为合并转发发送，存在延迟和发送失败的可能

3.新的0.1.0版本为破坏性更新：代理配置格式更改，关注列表需重新关注。

### 更新记录

2023.07.28 0.1.13
1. 修复bug


2023.07.25

1. 优化推送消息发送方式
2. 修复bug

2023.07.20

1. 增加了仅媒体推送
2. 修复了该插件与若干问题


2023.06.27

1. 临时解决回复原推文时，无法推送全部推文的问题
