from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional, Any
from config import Config
from core.utils import register_logger
from api.models.common import Response
from pydantic import BaseModel
import json
import os
from pathlib import Path
from datetime import datetime

router = APIRouter()
logger = register_logger(__name__)
config = Config()

class BanwordCategory(BaseModel):
    """敏感词分类模型"""
    name: str
    defaultRisk: int
    words: List[str]
    patterns: Optional[List[List[str]]] = []

class BanwordRequest(BaseModel):
    """添加敏感词请求模型"""
    category: str
    words: List[str]
    risk: Optional[int] = 3

class BanwordLibrary(BaseModel):
    """敏感词库模型"""
    library: Dict[str, BanwordCategory]

def get_banwords_file_path() -> Path:
    """获取敏感词文件路径"""
    return Path("banwords.json")

def load_banwords_from_json() -> Dict[str, Any]:
    """从JSON文件加载敏感词数据"""
    banwords_path = get_banwords_file_path()
    if not banwords_path.exists():
        logger.warning("敏感词文件不存在，返回空数据")
        return {}
    
    try:
        content = banwords_path.read_text(encoding='utf-8')
        data = json.loads(content)
        return data.get('library', {})
        
    except json.JSONDecodeError as e:
        logger.error(f"敏感词JSON文件格式错误: {e}")
        return {}
    except Exception as e:
        logger.error(f"加载敏感词文件失败: {e}")
        return {}

def save_banwords_to_json(library_data: Dict[str, Any]) -> bool:
    """保存敏感词数据到JSON文件"""
    banwords_path = get_banwords_file_path()
    
    try:
        # 读取现有文件获取元数据
        existing_data = {}
        if banwords_path.exists():
            try:
                content = banwords_path.read_text(encoding='utf-8')
                existing_data = json.loads(content)
            except:
                pass
        
        # 构建新的数据结构
        new_data = {
            "description": existing_data.get("description", "敏感词库配置文件"),
            "version": existing_data.get("version", "1.0.0"),
            "lastUpdate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "library": library_data
        }
        
        # 备份原文件
        if banwords_path.exists():
            backup_path = banwords_path.with_suffix('.json.bak')
            backup_path.write_text(banwords_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        # 写入新文件
        with open(banwords_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"保存敏感词文件失败: {e}")
        return False

@router.get("/banwords")
async def get_banwords():
    """获取所有敏感词分类和词汇"""
    try:
        library_data = load_banwords_from_json()
        
        # 转换为前端需要的格式
        result = {}
        for category, config in library_data.items():
            result[category] = {
                'defaultRisk': config.get('defaultRisk', 3),
                'words': config.get('words', []),
                'patterns': config.get('patterns', [])
            }
        
        return Response.success(
            data={'library': result},
            message="获取敏感词库成功"
        )
        
    except Exception as e:
        logger.error(f"获取敏感词失败: {e}")
        raise HTTPException(status_code=500, detail="获取敏感词失败")

@router.get("/banwords/categories")
async def get_banword_categories():
    """获取敏感词分类列表"""
    try:
        library_data = load_banwords_from_json()
        categories = list(library_data.keys())
        
        return Response.success(
            data={'categories': categories},
            message="获取敏感词分类成功"
        )
        
    except Exception as e:
        logger.error(f"获取敏感词分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取敏感词分类失败")

@router.post("/banwords")
async def add_banwords(request: BanwordRequest):
    """添加敏感词到指定分类"""
    try:
        library_data = load_banwords_from_json()
        
        # 确保分类存在
        if request.category not in library_data:
            library_data[request.category] = {
                'defaultRisk': request.risk,
                'words': [],
                'patterns': []
            }
        
        # 添加新词汇，避免重复
        existing_words = set(library_data[request.category].get('words', []))
        new_words = [word for word in request.words if word not in existing_words]
        
        if new_words:
            library_data[request.category]['words'].extend(new_words)
            
            # 保存到文件
            if save_banwords_to_json(library_data):
                return Response.success(
                    data={'added_count': len(new_words)},
                    message=f"成功添加{len(new_words)}个敏感词"
                )
            else:
                raise HTTPException(status_code=500, detail="保存敏感词失败")
        else:
            return Response.success(
                data={'added_count': 0},
                message="没有新的敏感词需要添加"
            )
            
    except Exception as e:
        logger.error(f"添加敏感词失败: {e}")
        raise HTTPException(status_code=500, detail="添加敏感词失败")

@router.delete("/banwords/{category}/{word}")
async def delete_banword(category: str, word: str):
    """删除指定分类中的敏感词"""
    try:
        library_data = load_banwords_from_json()
        
        if category not in library_data:
            raise HTTPException(status_code=404, detail=f"分类 {category} 不存在")
        
        words = library_data[category].get('words', [])
        if word in words:
            words.remove(word)
            library_data[category]['words'] = words
            
            if save_banwords_to_json(library_data):
                return Response.success(
                    data={},
                    message=f"成功删除敏感词: {word}"
                )
            else:
                raise HTTPException(status_code=500, detail="保存敏感词失败")
        else:
            raise HTTPException(status_code=404, detail=f"敏感词 {word} 不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除敏感词失败: {e}")
        raise HTTPException(status_code=500, detail="删除敏感词失败")

@router.put("/banwords/{category}")
async def update_banword_category(category: str, words: List[str]):
    """更新指定分类的所有敏感词"""
    try:
        library_data = load_banwords_from_json()
        
        if category not in library_data:
            raise HTTPException(status_code=404, detail=f"分类 {category} 不存在")
        
        library_data[category]['words'] = words
        
        if save_banwords_to_json(library_data):
            return Response.success(
                data={'word_count': len(words)},
                message=f"成功更新分类 {category} 的敏感词"
            )
        else:
            raise HTTPException(status_code=500, detail="保存敏感词失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新敏感词分类失败: {e}")
        raise HTTPException(status_code=500, detail="更新敏感词分类失败") 