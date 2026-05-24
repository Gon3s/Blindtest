import { Component, EventEmitter, Input, Output } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';

@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    @if (loading) {
      <span class="btn__spinner" aria-hidden="true"></span>
    }
    <ng-content />
  `,
  styleUrl: './app-button.component.scss',
  host: {
    class: 'btn',
    '[class.btn-primary]': "variant === 'primary'",
    '[class.btn-secondary]': "variant === 'secondary'",
    '[class.btn-success]': "variant === 'success'",
    '[class.btn-danger]': "variant === 'danger'",
    '[class.btn-ghost]': "variant === 'ghost'",
    '[class.btn--loading]': 'loading',
    '[class.btn--disabled]': 'disabled || loading',
    '[attr.role]': '"button"',
    '[attr.tabindex]': 'disabled || loading ? -1 : 0',
    '[attr.aria-disabled]': 'disabled || loading ? true : null',
    '(click)': 'handleClick($event)',
    '(keydown.enter)': 'handleClick($event)',
    '(keydown.space)': 'handleSpaceKey($event)',
  },
})
export class AppButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() loading = false;
  @Input() disabled = false;
  @Output() readonly clicked = new EventEmitter<void>();

  handleClick(event: Event): void {
    if (this.disabled || this.loading) {
      event.stopPropagation();
      return;
    }
    this.clicked.emit();
  }

  handleSpaceKey(event: Event): void {
    event.preventDefault();
    this.handleClick(event);
  }
}
