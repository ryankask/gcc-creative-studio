# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.base_dto import (
    AspectRatioEnum,
    ColorAndToneEnum,
    CompositionEnum,
    LightingEnum,
    MimeTypeEnum,
    StyleEnum,
)
from src.common.base_repository import BaseDocument
from src.common.schema.media_item_model import (
    SourceAssetLink,
)
from src.database import Base


class IndustryEnum(str, Enum):
    """Enum for categorizing templates by industry."""

    AUTOMOTIVE = "Automotive"
    CONSUMER_GOODS = "Consumer Goods"
    ART_AND_DESIGN = "Art & Design"
    ENTERTAINMENT = "Entertainment"
    HOME_APPLIANCES = "Home Appliances"
    FASHION_AND_APPAREL = "Fashion & Apparel"
    FOOD_AND_BEVERAGE = "Food & Beverage"
    HEALTH_AND_WELLNESS = "Health & Wellness"
    LUXURY_GOODS = "Luxury Goods"
    TECHNOLOGY = "Technology"
    TRAVEL_AND_HOSPITALITY = "Travel & Hospitality"
    PET_SUPPLIES = "Pet Supplies"
    OTHER = "Other"


class GenerationParameters(BaseModel):
    """A nested model to cleanly bundle all settings that will be passed
    to the media generation UI or service.
    """

    prompt: str | None = None
    model: str | None = None
    aspect_ratio: AspectRatioEnum | None = None
    style: StyleEnum | None = None
    lighting: LightingEnum | None = None
    color_and_tone: ColorAndToneEnum | None = None
    composition: CompositionEnum | None = None
    negative_prompt: str | None = None

    model_config = ConfigDict(
        use_enum_values=True,  # Allows passing enum members like StyleEnum.MODERN
        extra="forbid",  # Prevents accidental extra fields
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )


class MediaTemplate(Base):
    """SQLAlchemy model for the 'media_templates' table."""

    __tablename__ = "media_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    mime_type: Mapped[MimeTypeEnum] = mapped_column(String, nullable=False)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)

    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])

    gcs_uris: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    thumbnail_uris: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])

    generation_parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)

    source_assets: Mapped[list[dict] | None] = mapped_column(
        JSONB, nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )


class MediaTemplateModel(BaseDocument):
    """Represents a unified, pre-configured, and queryable template for media generation,
    incorporating strong validation and a clean structure.
    """

    id: int | None = None

    # Using Field(..., min_length=1) for required, non-empty strings
    name: Annotated[
        str,
        Field(
            min_length=1,
            description="The display name of the template, e.g., 'Cinematic Rolex Watch Ad'.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            min_length=1,
            description="A brief explanation of what the template is for and its intended use case.",
        ),
    ]

    # --- Categorization & Filtering Fields ---
    mime_type: MimeTypeEnum = Field(
        description="The primary type of mime type this template generates.",
    )
    industry: IndustryEnum | None = Field(
        default=None,
        description="The target industry for this template.",
    )
    brand: str | None = Field(
        default=None,
        description="The specific brand this template is inspired by, e.g., 'IKEA'.",
    )
    tags: list[str] | None = Field(
        default_factory=list,
        description="A list of searchable keywords for filtering, e.g., ['futuristic', 'vibrant'].",
    )

    # --- UI Display Fields ---
    # Using str for automatic URL validation
    gcs_uris: Annotated[
        list[str],
        Field(
            min_length=1,
            description="A list of public URLs for the media to be displayed (e.g., video or image).",
        ),
    ]
    thumbnail_uris: Annotated[
        list[str] | None,
        Field(
            description="The public, permanent URL of the thumbnail image for this template.",
        ),
    ]

    # --- Nested Generation Parameters ---
    generation_parameters: GenerationParameters

    # --- Source Asset Information ---
    source_assets: list[SourceAssetLink] | None = Field(
        default=None,
        description="Links to source assets from the 'user_assets' collection used for generation.",
    )
