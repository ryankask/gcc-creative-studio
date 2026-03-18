/**
 * Copyright 2026 Google LLC
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

import {
  Component,
  EventEmitter,
  Input,
  Output,
  HostListener,
  ElementRef,
  HostBinding,
} from '@angular/core';
import {trigger, state, style, transition, animate} from '@angular/animations';

export interface DropdownOption {
  value: any;
  label: string;
  icon?: string;
  isSvgIcon?: boolean;
}

@Component({
  selector: 'studio-dropdown',
  templateUrl: './studio-dropdown.component.html',
  styleUrls: ['./studio-dropdown.component.scss'],
  animations: [
    trigger('dropdownAnimation', [
      state(
        'closed',
        style({
          height: '0px',
          opacity: 0,
          overflow: 'hidden',
          paddingTop: '0',
          paddingBottom: '0',
        }),
      ),
      state(
        'open',
        style({
          height: '*',
          opacity: 1,
        }),
      ),
      transition(
        'closed <=> open',
        animate('250ms cubic-bezier(0.4, 0, 0.2, 1)'),
      ),
    ]),
  ],
})
export class StudioDropdownComponent {
  @Input() options: DropdownOption[] = [];
  @Input() value: any;
  @Input() placeholder = 'Select an option';
  @Input() icon = ''; // Optional leading icon for the trigger button
  @Input() isSvgIcon = false;
  @Input() menuTitle = ''; // Title shown inside the dropdown menu
  @Input() size: 'small' | 'medium' | 'large' | 'default' = 'default';

  @Output() valueChange = new EventEmitter<any>();

  isOpen = false;

  @HostBinding('class') get hostClasses() {
    return `size-${this.size}`;
  }

  constructor(private elementRef: ElementRef) {}

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
    }
  }

  get selectedLabel(): string {
    const selected = this.options.find(opt => opt.value === this.value);
    return selected ? selected.label : this.placeholder;
  }

  toggleDropdown(event: Event) {
    event.stopPropagation();
    this.isOpen = !this.isOpen;
  }

  selectOption(option: DropdownOption) {
    this.value = option.value;
    this.valueChange.emit(this.value);
    this.isOpen = false;
  }
}
