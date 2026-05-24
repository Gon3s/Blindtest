import { inject, Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';
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
  cover_url: string | null;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
}

export interface RoundFinishedData {
  room_id: string;
  round_leaderboard: RoundLeaderboardItem[];
}

export type WsEventData =
  | { event: 'room.state'; data: RoomStateData }
  | { event: 'room.closed'; data: { room_id: string } }
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

export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'error';

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private static readonly MAX_RECONNECT_ATTEMPTS = 5;
  private static readonly RECONNECT_DELAY_MS = 2000;

  private socket?: WebSocket;
  private readonly _messages = new Subject<WsEvent>();
  private readonly _connectionError = new Subject<string>();
  private readonly _connectionStatus = new BehaviorSubject<ConnectionStatus>('disconnected');
  private readonly errorService = inject(ErrorService);

  private _intentionalClose = false;
  private _reconnectAttempts = 0;
  private _reconnectTimeout?: ReturnType<typeof setTimeout>;
  private _roomId = '';

  readonly messages$ = this._messages.asObservable();
  readonly connectionError$ = this._connectionError.asObservable();
  readonly connectionStatus$ = this._connectionStatus.asObservable();

  connect(roomId: string): void {
    this._intentionalClose = false;
    this._reconnectAttempts = 0;
    this._roomId = roomId;
    this._closeSocket();
    this._doConnect(roomId);
  }

  disconnect(): void {
    this._intentionalClose = true;
    this._closeSocket();
    this._connectionStatus.next('disconnected');
  }

  ngOnDestroy(): void {
    this.disconnect();
  }

  private _doConnect(roomId: string): void {
    this._connectionStatus.next('connecting');
    this.socket = new WebSocket(`${environment.wsBaseUrl}/ws/rooms/${roomId}`);

    this.socket.onopen = () => {
      this._reconnectAttempts = 0;
      this._connectionStatus.next('connected');
    };

    this.socket.onmessage = ({ data }) => {
      try {
        this._messages.next(JSON.parse(data as string) as WsEvent);
      } catch {
        // ignore malformed JSON
      }
    };

    this.socket.onclose = (event) => {
      if (this._intentionalClose || event.wasClean) {
        this._connectionStatus.next('disconnected');
        return;
      }
      this._scheduleReconnect();
    };

    this.socket.onerror = () => {
      this._connectionError.next(this.errorService.wsDisconnected);
    };
  }

  private _scheduleReconnect(): void {
    if (this._reconnectAttempts >= WebSocketService.MAX_RECONNECT_ATTEMPTS) {
      this._connectionStatus.next('error');
      this._connectionError.next(this.errorService.wsDisconnected);
      return;
    }
    this._reconnectAttempts++;
    this._connectionStatus.next('reconnecting');
    this._reconnectTimeout = setTimeout(() => {
      this._doConnect(this._roomId);
    }, WebSocketService.RECONNECT_DELAY_MS);
  }

  private _closeSocket(): void {
    clearTimeout(this._reconnectTimeout);
    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.close();
      this.socket = undefined;
    }
  }
}
