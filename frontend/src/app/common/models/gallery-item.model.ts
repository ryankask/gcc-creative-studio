/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { PaginatedResponse } from './paginated-response.model';

export interface GalleryItem {
  id: number;
  workspaceId: number;
  userId?: number;
  createdAt: string;
  itemType: 'media_item' | 'source_asset';
  status?: string;

  // Display fields (mapped from metadata)
  mimeType?: string;
  aspectRatio?: string;
  prompt?: string;
  originalPrompt?: string;

  // Unified arrays
  gcsUris?: string[];
  originalGcsUris?: string[];
  thumbnailUris?: string[];

  // Presigned URLs (injected by service)
  presignedUrls?: string[];
  originalPresignedUrls?: string[];
  presignedThumbnailUrls?: string[];

  // Detailed fields (optional, populated when available)
  model?: string;
  userEmail?: string;
  generationTime?: number;
  voiceName?: string;
  languageCode?: string;
  seed?: number;
  numMedia?: number;
  duration?: number;
  resolution?: string;
  googleSearch?: boolean;
  groundingMetadata?: any;
  rewrittenPrompt?: string;
  negativePrompt?: string;
  enrichedSourceAssets?: any[];
  enrichedSourceMediaItems?: any[];
  style?: string;
  lighting?: string;
  colorAndTone?: string;
  composition?: string;
  modifiers?: string[];
  comment?: string;
  critique?: string;
  rawData?: any;
  audioAnalysis?: any;
  error_message?: string;
  addWatermark?: boolean;

  // Metadata (loosely typed as it varies by itemType)
  metadata: Record<string, any>;
}

export type PaginatedGalleryResponse = PaginatedResponse<GalleryItem>;
