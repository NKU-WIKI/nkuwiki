"""
测试摘要生成模块
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from etl.transform.abstract import generate_abstract
from loguru import logger

def test_abstract():
    """
    测试摘要生成功能
    """
    # 当前目录下的README.md文件
    readme_path = Path(__file__).resolve().parent / "README.md"
    
    if not readme_path.exists():
        logger.error(f"测试文件不存在: {readme_path}")
        return False
    
    # 生成摘要
    logger.info(f"为文件生成摘要: {readme_path}")
    abstract = generate_abstract(str(readme_path), max_length=150, use_cache=False)
    
    if abstract:
        logger.info(f"生成的摘要: {abstract}")
        return True
    else:
        logger.error("摘要生成失败")
        return False

if __name__ == "__main__":
    # 配置日志
    logger.remove()  # 清除默认处理程序
    logger.add(sys.stdout, level="INFO")  # 添加标准输出处理程序
    
    # 运行测试
    test_result = test_abstract()
    
    if test_result:
        print("\n✅ 测试通过: 摘要生成成功")
    else:
        print("\n❌ 测试失败: 摘要生成失败") 