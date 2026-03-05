import { Component, EventEmitter, Input, Output, HostListener, ElementRef, HostBinding } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';

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
      state('closed', style({
        height: '0px',
        opacity: 0,
        overflow: 'hidden',
        paddingTop: '0',
        paddingBottom: '0'
      })),
      state('open', style({
        height: '*',
        opacity: 1
      })),
      transition('closed <=> open', animate('250ms cubic-bezier(0.4, 0, 0.2, 1)'))
    ])
  ]
})
export class StudioDropdownComponent {
  @Input() options: DropdownOption[] = [];
  @Input() value: any;
  @Input() placeholder: string = 'Select an option';
  @Input() icon: string = ''; // Optional leading icon for the trigger button
  @Input() isSvgIcon: boolean = false;
  @Input() menuTitle: string = ''; // Title shown inside the dropdown menu
  @Input() size: 'small' | 'medium' | 'large' | 'default' = 'default';
  
  @Output() valueChange = new EventEmitter<any>();

  isOpen: boolean = false;

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
