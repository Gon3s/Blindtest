import { Component, Input } from '@angular/core';

export type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'neutral';

@Component({
  selector: 'app-badge',
  standalone: true,
  template: `{{ text }}`,
  styleUrl: './app-badge.component.scss',
  host: {
    class: 'badge',
    '[class.badge--success]': "variant === 'success'",
    '[class.badge--danger]': "variant === 'danger'",
    '[class.badge--warning]': "variant === 'warning'",
    '[class.badge--info]': "variant === 'info'",
    '[class.badge--neutral]': "variant === 'neutral'",
  },
})
export class AppBadgeComponent {
  @Input() variant: BadgeVariant = 'neutral';
  @Input() text = '';
}
