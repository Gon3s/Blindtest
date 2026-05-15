import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { RoomService } from '../../services/room.service';

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

  submit(): void {
    const name = this.nickname.trim();
    if (!name) return;
    this.loading.set(true);
    this.error.set(null);
    this.roomService.createRoom(name).subscribe({
      next: res => {
        this.router.navigate(['/lobby', res.code], {
          state: { room_id: res.room_id, host_id: res.host_id, role: 'host' },
        });
      },
      error: (err: { error?: { detail?: string } }) => {
        this.error.set(err?.error?.detail ?? 'Erreur lors de la création de la salle');
        this.loading.set(false);
      },
    });
  }
}
