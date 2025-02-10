"""
channel factory
"""
from .channel import Channel


def create_channel(channel_type) -> Channel:
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    ch = Channel()
    if channel_type == "terminal":
        from services.terminal.terminal_channel import TerminalChannel
        ch = TerminalChannel()
    elif channel_type == 'website':
        from services.website import WebsiteChannel
        ch = WebsiteChannel()
    elif channel_type == "wechatmp":
        from services.wechatmp.wechatmp_channel import WechatMPChannel
        ch = WechatMPChannel(passive_reply=True)
    elif channel_type == "wechatmp_service":
        from services.wechatmp.wechatmp_channel import WechatMPChannel
        ch = WechatMPChannel(passive_reply=False)
    else:
        raise RuntimeError
    ch.channel_type = channel_type
    return ch
