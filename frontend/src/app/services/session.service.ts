import { Injectable } from '@angular/core';

export interface Session {
  roomCode: string;
  roomId: string;
  role: 'host' | 'player';
  participantId: string;
  hostToken?: string;
  nickname: string;
}

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly KEY = 'blindtest_session';

  saveSession(session: Session): void {
    localStorage.setItem(this.KEY, JSON.stringify(session));
  }

  loadSession(): Session | null {
    const raw = localStorage.getItem(this.KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as Session;
    } catch {
      return null;
    }
  }

  clearSession(): void {
    localStorage.removeItem(this.KEY);
  }
}
