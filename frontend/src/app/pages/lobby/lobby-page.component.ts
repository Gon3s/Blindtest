import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';

@Component({
  selector: 'app-lobby-page',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './lobby-page.component.html',
  styleUrl: './lobby-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LobbyPageComponent {
  private readonly route = inject(ActivatedRoute);
  readonly code = toSignal(
    this.route.paramMap.pipe(map(p => p.get('code') ?? '')),
    { initialValue: '' },
  );
}
