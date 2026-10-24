import os
from dataclasses import dataclass, field


class ConfigurationError(ValueError):
    """模型调用前可检查的配置错误。"""


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model: str

    @classmethod
    def from_env(cls):
        key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        model = os.environ.get("DEEPSEEK_MODEL", "").strip()
        if not key:
            raise ConfigurationError("real 模式需要 DEEPSEEK_API_KEY，请在本机环境或 .env 中配置。")
        if not model:
            raise ConfigurationError("real 模式需要 DEEPSEEK_MODEL，请填写可用的模型名称。")
        return cls(api_key=key, model=model)
