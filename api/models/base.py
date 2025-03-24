"""
API基础模型
定义所有API模型的基类
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

class BaseModelConfig:
    """基础模型配置"""
    model_config = ConfigDict(
        from_attributes=True,  # 支持ORM模型转换
        populate_by_name=True,  # 支持别名
        use_enum_values=True,  # 枚举使用值而不是枚举对象
        validate_assignment=True,  # 赋值时验证
        json_schema_extra={"example": {}},  # 示例数据
        arbitrary_types_allowed=True,  # 允许任意类型
    )

class BaseAPIModel(BaseModel):
    """API基础模型"""
    model_config = ConfigDict(from_attributes=True)

class TimeStampMixin(BaseModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    @field_validator("updated_at", mode="before")
    def default_updated_at(cls, v):
        """更新时间默认为当前时间"""
        return v or datetime.now()

class MetadataMixin(BaseModel):
    """元数据混入类"""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")

class BaseTimeStampModel(BaseAPIModel, TimeStampMixin):
    """带时间戳的基础模型"""
    pass

class BaseMetadataModel(BaseAPIModel, MetadataMixin):
    """带元数据的基础模型"""
    pass

class BaseFullModel(BaseTimeStampModel, MetadataMixin):
    """完整的基础模型(时间戳+元数据)"""
    pass 