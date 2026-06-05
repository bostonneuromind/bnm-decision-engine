"""FischerLevel — bnm-learning-engine ml/types.py에서 미러 (변경 금지).

mappings 5함수가 의존하는 최소 타입만. 원본: bnm-learning-engine/ml/types.py:FischerLevel.
(a)안 미러: 변환 로직은 learning repo가 원본, 여기는 decision Flask 호출용 복제.
"""

from pydantic import BaseModel, Field


class FischerLevel(BaseModel):
    """Fischer L + confidence + markers."""
    level: float = Field(..., ge=1.0, le=13.5, description="L1-L13b")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    markers_matched: list = []

    @property
    def integer_level(self) -> int:
        return int(self.level)

    @property
    def progress_to_next(self) -> float:
        return self.level - self.integer_level
