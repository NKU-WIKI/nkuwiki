import uvicorn
from fastapi import FastAPI, Request, HTTPException
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
import json
import os
import time
import asyncio
import subprocess
import re

# 目录与日志
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOGS_DIR, 'deploy_webhook.log'),
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
file_handler.suffix = "%Y-%m-%d"

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger().handlers.clear()
logging.getLogger().addHandler(console_handler)
logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.INFO)

logger.info("部署Webhook日志初始化完成")

# 配置
FEISHU_APP_ID = None
FEISHU_APP_SECRET = None
DEFAULT_FEISHU_CHAT_ID = None
PROJECT_CHAT_MAPPING = {}

# 默认读取当前目录下的配置文件
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "feishu_config.json")
APP_CONFIG_FILE = os.environ.get("FEISHU_CONFIG_FILE", DEFAULT_CONFIG_PATH)


def load_app_config() -> bool:
    global FEISHU_APP_ID, FEISHU_APP_SECRET, DEFAULT_FEISHU_CHAT_ID, PROJECT_CHAT_MAPPING
    if not os.path.exists(APP_CONFIG_FILE):
        logger.error(f"找不到配置文件: {APP_CONFIG_FILE}")
        return False
    try:
        with open(APP_CONFIG_FILE, 'r') as f:
            cfg = json.load(f)
        FEISHU_APP_ID = cfg.get("feishu_app_id")
        FEISHU_APP_SECRET = cfg.get("feishu_app_secret")
        DEFAULT_FEISHU_CHAT_ID = cfg.get("default_chat_id") or cfg.get("feishu_chat_id")
        PROJECT_CHAT_MAPPING = cfg.get("project_chat_mapping") or {}
        if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not DEFAULT_FEISHU_CHAT_ID:
            logger.error("飞书配置缺失(必须包含 feishu_app_id, feishu_app_secret, default_chat_id)")
            return False
        logger.info("飞书配置加载成功")
        return True
    except Exception as e:
        logger.error(f"读取配置失败: {e}")
        return False


def get_chat_id_for_project(repo_full_name: str) -> str:
    if not PROJECT_CHAT_MAPPING:
        return DEFAULT_FEISHU_CHAT_ID
    return PROJECT_CHAT_MAPPING.get(repo_full_name) or \
        PROJECT_CHAT_MAPPING.get("default") or DEFAULT_FEISHU_CHAT_ID


tenant_access_token_cache = {"token": None, "expires_at": 0}


async def get_tenant_access_token() -> str | None:
    now = time.time()
    if tenant_access_token_cache["token"] and tenant_access_token_cache["expires_at"] > now:
        return tenant_access_token_cache["token"]
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            tenant_access_token_cache["token"] = data["tenant_access_token"]
            tenant_access_token_cache["expires_at"] = now + data.get("expire", 7200) - 300
            return tenant_access_token_cache["token"]
        logger.error(f"获取tenant_access_token失败: {data}")
        return None
    except Exception as e:
        logger.error(f"获取tenant_access_token异常: {e}")
        return None


async def send_feishu_card(chat_id: str, title: str, elements: list) -> dict:
    access_token = await get_tenant_access_token()
    if not access_token:
        raise RuntimeError("无法获取飞书token")
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": "blue"},
        "elements": elements,
    }
    payload = {"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card)}
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"飞书发送失败: {data}")
    return data


def safe_tail(text: str, max_len: int = 1600) -> str:
    if text is None:
        return ""
    text = text.strip()
    return text[-max_len:] if len(text) > max_len else text


def strip_ansi(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)


DEPLOY_CMD = ["/home/dev/nkuwiki-dev/nkuwiki_service_manager.sh", "start", "dev"]


async def run_deploy_and_capture() -> tuple[int, str, str]:
    loop = asyncio.get_event_loop()

    def _run():
        try:
            proc = subprocess.run(
                DEPLOY_CMD,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd="/home/dev/nkuwiki-dev",
            )
            return proc.returncode, proc.stdout, proc.stderr
        except Exception as e:
            return 1, "", str(e)

    return await loop.run_in_executor(None, _run)


app = FastAPI()

CONFIG_OK = load_app_config()
deployment_lock = asyncio.Lock()


