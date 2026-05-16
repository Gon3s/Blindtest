import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { RoomService, SubmitAnswerResponse } from '../../services/room.service';
import { WebSocketService, WsEvent } from '../../services/websocket.service';

type FeedbackState = 'none' | 'not_found' | 'title_found' | 'artist_found' | 'both_found';

interface SongStartedData {
  song_id: string;
  song_index: number;
  round_id: string;
  started_at: string;
  ends_at: string;
}

@Component({
  selector: 'app-play-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './play-page.component.html',
  styleUrl: './play-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlayPageComponent implements OnInit, OnDestroy {
  private readonly wsService = inject(WebSocketService);
  private readonly roomService = inject(RoomService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  readonly songIndex = signal(0);
  readonly totalSongs = signal(10);
  readonly timeLeft = signal(0);
  readonly locked = signal(false);
  readonly answer = signal('');
  readonly feedback = signal<FeedbackState>('none');
  readonly submitError = signal<string | null>(null);

  private songId = '';
  private participantId = '';
  private subscription?: Subscription;
  private timerInterval?: ReturnType<typeof setInterval>;
  private endsAt = new Date();
  private roomId = '';

  onAnswerInput(event: Event): void {
    this.answer.set((event.target as HTMLInputElement).value);
  }

  ngOnInit(): void {
    const state = history.state as {
      room_id?: string;
      song_id?: string;
      participant_id?: string;
      song_index?: number;
      total_songs?: number;
      ends_at?: string;
    };

    this.roomId = state.room_id ?? '';
    if (!this.roomId) {
      void this.router.navigate(['/']);
      return;
    }

    this.songId = state.song_id ?? '';
    this.participantId = state.participant_id ?? '';
    this.songIndex.set(state.song_index ?? 0);
    this.totalSongs.set(state.total_songs ?? 10);
    this.endsAt = new Date(state.ends_at ?? Date.now());
    this.startTimer();

    this.wsService.connect(this.roomId);
    this.subscription = this.wsService.messages$.subscribe((event: WsEvent) => {
      if (event.event === 'song.started') {
        const d = event.data as SongStartedData;
        this.songId = d.song_id;
        this.songIndex.set(d.song_index);
        this.endsAt = new Date(d.ends_at);
        this.locked.set(false);
        this.answer.set('');
        this.feedback.set('none');
        this.submitError.set(null);
        this.restartTimer();
      } else if (event.event === 'song.locked') {
        this.locked.set(true);
        this.stopTimer();
      }
    });
  }

  ngOnDestroy(): void {
    this.stopTimer();
    this.subscription?.unsubscribe();
    this.wsService.disconnect();
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
      error: (err: { status?: number }) => {
        this.submitError.set(err.status === 409 ? 'Trop tard !' : "Erreur lors de l'envoi.");
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
