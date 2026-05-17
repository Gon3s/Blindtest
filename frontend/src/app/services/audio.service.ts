import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AudioService {
  private audio: HTMLAudioElement | null = null;

  play(url: string): void {
    this.stop();
    this.audio = new Audio(url);
    this.audio.play().catch(() => undefined);
  }

  stop(): void {
    if (this.audio) {
      this.audio.pause();
      this.audio.src = '';
      this.audio = null;
    }
  }
}
