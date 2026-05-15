import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { Participant, WebSocketService, WsEvent } from '../../services/websocket.service';

@Component({
  selector: 'app-lobby-page',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './lobby-page.component.html',
  styleUrl: './lobby-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LobbyPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly wsService = inject(WebSocketService);

  readonly code = toSignal(
    this.route.paramMap.pipe(map(p => p.get('code') ?? '')),
    { initialValue: '' },
  );
  readonly participants = signal<Participant[]>([]);

  private subscription?: Subscription;

  ngOnInit(): void {
    const state = history.state as { room_id?: string };
    const roomId = state.room_id ?? '';

    if (!roomId) {
      void this.router.navigate(['/']);
      return;
    }

    this.wsService.connect(roomId);
    this.subscription = this.wsService.messages$.subscribe((event: WsEvent) => {
      if (event.event === 'room.state') {
        const d = event.data as { participants: Participant[] };
        this.participants.set(d.participants);
      } else if (event.event === 'participant.joined') {
        const p = event.data as Participant;
        this.participants.update(list => [...list, p]);
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.wsService.disconnect();
  }
}
