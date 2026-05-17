import { Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface WsEvent {
  event: string;
  data: unknown;
}

export interface Participant {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

@Injectable({ providedIn: 'root' })
export class WebSocketService implements OnDestroy {
  private socket?: WebSocket;
  private readonly _messages = new Subject<WsEvent>();
  readonly messages$ = this._messages.asObservable();

  connect(roomId: string): void {
    this.disconnect();
    this.socket = new WebSocket(`${environment.wsBaseUrl}/ws/rooms/${roomId}`);
    this.socket.onmessage = ({ data }) => {
      this._messages.next(JSON.parse(data as string) as WsEvent);
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
