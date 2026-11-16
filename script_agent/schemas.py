"""Input schema for a script request (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from script_agent import config


class Metadata(BaseModel):
    platform: str = Field(min_length=1, description="e.g. TikTok, YouTube Shorts")
    audience: str = Field(min_length=1, description="Target audience")
    duration: float = Field(gt=0, description="Video length in MINUTES (0.5 = 30s)")

    @field_validator("platform", "audience")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("duration")
    @classmethod
    def _check_duration(cls, v: float) -> float:
        seconds = v * 60
        if abs(seconds - round(seconds)) > 1e-6:
            raise ValueError("duration must be a whole number of seconds")
        if not config.MIN_DURATION_SECONDS <= seconds <= config.MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration must be between {config.MIN_DURATION_SECONDS}s and "
                f"{config.MAX_DURATION_SECONDS}s, got {round(seconds)}s"
            )
        return v

    @property
    def duration_seconds(self) -> int:
        return round(self.duration * 60)


class ScriptRequest(BaseModel):
    topic: str = Field(min_length=1)
    screenplay: str = Field(default="", description="Optional brief / creative direction")
    scenes: list[str] = Field(default_factory=list, description="Optional scene ideas")
    characters: list[str] = Field(default_factory=list, description="Optional characters")
    metadata: Metadata

    @field_validator("topic")
    @classmethod
    def _strip_topic(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v
