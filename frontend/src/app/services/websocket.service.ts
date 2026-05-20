import { inject, Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { ErrorService } from './error.service';

export interface Participant {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

export interface PlayerRevealItem {
  participant_id: string;
  nickname: string;
  answer: string;
  title_found: boolean;
  artist_found: boolean;
  score: number;
}

export interface MiniLeaderboardItem {
  rank: number;
  participant_id: string;
  nickname: string;
  total_points: number;
}

export interface RoundLeaderboardItem {
  rank: number;
  participant_id: string;
  nickname: string;
  round_points: number;
}

export interface RoomStateData {
  room_id: string;
  participants: Participant[];
}

export interface ParticipantJoinedData {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

export interface RoundStartedData {
  round_id: string;
  theme: string;
  song_count: number;
}

export interface SongStartedData {
  song_id: string;
  song_index: number;
  round_id: string;
  started_at: string;
  ends_at: string;
  preview_url: string | null;
}

export interface SongLockedData {
  song_id: string;
  round_id: string;
}

export interface SongRevealedData {
  song_id: string;
  title: string;
  artist: string;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
}

export interface RoundFinishedData {
  room_id: string;
  round_leaderboard: RoundLeaderboardItem[];
}

export type WsEventData =
  | { event: 'room.state'; data: RoomStateData }
  | { event: 'participant.joined'; data: ParticipantJoinedData }
  | { event: 'round.started'; data: RoundStartedData }
  | { event: 'song.started'; data: SongStartedData }
  | { event: 'song.locked'; data: SongLockedData }
  | { event: 'song.revealed'; data: SongRevealedData }
  | { event: 'round.finished'; data: RoundFinishedData };

export interface WsEvent {
  event: string;
  data: unknown;
}

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private socket?: WebSocket;
  private readonly _messages = new Subject<WsEvent>();
  private readonly _connectionError = new Subject<string>();
  private readonly errorService = inject(ErrorService);

  readonly messages$ = this._messages.asObservable();
  readonly connectionError$ = this._connectionError.asObservable();

  connect(roomId: string): void {
    this.disconnect();
    this.socket = new WebSocket(`${environment.wsBaseUrl}/ws/rooms/${roomId}`);
    this.socket.onmessage = ({ data }) => {
      this._messages.next(JSON.parse(data as string) as WsEvent);
    };
    this.socket.onclose = (event) => {
      if (!event.wasClean) {
        this._connectionError.next(this.errorService.wsDisconnected);
      }
    };
    this.socket.onerror = () => {
      this._connectionError.next(this.errorService.wsDisconnected);
    };
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = undefined;
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
