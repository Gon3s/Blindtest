import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AppButtonComponent } from '../../shared/button/app-button.component';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { AudioService } from '../../services/audio.service';
import { RoomService } from '../../services/room.service';
import { Session, SessionService } from '../../services/session.service';
import {
  ConnectionStatus,
  Participant,
  WebSocketService,
  WsEvent,
} from '../../services/websocket.service';
import { PREDEFINED_THEMES } from '../../shared/predefined-themes';

@Component({
  selector: 'app-lobby-page',
  standalone: true,
  imports: [RouterLink, AppButtonComponent, FormsModule],
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
  private readonly sessionService = inject(SessionService);

  readonly code = toSignal(this.route.paramMap.pipe(map((p) => p.get('code') ?? '')), {
    initialValue: '',
  });
  readonly participants = signal<Participant[]>([]);
  readonly isHost = signal(false);
  readonly nickname = signal('');
  readonly theme = signal('');
  readonly answerMode = signal<'both' | 'title_only' | 'artist_only'>('both');
  readonly sessionRestoreError = signal(false);
  readonly predefinedThemes = PREDEFINED_THEMES;
  readonly connectionStatus = signal<ConnectionStatus>('disconnected');

  private roomId = '';
  private participantId = '';
  private hostToken = '';
  private subscription?: Subscription;
  private wsStatusSubscription?: Subscription;

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
      const session = this.sessionService.loadSession();
      if (session && session.roomCode === this.code()) {
        this.restoreFromSession(session);
      } else {
        void this.router.navigate(['/']);
      }
      return;
    }

    this.isHost.set(state.role === 'host');
    this.nickname.set(state.nickname ?? '');
    this.participantId = state.participant_id ?? state.host_id ?? '';
    const session = this.sessionService.loadSession();
    this.hostToken = session?.hostToken ?? '';
    this.wsConnect();
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.wsStatusSubscription?.unsubscribe();
    this.wsService.disconnect();
  }

  startRound(): void {
    this.roomService
      .startRound(this.roomId, this.theme().trim(), this.hostToken, this.answerMode())
      .subscribe();
  }

  quit(): void {
    if (this.isHost() && this.roomId && this.hostToken) {
      this.roomService.closeRoom(this.roomId, this.hostToken).subscribe({
        next: () => {
          this.sessionService.clearSession();
          void this.router.navigate(['/']);
        },
        error: () => {
          this.sessionService.clearSession();
          void this.router.navigate(['/']);
        },
      });
    } else {
      this.sessionService.clearSession();
      void this.router.navigate(['/']);
    }
  }

  private restoreFromSession(session: Session): void {
    this.hostToken = session.hostToken ?? '';
    this.roomService.getRoomState(session.roomCode).subscribe({
      next: (roomState) => {
        this.roomId = roomState.room_id;
        this.isHost.set(session.role === 'host');
        this.nickname.set(session.nickname);
        this.participantId = session.participantId;

        if (['round_in_progress', 'reveal'].includes(roomState.status) && roomState.current_song) {
          const cs = roomState.current_song;
          void this.router.navigate(['/play', session.roomCode], {
            state: {
              room_id: roomState.room_id,
              participant_id: session.participantId,
              nickname: session.nickname,
              is_host: session.role === 'host',
              host_id: session.role === 'host' ? session.participantId : '',
              song_id: cs.song_id,
              song_index: cs.song_index,
              round_id: cs.round_id,
              total_songs: cs.total_songs,
              ends_at: cs.ends_at,
            },
          });
        } else {
          this.wsConnect();
        }
      },
      error: (err: { status?: number }) => {
        if (err.status === 404) {
          this.sessionService.clearSession();
        }
        this.sessionRestoreError.set(true);
      },
    });
  }

  private wsConnect(): void {
    this.wsService.connect(this.roomId);
    this.wsStatusSubscription = this.wsService.connectionStatus$.subscribe((status) => {
      this.connectionStatus.set(status);
    });
    this.subscription = this.wsService.messages$.subscribe((event: WsEvent) => {
      if (event.event === 'room.state') {
        const d = event.data as { participants: Participant[] };
        this.participants.set(d.participants);
      } else if (event.event === 'participant.joined') {
        const p = event.data as Participant;
        this.participants.update((list) => [...list, p]);
      } else if (event.event === 'room.closed') {
        this.sessionService.clearSession();
        void this.router.navigate(['/']);
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
}
