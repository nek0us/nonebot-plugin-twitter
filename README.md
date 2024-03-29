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
| twitter_htmlmode | 否 | false | 网页截图模式 |
| twitter_original | 否 | false | 使用x官网截图 |
| twitter_no_text | 否 | false | 开启媒体过滤后彻底不输出文字 |
| twitter_node | 否 | true | 使用合并转发消息发送 |

配置格式示例
```bash
# twitter
twitter_proxy="http://127.0.0.1:1090"
twitter_qq=2854196306
command_priority=10

# 使用截图纯图模式示例
twitter_htmlmode=true
twitter_original=false
twitter_no_text=true
twitter_node=false
```

## 🎉 使用
### 指令表
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

4.已知bug，视频无法发送（可能为gocq bug）

5.链接识别发送方式与配置文件配置有关

6.推文列表暂时仅在 网页截图模式 开启时支持

### 更新记录
2024.01.20 0.2.4
1. 优化代理设置
2. 添加链接识别功能
3. 添加查看时间线截图功能
   

2024.01.14 0.2.3
1. 修复内存溢出bug
2. 修复代理未完全生效bug


2024.01.06 0.2.2
1. 更新默认镜像站列表
2. 调整文字输出，不再会输出评论区文字
3. 调整合并转发消息内，图片的优先级（其实是上次更新内容，但忘写了）
4. 调整自动切换镜像站（非指定website的情况下）


2024.01.01 0.2.0
1. 增加截图模式
2. 增加无文字的媒体过滤
3. 增加非合并转发发送方式
4. 调整缓存删除方式为每天早上删除（没什么用，现在发不出视频）
5. 调整媒体图片输出不再会输出评论区他人的图片视频
6. 优化了日志输出
7. 还有什么有点忘了，一口气改到0点，祝大家2024新年快乐吧


2023.10.28 0.1.14
1. 更新可用站点列表


2023.09.16 0.1.13
1. 暂无更新，可在env配置文件中添加以下参数来解决不可用问题
```bash
# twitter
twitter_website="https://nitter.privacydev.net"
```

最近找工作忙，更新慢了请见谅


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
