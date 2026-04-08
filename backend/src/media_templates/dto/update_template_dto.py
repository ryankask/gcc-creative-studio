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


from src.common.base_dto import BaseDto
from src.media_templates.schema.media_template_model import (
    GenerationParameters,
    IndustryEnum,
)


class UpdateTemplateDto(BaseDto):
    """Defines the fields that can be updated for a MediaTemplate.
    All fields are optional.
    """

    name: str | None = None
    description: str | None = None
    industry: IndustryEnum | None = None
    brand: str | None = None
    tags: list[str] | None = None
    gcs_uris: list[str] | None = None
    thumbnail_uris: list[str] | None = None
    source_assets: list[str] | None = None
    generation_parameters: GenerationParameters | None = None
