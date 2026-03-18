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

from pydantic import Field

from src.common.dto.base_search_dto import BaseSearchDto
from src.media_templates.schema.media_template_model import (
    IndustryEnum,
    MimeTypeEnum,
)


class TemplateSearchDto(BaseSearchDto):
    """Defines the searchable and filterable fields for the template gallery."""

    # Filtering fields based on MediaTemplateModel
    industry: IndustryEnum | None = None
    brand: str | None = None
    mime_type: MimeTypeEnum | None = None
    # For tags, we'll likely search one at a time
    tag: str | None = Field(
        default=None, description="A single tag to filter by."
    )
