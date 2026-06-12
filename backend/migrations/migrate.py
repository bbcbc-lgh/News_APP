"""
数据库迁移运行器（轻量版，不依赖 alembic）

使用方式：
  python migrations/migrate.py            # 执行所有未应用的迁移
  python migrations/migrate.py --status   # 查看当前迁移状态
  python migrations/migrate.py --rollback # 回滚最后一次迁移

迁移文件放在 migrations/versions/ 目录下，文件名格式：
  0001_initial.py
  0002_add_search_index.py
  ...

每个迁移文件需实现两个函数：
  def upgrade(conn): ...   # 应用迁移
  def downgrade(conn): ... # 回滚迁移
"""
import sys
import importlib.util
import asyncio
from pathlib import Path
from datetime import datetime

# 确保能找到项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from config.env import get

DATABASE_URL = get("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/news_app?charset=utf8mb4")
VERSIONS_DIR = Path(__file__).parent / "versions"

# 迁移记录表，用于追踪哪些迁移已经执行过
MIGRATION_TABLE = sa.Table(
    "_migrations",
    sa.MetaData(),
    sa.Column("version", sa.String(255), primary_key=True),
    sa.Column("applied_at", sa.DateTime, default=datetime.now),
)


async def ensure_migration_table(conn: AsyncConnection):
    """确保迁移记录表存在"""
    await conn.run_sync(MIGRATION_TABLE.metadata.create_all)


async def get_applied_versions(conn: AsyncConnection) -> set:
    """查询已执行的迁移版本号"""
    result = await conn.execute(sa.select(MIGRATION_TABLE.c.version))
    return {row[0] for row in result}


async def mark_applied(conn: AsyncConnection, version: str):
    """记录某个迁移版本已执行"""
    await conn.execute(
        MIGRATION_TABLE.insert().values(version=version, applied_at=datetime.now())
    )


async def mark_rolled_back(conn: AsyncConnection, version: str):
    """删除某个迁移版本的执行记录"""
    await conn.execute(
        MIGRATION_TABLE.delete().where(MIGRATION_TABLE.c.version == version)
    )


def load_migration(path: Path):
    """动态加载迁移文件模块"""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_all_versions() -> list[Path]:
    """获取所有迁移文件，按文件名排序"""
    return sorted(VERSIONS_DIR.glob("*.py"))


async def run_migrate():
    """执行所有未应用的迁移"""
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await ensure_migration_table(conn)
        applied = await get_applied_versions(conn)
        files = get_all_versions()
        pending = [f for f in files if f.stem not in applied]
        if not pending:
            print("[OK] All migrations are up to date.")
            return
        for f in pending:
            print(f"  applying: {f.stem} ...", end=" ", flush=True)
            module = load_migration(f)
            await module.upgrade(conn)
            await mark_applied(conn, f.stem)
            print("done")
    await engine.dispose()


async def run_status():
    """查看迁移状态"""
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await ensure_migration_table(conn)
        applied = await get_applied_versions(conn)
        files = get_all_versions()
        print(f"\nMigration status ({len(files)} total):")
        for f in files:
            status = "[applied]" if f.stem in applied else "[pending]"
            print(f"  {status}  {f.stem}")
    await engine.dispose()


async def run_rollback():
    """回滚最后一次迁移"""
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await ensure_migration_table(conn)
        applied = await get_applied_versions(conn)
        files = [f for f in get_all_versions() if f.stem in applied]
        if not files:
            print("Nothing to roll back.")
            return
        last = files[-1]
        print(f"  rolling back: {last.stem} ...", end=" ", flush=True)
        module = load_migration(last)
        await module.downgrade(conn)
        await mark_rolled_back(conn, last.stem)
        print("done")
    await engine.dispose()


if __name__ == "__main__":
    if "--status" in sys.argv:
        asyncio.run(run_status())
    elif "--rollback" in sys.argv:
        asyncio.run(run_rollback())
    else:
        asyncio.run(run_migrate())
