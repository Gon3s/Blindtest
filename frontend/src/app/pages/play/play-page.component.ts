import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { AudioService } from '../../services/audio.service';
import { ErrorService } from '../../services/error.service';
import {
  AnswerSummaryItem,
  MiniLeaderboardItem,
  PlayerRevealItem,
  RoomService,
  RoundLeaderboardItem,
  SongSummaryResponse,
  SubmitAnswerResponse,
} from '../../services/room.service';
import { ConnectionStatus, WebSocketService, WsEvent } from '../../services/websocket.service';
import { SessionService } from '../../services/session.service';
import { PREDEFINED_THEMES } from '../../shared/predefined-themes';
import { AppBadgeComponent } from '../../shared/badge/app-badge.component';
import type { BadgeVariant } from '../../shared/badge/app-badge.component';
import { AppButtonComponent } from '../../shared/button/app-button.component';
import { AppCardComponent } from '../../shared/card/app-card.component';
import { AppTimerBarComponent } from '../../shared/timer-bar/app-timer-bar.component';

type FeedbackState = 'none' | 'not_found' | 'title_found' | 'artist_found' | 'both_found';

interface SongStartedData {
  song_id: string;
  song_index: number;
  round_id: string;
  started_at: string;
  ends_at: string;
  preview_url: string | null;
}

interface SongRevealedData {
  song_id: string;
  title: string;
  artist: string;
  cover_url: string | null;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
}

interface RoundFinishedData {
  room_id: string;
  round_leaderboard: RoundLeaderboardItem[];
}

interface RoundStartedData {
  round_id: string;
  answer_mode?: 'both' | 'title_only' | 'artist_only';
}

interface RoundLeaderboardMergedEntry extends RoundLeaderboardItem {
  total_points: number;
}

