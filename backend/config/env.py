"""
环境变量加载工具
优先读取 .env 文件，再从系统环境变量中取值，不依赖第三方包
"""
import os
from pathlib import Path


def _load_dotenv():
    """解析项目根目录下的 .env 文件，将键值对注入 os.environ（已有的不覆盖）"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # 不覆盖系统已有的环境变量，方便生产环境直接注入
            os.environ.setdefault(key, value)


# 模块被 import 时立即执行
_load_dotenv()

# 提供一个简化的接口获取环境变量
def get(key: str, default: str = "") -> str:
    """获取环境变量，未找到时返回 default"""
    return os.environ.get(key, default)
