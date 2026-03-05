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

import { Component, Input, Output, EventEmitter, OnDestroy, Inject, PLATFORM_ID } from '@angular/core';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { GalleryItem } from '../../models/gallery-item.model';
import { MediaItemSelection } from '../image-selector/image-selector.component';
import { MediaItem } from '../../models/media-item.model';

@Component({
  selector: 'app-gallery-card',
  templateUrl: './gallery-card.component.html',
  styleUrls: ['./gallery-card.component.scss'],
})
export class GalleryCardComponent implements OnDestroy {
  constructor(
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}
  @Input() item!: GalleryItem;
  @Input() isSelectionMode: boolean = false;
  @Input() isSelected: boolean = false;
  @Input() anyItemSelected: boolean = false;
  
  @Output() mediaItemSelected = new EventEmitter<MediaItemSelection>();
  @Output() mediaSelected = new EventEmitter<GalleryItem>();

  currentImageIndex: number = 0;
  loadedMedia: Record<number, boolean> = {};
  hoveredVideoId: number | null = null;
  hoveredAudioId: number | null = null;
  
  get displayUrls(): string[] {
    if (this.item.presignedThumbnailUrls && this.item.presignedThumbnailUrls.length > 0) {
      return this.item.presignedThumbnailUrls;
    }
    return this.item.presignedUrls || [];
  }

  get displayPaddingBottom(): string {
    const rawRatio = this.item.aspectRatio;
    const gap = 16; // gap-4 is 1rem = 16px

    // Default handles for no ratio
    if (!rawRatio) {
      if (this.item.mimeType?.startsWith('audio/')) {
        return `calc(50% - ${gap / 2}px)`; // 2:1 for audio
      }
      if (this.item.mimeType?.startsWith('video/')) {
        return '100%'; // 1:1 default for video if unknown (16:9 would be closer to 2:1)
      }
      return '100%'; // 1:1 default
    }

    const parts = rawRatio.split(':').map(Number);
    if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1]) || parts[1] === 0) {
      return '100%';
    }
    const ratio = parts[0] / parts[1];

    // Thresholds:
    // 2:1 if ratio >= 2
    // 1:2 if ratio <= 0.5
    // 1:1 otherwise
    if (ratio >= 2) {
      return `calc(50% - ${gap / 2}px)`; // 2:1
    } else if (ratio <= 0.5) {
      return `calc(200% + ${gap}px)`; // 1:2
    } else {
      return '100%'; // 1:1
    }
  }

  ngOnDestroy() {
  }

  onMouseEnter() {
    if (this.item.mimeType?.startsWith('video/')) {
      this.hoveredVideoId = this.item.id;
    }
    if (this.item.mimeType?.startsWith('audio/')) {
      this.hoveredAudioId = this.item.id;
    }
  }

  onMouseLeave() {
    this.hoveredVideoId = null;
    this.hoveredAudioId = null;
  }

  nextImageItem(event: Event) {
    event.stopPropagation();
    event.preventDefault();
    const total = this.displayUrls.length;
    this.currentImageIndex = (this.currentImageIndex + 1) % total;
  }

  prevImageItem(event: Event) {
    event.stopPropagation();
    event.preventDefault();
    const total = this.displayUrls.length;
    this.currentImageIndex = (this.currentImageIndex - 1 + total) % total;
  }

  onMediaLoad(index: number = 0): void {
    this.loadedMedia[index] = true;
  }

  isMediaLoaded(index: number = 0): boolean {
    return !!this.loadedMedia[index];
  }

  selectMedia(event: Event): void {
    if (this.isSelectionMode || this.anyItemSelected) {
      event.preventDefault();
      
      if (this.isSelectionMode) {
        this.mediaItemSelected.emit({
          mediaItem: this.item as unknown as MediaItem,
          selectedIndex: this.currentImageIndex
        });
      }
    }
  }

  onSelectionClick(event: Event): void {
    event.preventDefault();
  }

  onDblClick(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    
    const route = this.item.itemType === 'source_asset'
      ? ['/asset-detail', this.item.id]
      : ['/gallery', this.item.id];
      
    this.router.navigate(route, { state: { mediaItem: this.item } });
  }

  getShortPrompt(prompt: string | undefined | null, wordLimit = 20): string {
    if (!prompt) return 'Generated media';
    let textToTruncate = prompt;
    try {
      const parsedPrompt = JSON.parse(prompt);
      if (parsedPrompt && typeof parsedPrompt === 'object' && parsedPrompt.prompt_name) {
        textToTruncate = parsedPrompt.prompt_name;
      }
    } catch (e) {}
    const words = textToTruncate.split(/\s+/);
    if (words.length > wordLimit) return words.slice(0, wordLimit).join(' ') + '...';
    return textToTruncate;
  }
}