@Component({
  selector: 'app-play-page',
  standalone: true,
  imports: [
    FormsModule,
    AppBadgeComponent,
    AppButtonComponent,
    AppCardComponent,
    AppTimerBarComponent,
  ],
  templateUrl: './play-page.component.html',
  styleUrl: './play-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlayPageComponent implements OnInit, OnDestroy {
  private readonly wsService = inject(WebSocketService);
  private readonly roomService = inject(RoomService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly audioService = inject(AudioService);
  private readonly errorService = inject(ErrorService);
  private readonly sessionService = inject(SessionService);

  readonly songIndex = signal(0);
  readonly totalSongs = signal(10);
  readonly timeLeft = signal(0);
  readonly locked = signal(false);
  readonly answer = signal('');
  readonly feedback = signal<FeedbackState>('none');
  readonly submitError = signal<string | null>(null);
  readonly connectionError = signal<string | null>(null);
  readonly connectionStatus = signal<ConnectionStatus>('disconnected');
  readonly isHost = signal(false);
  readonly songSummary = signal<SongSummaryResponse | null>(null);
  readonly summaryLoading = signal(false);
  readonly summaryError = signal<string | null>(null);
  readonly revealData = signal<SongRevealedData | null>(null);
  readonly roundFinishedData = signal<RoundFinishedData | null>(null);
  readonly newRoundTheme = signal('Général');
  readonly newRoundAnswerMode = signal<'both' | 'title_only' | 'artist_only'>('both');
  readonly totalDuration = signal(30);
  readonly predefinedThemes = PREDEFINED_THEMES;

  readonly timerProgress = computed(() => {
    const total = this.totalDuration();
    return total > 0 ? Math.min(1, Math.max(0, this.timeLeft() / total)) : 0;
  });

  readonly sortedAnswers = computed(() => {
    const summary = this.songSummary();
    if (!summary) return [];
    return [
      ...summary.answers.filter((a) => a.validation_status === 'doubtful'),
      ...summary.answers.filter((a) => a.validation_status !== 'doubtful'),
    ];
  });

  readonly myRevealResult = computed(() => {
    const reveal = this.revealData();
    if (!reveal) return null;
    return reveal.player_results.find((r) => r.participant_id === this.participantId) ?? null;
  });

  readonly roundLeaderboardMerged = computed((): RoundLeaderboardMergedEntry[] => {
    const round = this.roundFinishedData();
    if (!round) return [];
    const miniMap = new Map<string, number>();
    this.revealData()?.mini_leaderboard.forEach((m) =>
      miniMap.set(m.participant_id, m.total_points),
    );
    return round.round_leaderboard.map((e) => ({
      ...e,
      total_points: miniMap.get(e.participant_id) ?? 0,
    }));
  });

  readonly podiumEntries = computed(() => this.roundLeaderboardMerged().filter((e) => e.rank <= 3));

  private songId = '';
  private roundId = '';
  private participantId = '';
  private hostToken = '';
  private subscription?: Subscription;
  private wsErrorSubscription?: Subscription;
  private wsStatusSubscription?: Subscription;
  private summarySubscription?: Subscription;
  private timerInterval?: ReturnType<typeof setInterval>;
  private endsAt = new Date();
  private roomId = '';

  onAnswerInput(event: Event): void {
    this.answer.set((event.target as HTMLInputElement).value);
  }

  onThemeInput(event: Event): void {
    this.newRoundTheme.set((event.target as HTMLInputElement).value);
  }

  ngOnInit(): void {
    const state = history.state as {
      room_id?: string;
      song_id?: string;
      participant_id?: string;
      is_host?: boolean;
      host_id?: string;
      song_index?: number;
      round_id?: string;
      total_songs?: number;
      ends_at?: string;
    };

    this.roomId = state.room_id ?? '';
    if (!this.roomId) {
      const code = this.route.snapshot.paramMap.get('code');
      if (code) {
        void this.router.navigate(['/lobby', code]);
      } else {
        void this.router.navigate(['/']);
      }
      return;
    }

    this.songId = state.song_id ?? '';
    this.roundId = state.round_id ?? '';
    this.participantId = state.participant_id ?? '';
    this.isHost.set(state.is_host ?? false);
    const session = this.sessionService.loadSession();
    this.hostToken = session?.hostToken ?? '';
    this.songIndex.set(state.song_index ?? 0);
    this.totalSongs.set(state.total_songs ?? 10);
    this.endsAt = new Date(state.ends_at ?? Date.now());
    this.startTimer();

    this.wsService.connect(this.roomId);
    this.wsErrorSubscription = this.wsService.connectionError$.subscribe((msg) => {
      this.connectionError.set(msg);
      this.cdr.markForCheck();
    });
    this.wsStatusSubscription = this.wsService.connectionStatus$.subscribe((status) => {
      this.connectionStatus.set(status);
      this.cdr.markForCheck();
    });
    this.subscription = this.wsService.messages$.subscribe((event: WsEvent) => {
      if (event.event === 'round.started') {
        const d = event.data as RoundStartedData;
        this.newRoundAnswerMode.set(d.answer_mode ?? 'both');
      } else if (event.event === 'song.started') {
        const d = event.data as SongStartedData;
        this.songId = d.song_id;
        this.roundId = d.round_id;
        this.songIndex.set(d.song_index);
        this.endsAt = new Date(d.ends_at);
        const totalMs = this.endsAt.getTime() - new Date(d.started_at).getTime();
        this.totalDuration.set(Math.max(1, Math.round(totalMs / 1000)));
        this.locked.set(false);
        this.answer.set('');
        this.feedback.set('none');
        this.submitError.set(null);
        this.songSummary.set(null);
        this.summaryLoading.set(false);
        this.summaryError.set(null);
        this.revealData.set(null);
        this.roundFinishedData.set(null);
        this.restartTimer();
        if (d.preview_url) {
          this.audioService.play(d.preview_url);
        }
      } else if (event.event === 'song.locked') {
        this.locked.set(true);
        this.timeLeft.set(0);
        this.stopTimer();
        this.audioService.stop();
        if (this.isHost()) {
          this.fetchSongSummary();
        }
      } else if (event.event === 'song.revealed') {
        this.locked.set(true);
        this.timeLeft.set(0);
        this.stopTimer();
        this.audioService.stop();
        this.revealData.set(event.data as SongRevealedData);
        this.cdr.markForCheck();
      } else if (event.event === 'round.finished') {
        this.roundFinishedData.set(event.data as RoundFinishedData);
        this.cdr.markForCheck();
      } else if (event.event === 'room.closed') {
        this.sessionService.clearSession();
        void this.router.navigate(['/']);
      }
    });
  }

  ngOnDestroy(): void {
    this.stopTimer();
    this.audioService.stop();
    this.subscription?.unsubscribe();
    this.wsErrorSubscription?.unsubscribe();
    this.wsStatusSubscription?.unsubscribe();
    this.summarySubscription?.unsubscribe();
    this.wsService.disconnect();
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

  submitAnswer(): void {
    const text = this.answer().trim();
    if (!text) {
      this.submitError.set('La réponse ne peut pas être vide.');
      this.cdr.markForCheck();
      return;
    }
    this.submitError.set(null);
    this.roomService.submitAnswer(this.songId, this.participantId, text).subscribe({
      next: (res: SubmitAnswerResponse) => {
        if (res.title_found && res.artist_found) {
          this.feedback.set('both_found');
        } else if (res.title_found) {
          this.feedback.set('title_found');
        } else if (res.artist_found) {
          this.feedback.set('artist_found');
        } else {
          this.feedback.set('not_found');
        }
        this.cdr.markForCheck();
      },
      error: (err: { error?: { code?: string; message?: string; detail?: string } }) => {
        this.submitError.set(this.errorService.fromHttpError(err));
        this.cdr.markForCheck();
      },
    });
  }

  revealSong(): void {
    this.roomService.revealSong(this.songId, this.hostToken).subscribe();
  }

  startNewRound(): void {
    this.roomService.restartRound(this.roomId, this.newRoundTheme(), this.newRoundAnswerMode()).subscribe();
  }

  nextSong(): void {
    const nextIndex = this.songIndex() + 1;
    this.roomService.startSong(this.roundId, nextIndex).subscribe();
  }

  badgeVariantFor(status: string): BadgeVariant {
    switch (status) {
      case 'found':
        return 'success';
      case 'not_found':
        return 'danger';
      case 'doubtful':
        return 'warning';
      default:
        return 'neutral';
    }
  }

  acceptAnswer(answer: AnswerSummaryItem): void {
    this.roomService
      .overrideAnswer(this.songId, answer.answer_id, this.hostToken, true, true)
      .subscribe({
        next: (res) => {
          const summary = this.songSummary();
          if (!summary) return;
          this.songSummary.set({
            ...summary,
            answers: summary.answers.map((a) =>
              a.answer_id === res.answer_id
                ? {
                    ...a,
                    title_found: res.title_found,
                    artist_found: res.artist_found,
                    validation_status: res.validation_status,
                  }
                : a,
            ),
          });
          this.cdr.markForCheck();
        },
      });
  }

  private fetchSongSummary(): void {
    this.summarySubscription?.unsubscribe();
    this.summaryLoading.set(true);
    this.summaryError.set(null);
    this.summarySubscription = this.roomService.getSongSummary(this.songId, this.hostToken).subscribe({
      next: (res) => {
        this.songSummary.set(res);
        this.summaryLoading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.summaryLoading.set(false);
        this.summaryError.set('Impossible de charger le résumé.');
        this.cdr.markForCheck();
      },
    });
  }

  private startTimer(): void {
    this.updateTimeLeft();
    this.timerInterval = setInterval(() => {
      this.updateTimeLeft();
      this.cdr.markForCheck();
    }, 1000);
  }

  private restartTimer(): void {
    this.stopTimer();
    this.startTimer();
  }

  private stopTimer(): void {
    if (this.timerInterval != null) {
      clearInterval(this.timerInterval);
      this.timerInterval = undefined;
    }
  }

  private updateTimeLeft(): void {
    const remaining = Math.max(0, Math.ceil((this.endsAt.getTime() - Date.now()) / 1000));
    this.timeLeft.set(remaining);
  }
}