@app.post("/webhook/github")
async def github_webhook(request: Request):
    if not CONFIG_OK:
        raise HTTPException(status_code=500, detail="飞书配置未正确加载")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="非法JSON负载")

    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type != "push":
        return {"status": "ignored", "message": f"忽略事件: {event_type}"}

    repo_name = payload.get("repository", {}).get("full_name", "未知仓库")
    ref = payload.get("ref", "")
    branch = ref.split("/")[-1] if ref else ""
    pusher = payload.get("pusher", {}).get("name", "未知")
    head_commit = payload.get("head_commit") or {}
    commit_msg = head_commit.get("message", "无")
    commit_url = head_commit.get("url", "#")
    commits = payload.get("commits", [])

    # 仅处理 dev 分支
    if branch != "dev":
        return {"status": "ignored", "message": f"仅处理dev分支, 当前: {branch}"}

    chat_id = get_chat_id_for_project(repo_name)

    # docs-only 提交（不触发部署，仅通知）
    docs_only = False
    commit_author = head_commit.get("author", {}).get("name", pusher)
    if isinstance(commits, list) and commits:
        docs_only = all((c.get("message", "").strip().lower().startswith("docs:")) for c in commits)
        latest_commit = commits[-1]
        commit_msg = latest_commit.get("message", commit_msg)
        commit_url = latest_commit.get("url", commit_url)
        commit_author = latest_commit.get("author", {}).get("name", commit_author)
    else:
        msg = (commit_msg or "").strip().lower()
        docs_only = msg.startswith("docs:")

    if docs_only:
        try:
            elements = [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"📦 **仓库**: {repo_name}"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"🌿 **分支**: {branch}"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"👤 **提交者**: {commit_author} (推送者: {pusher})"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"💬 **信息**: {commit_msg}"}},
                {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": "🔗 查看提交详情"}, "type": "default", "url": commit_url}]}
            ]
            if isinstance(commits, list) and len(commits) > 1:
                elements.insert(4, {"tag": "div", "text": {"tag": "lark_md", "content": f"✨ **总提交数**: {len(commits)}"}})
                compare_url = payload.get("compare")
                if compare_url:
                    elements.append({
                        "tag": "action",
                        "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": "🔍 查看所有变更"}, "type": "default", "url": compare_url}]
                    })
            await send_feishu_card(chat_id, "GitHub 文档更新通知", elements)
        except Exception as e:
            logger.error(f"发送文档更新通知失败: {e}")
        return {"status": "success", "message": "docs-only 提交，未触发部署"}

    # 发送开始通知
    try:
        elements = [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"📦 **仓库**: {repo_name}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"🌿 **分支**: {branch}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"👤 **推送者**: {pusher}"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": f"💬 **提交**: {commit_msg}"}},
            {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": "🔗 查看提交"}, "type": "default", "url": commit_url}]},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": "🚀 准备开始自动部署: `nkuwiki_service_manager.sh start dev`"}},
        ]
        await send_feishu_card(chat_id, "CI/CD: 部署开始", elements)
    except Exception as e:
        logger.error(f"发送开始通知失败: {e}")

    # 后台执行部署，避免阻塞GitHub回调
    async def _do_deploy_and_notify():
        async with deployment_lock:
            start_ts = time.strftime('%Y-%m-%d %H:%M:%S')
            code, out, err = await run_deploy_and_capture()
            end_ts = time.strftime('%Y-%m-%d %H:%M:%S')
            ok = (code == 0)
            status_emoji = "✅" if ok else "❌"
            clean_out = strip_ansi(out)
            clean_err = strip_ansi(err)
            elements = [
                {"tag": "div", "text": {"tag": "lark_md", "content": f"{status_emoji} **部署完成** (返回码: {code})"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"⏱️ {start_ts} → {end_ts}"}},
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": "🟦 标准输出(尾部):"}},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"```\n{safe_tail(clean_out, 1400)}\n```"}},
            ]
            if clean_err and clean_err.strip():
                label = "🟥 错误输出(尾部):" if not ok else "🟨 附加输出(尾部):"
                elements += [
                    {"tag": "div", "text": {"tag": "lark_md", "content": label}},
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"```\n{safe_tail(clean_err, 800)}\n```"}},
                ]
            try:
                await send_feishu_card(chat_id, "CI/CD: 部署结果", elements)
            except Exception as e:
                logger.error(f"发送部署结果失败: {e}")

    asyncio.create_task(_do_deploy_and_notify())

    total_commits = len(commits) if isinstance(commits, list) else 0
    return {"status": "accepted", "message": f"已触发dev部署，提交数: {total_commits}"}


@app.get("/")
async def root():
    return {
        "service": "NKUWiki Deploy Webhook",
        "config_loaded": CONFIG_OK,
        "config_file": APP_CONFIG_FILE,
        "endpoints": ["/webhook/github"],
    }


if __name__ == "__main__":
    if not CONFIG_OK:
        logger.error("配置未加载，服务不启动")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")


