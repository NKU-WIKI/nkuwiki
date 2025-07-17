import sys
import asyncio
from pathlib import Path

# 将项目根目录添加到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from etl.crawler.wechat import Wechat
from core.utils.logger import register_logger

async def main():
    """
    主函数，用于登录微信公众号平台并保存cookies。
    此脚本会以有头模式打开浏览器，并等待您扫描二维码登录。
    登录成功后，它会保存cookies并自动退出。
    """
    logger = register_logger('get_wechat_cookies')
    logger.info("=" * 50)
    logger.info("微信公众号 Cookie 获取工具")
    logger.info("=" * 50)
    logger.info("即将打开浏览器，请使用微信扫描二维码登录...")
    logger.info("登录成功后，程序将自动保存Cookie并关闭。")

    # 以有头模式实例化微信爬虫
    # 构造函数需要一个公众号列表，我们传入一个虚拟的即可
    wechat_crawler = Wechat(authors=["nkunews"], headless=False)

    try:
        # 初始化浏览器和页面
        await wechat_crawler.async_init()

        # 调用登录方法
        cookies = await wechat_crawler.login_for_cookies()

        if cookies:
            # 使用基类中的方法保存cookies
            wechat_crawler.save_cookies(cookies)
            logger.info(f"Cookies 保存成功！文件位置: {wechat_crawler.cookie_file_path}")
        else:
            logger.error("未能获取到 Cookies。可能是登录超时或被中断。")

    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        # 清理并关闭浏览器
        await wechat_crawler.close()
        logger.info("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main()) 