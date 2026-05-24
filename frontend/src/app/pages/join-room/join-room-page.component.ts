import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ErrorService } from '../../services/error.service';
import { RoomService } from '../../services/room.service';
import { SessionService } from '../../services/session.service';

@Component({
  selector: 'app-join-room-page',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './join-room-page.component.html',
  styleUrl: './join-room-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JoinRoomPageComponent {
  code = '';
  nickname = '';
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  private readonly roomService = inject(RoomService);
  private readonly router = inject(Router);
  private readonly sessionService = inject(SessionService);
  private readonly errorService = inject(ErrorService);

  submit(): void {
    const code = this.code.trim().toUpperCase();
    const nickname = this.nickname.trim();
    if (!code || !nickname) return;
    this.loading.set(true);
    this.error.set(null);
    this.roomService.joinRoom(code, nickname).subscribe({
      next: (res) => {
        this.sessionService.saveSession({
          roomCode: code,
          roomId: res.room_id,
          role: 'player',
          participantId: res.participant_id,
          nickname,
        });
        this.router.navigate(['/lobby', code], {
          state: {
            room_id: res.room_id,
            participant_id: res.participant_id,
            role: 'player',
            nickname,
          },
        });
      },
      error: (err: { error?: { code?: string; message?: string; detail?: string } }) => {
        this.error.set(this.errorService.fromHttpError(err));
        this.loading.set(false);
      },
    });
  }
}
