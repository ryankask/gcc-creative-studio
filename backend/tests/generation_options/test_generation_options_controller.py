# Copyright 2026 Google LLC
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
"""Tests for Generation Options Controller."""


import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.generation_options.generation_options_controller import router


@pytest.fixture(name="client")
def fixture_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_image_generation_options_success(client):
    response = client.get("/api/options/image-generation")
    assert response.status_code == 200
    data = response.json()
    # verify some fields exist
    assert "generation_models" in data or "generationModels" in data
    assert "styles" in data
