# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from pydantic import BaseModel


class GenerationOptionsResponse(BaseModel):
    """Defines the shape of the data for frontend dropdown options."""

    generation_models: list[str]
    aspect_ratios: list[str]
    styles: list[str]
    lightings: list[str]
    colors_and_tones: list[str]
    composition: list[str]
    numbers_of_images: list[int]
