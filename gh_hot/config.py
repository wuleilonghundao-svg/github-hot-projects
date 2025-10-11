import os
import yaml
from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    days: int
    top_n: int
    languages: List[str]
    use_growth: bool
    token: str | None


def load_settings(config_path: str) -> Settings:
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}

    days = int(os.getenv('GH_HOT_DAYS', cfg.get('days', 7)))
    top_n = int(os.getenv('GH_HOT_TOP_N', cfg.get('top_n', 50)))
    langs_env = os.getenv('GH_HOT_LANGS')
    languages = (
        [s.strip() for s in langs_env.split(',') if s.strip()]
        if langs_env else cfg.get('languages', ['All'])
    )
    use_growth_env = os.getenv('GH_HOT_USE_GROWTH')
    use_growth = (
        (use_growth_env == '1') if use_growth_env is not None else bool(cfg.get('use_growth', True))
    )
    token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')

    return Settings(days=days, top_n=top_n, languages=languages, use_growth=use_growth, token=token)

