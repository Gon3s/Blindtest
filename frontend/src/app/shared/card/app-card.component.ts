import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    @if (title) {
      <h3 class="card__title">{{ title }}</h3>
    }
    <ng-content />
  `,
  styleUrl: './app-card.component.scss',
  host: {
    class: 'card',
  },
})
export class AppCardComponent {
  @Input() title?: string;
}
