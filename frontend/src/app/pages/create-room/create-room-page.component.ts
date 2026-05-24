import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ErrorService } from '../../services/error.service';
import { RoomService } from '../../services/room.service';
import { SessionService } from '../../services/session.service';

@Component({
  selector: 'app-create-room-page',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './create-room-page.component.html',
  styleUrl: './create-room-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateRoomPageComponent {
  nickname = '';
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  private readonly roomService = inject(RoomService);
  private readonly router = inject(Router);
  private readonly sessionService = inject(SessionService);
  private readonly errorService = inject(ErrorService);

  submit(): void {
    const name = this.nickname.trim();
    if (!name) return;
    this.loading.set(true);
    this.error.set(null);
    this.roomService.createRoom(name).subscribe({
      next: (res) => {
        this.sessionService.saveSession({
          roomCode: res.code,
          roomId: res.room_id,
          role: 'host',
          participantId: res.host_id,
          hostToken: res.host_token,
          nickname: name,
        });
        this.router.navigate(['/lobby', res.code], {
          state: { room_id: res.room_id, host_id: res.host_id, role: 'host', nickname: name },
        });
      },
      error: (err: { error?: { code?: string; message?: string; detail?: string } }) => {
        this.error.set(this.errorService.fromHttpError(err));
        this.loading.set(false);
      },
    });
  }
}
