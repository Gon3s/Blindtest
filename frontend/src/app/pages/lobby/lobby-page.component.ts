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
import { AppButtonComponent } from '../../shared/button/app-button.component';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { AudioService } from '../../services/audio.service';
import { RoomService } from '../../services/room.service';
import { Participant, WebSocketService, WsEvent } from '../../services/websocket.service';

@Component({
  selector: 'app-lobby-page',
  standalone: true,
  imports: [RouterLink, AppButtonComponent],
  templateUrl: './lobby-page.component.html',
  styleUrl: './lobby-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LobbyPageComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly wsService = inject(WebSocketService);
  private readonly roomService = inject(RoomService);
  private readonly audioService = inject(AudioService);

  readonly code = toSignal(
    this.route.paramMap.pipe(map(p => p.get('code') ?? '')),
    { initialValue: '' },
  );
  readonly participants = signal<Participant[]>([]);
  readonly isHost = signal(false);
  readonly nickname = signal('');

  private roomId = '';
  private participantId = '';
  private subscription?: Subscription;

  ngOnInit(): void {
    const state = history.state as {
      room_id?: string;
      role?: string;
      nickname?: string;
      participant_id?: string;
      host_id?: string;
    };
    this.roomId = state.room_id ?? '';

    if (!this.roomId) {
      void this.router.navigate(['/']);
      return;
    }

    this.isHost.set(state.role === 'host');
    this.nickname.set(state.nickname ?? '');
    this.participantId = state.participant_id ?? state.host_id ?? '';

    this.wsService.connect(this.roomId);
    this.subscription = this.wsService.messages$.subscribe((event: WsEvent) => {
      if (event.event === 'room.state') {
        const d = event.data as { participants: Participant[] };
        this.participants.set(d.participants);
      } else if (event.event === 'participant.joined') {
        const p = event.data as Participant;
        this.participants.update(list => [...list, p]);
      } else if (event.event === 'song.started') {
        const d = event.data as {
          song_id: string;
          song_index: number;
          round_id: string;
          started_at: string;
          ends_at: string;
          preview_url: string | null;
        };
        if (d.preview_url) {
          this.audioService.play(d.preview_url);
        }
        void this.router.navigate(['/play', this.code()], {
          state: {
            room_id: this.roomId,
            participant_id: this.participantId,
            nickname: this.nickname(),
            is_host: this.isHost(),
            host_id: this.isHost() ? this.participantId : '',
            song_id: d.song_id,
            song_index: d.song_index,
            round_id: d.round_id,
            total_songs: 10,
            ends_at: d.ends_at,
          },
        });
      }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.wsService.disconnect();
  }

  startRound(): void {
    this.roomService.startRound(this.roomId).subscribe();
  }
}
