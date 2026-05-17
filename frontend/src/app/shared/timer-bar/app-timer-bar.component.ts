import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-timer-bar',
  standalone: true,
  template: `
    <div class="timer-bar__track">
      <div
        class="timer-bar__fill"
        [class.timer-bar__fill--urgent]="progress < 0.25"
        [style.width.%]="progress * 100"
      ></div>
    </div>
    <span
      class="timer-bar__time"
      data-testid="timer"
      [class.timer-bar__time--urgent]="progress < 0.25"
      aria-live="polite"
      aria-atomic="true"
    >{{ timeLeft }}</span>
  `,
  styleUrl: './app-timer-bar.component.scss',
})
export class AppTimerBarComponent {
  @Input() progress = 1;
  @Input() timeLeft = 0;
}
