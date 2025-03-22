"""
微信小程序关于我们API
提供平台信息、版本更新、协议条款等相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.wxapp import router
from core.api.wxapp.common_utils import format_datetime

# 平台信息
PLATFORM_INFO = {
    "name": "南开知识共享平台",
    "description": "致力于构建南开知识共同体，践行开源·共治·普惠三位一体价值体系",
    "slogan": "消除南开学子信息差距，开放知识资源免费获取，构建可持续的互助社区",
    "version": "1.0.0",
    "website": "https://nkuwiki.com",
    "email": "contact@nkuwiki.com",
    "github": "https://github.com/nkuwiki",
    "wechat": "nkuwiki",
    "team": [
        {
            "name": "Nku Wiki 团队",
            "role": "开发者",
            "avatar": "https://nkuwiki.com/images/logo.jpg"
        }
    ],
    "features": [
        {
            "name": "校园知识库",
            "description": "收集整理南开大学学习资源、校园信息、生活指南等知识内容"
        },
        {
            "name": "智能问答",
            "description": "基于大模型的智能问答系统，解答校园学习生活相关问题"
        },
        {
            "name": "社区交流",
            "description": "提供交流平台，分享经验，互帮互助"
        }
    ]
}

# 版本更新历史
VERSION_HISTORY = [
    {
        "version": "1.0.0",
        "date": "2023-09-01",
        "title": "正式发布",
        "description": "南开Wiki正式发布",
        "changes": [
            "校园知识库基础功能",
            "智能问答系统",
            "用户账号管理"
        ]
    },
    {
        "version": "0.9.0",
        "date": "2023-08-15",
        "title": "内测版本",
        "description": "南开Wiki内测版本发布",
        "changes": [
            "完成核心功能开发",
            "进行性能优化",
            "修复主要BUG"
        ]
    },
    {
        "version": "0.5.0",
        "date": "2023-07-01",
        "title": "早期测试版",
        "description": "南开Wiki早期测试版",
        "changes": [
            "实现基础功能原型",
            "开始进行用户测试"
        ]
    }
]

# 用户协议
USER_AGREEMENT = {
    "title": "南开Wiki用户协议",
    "content": """
# 南开Wiki用户协议

欢迎使用南开Wiki！本协议是您与南开Wiki之间关于使用南开Wiki平台服务的协议。

## 一、服务内容

南开Wiki是一个校园知识共享平台，旨在为南开大学学生提供学习资源、校园信息、生活指南等内容的共享和交流平台。

## 二、用户注册与账号安全

1. 用户需要使用微信授权登录，获取基本用户信息。
2. 用户应当妥善保管自己的账号信息，对账号下的所有行为负责。
3. 平台有权在发现违规行为时，暂停或终止用户的使用权限。

## 三、用户行为规范

1. 用户在使用平台时，应遵守中华人民共和国相关法律法规。
2. 用户不得发布违法、色情、暴力、政治敏感等内容。
3. 用户不得侵犯他人知识产权、隐私权等合法权益。
4. 用户应尊重他人，不得进行人身攻击、辱骂等不良行为。

## 四、知识产权

1. 平台上的原创内容归作者所有，作者授权平台进行使用和传播。
2. 用户上传的内容应确保拥有合法的知识产权或使用权。

## 五、免责声明

1. 平台不对用户发布的内容真实性、准确性负责。
2. 平台不对因不可抗力、网络问题等导致的服务中断负责。

## 六、协议修改

平台有权在必要时修改本协议，修改后的协议将在平台上公布。

## 七、其他

本协议的解释权归南开Wiki所有。
    """
}

# 隐私政策
PRIVACY_POLICY = {
    "title": "南开Wiki隐私政策",
    "content": """
# 南开Wiki隐私政策

南开Wiki非常重视用户的隐私保护，本隐私政策说明我们如何收集、使用、存储和保护您的个人信息。

## 一、信息收集

1. 基本信息：当您使用微信授权登录时，我们会获取您的微信昵称、头像等基本信息。
2. 使用信息：我们会收集您在平台上的使用记录、浏览历史、搜索记录等。
3. 设备信息：我们会收集您使用的设备型号、操作系统、网络状态等信息。

## 二、信息使用

1. 提供服务：我们使用收集的信息为您提供个性化的服务和内容推荐。
2. 改进产品：通过分析用户行为，不断优化产品功能和用户体验。
3. 安全保障：用于账号安全、防止欺诈等安全保障功能。

## 三、信息存储

1. 信息存储在中国境内的服务器上。
2. 我们会采取严格的安全措施保护您的信息安全。

## 四、信息保护

1. 我们使用加密技术保护数据传输和存储。
2. 我们设有严格的内部权限控制，限制对用户信息的访问。

## 五、信息共享

除以下情况外，我们不会与第三方共享您的个人信息：
1. 获得您的明确授权。
2. 法律法规要求的情况。
3. 为了保护平台及用户的合法权益。

## 六、隐私政策更新

我们可能会不时更新本隐私政策，更新后的政策将在平台上公布。

## 七、联系我们

如果您对本隐私政策有任何疑问，可以通过以下方式联系我们：
邮箱：contact@nkuwiki.com
    """
}

@router.get("/about", response_model=Dict[str, Any], summary="获取平台信息")
@handle_api_errors("获取平台信息")
async def get_about_info(
    api_logger=Depends(get_api_logger)
):
    """
    获取平台基本信息，包括平台名称、描述、版本、团队等
    """
    api_logger.debug("获取平台信息")
    
    return create_standard_response(
        code=200,
        message="获取平台信息成功",
        data=PLATFORM_INFO
    )

@router.get("/versions", response_model=Dict[str, Any], summary="获取版本更新历史")
@handle_api_errors("获取版本历史")
async def get_version_history(
    limit: int = Query(10, description="返回记录数量限制", ge=1, le=50),
    api_logger=Depends(get_api_logger)
):
    """
    获取平台版本更新历史
    """
    api_logger.debug(f"获取版本更新历史, 限制数量={limit}")
    
    # 限制返回数量
    versions = VERSION_HISTORY[:limit]
    
    return create_standard_response(
        code=200,
        message="获取版本历史成功",
        data={"versions": versions}
    )

@router.get("/agreement/{type}", response_model=Dict[str, Any], summary="获取用户协议或隐私政策")
@handle_api_errors("获取协议")
async def get_agreement(
    type: str = PathParam(..., description="协议类型: user-用户协议, privacy-隐私政策"),
    api_logger=Depends(get_api_logger)
):
    """
    获取用户协议或隐私政策
    """
    api_logger.debug(f"获取协议, 类型={type}")
    
    if type == "user":
        agreement = USER_AGREEMENT
    elif type == "privacy":
        agreement = PRIVACY_POLICY
    else:
        raise HTTPException(status_code=400, detail="无效的协议类型")
    
    return create_standard_response(
        code=200,
        message="获取协议成功",
        data=agreement
    ) 