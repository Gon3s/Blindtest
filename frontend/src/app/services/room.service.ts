import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CreateRoomResponse {
  room_id: string;
  code: string;
  host_id: string;
}

export interface JoinRoomResponse {
  room_id: string;
  participant_id: string;
}

export interface SubmitAnswerResponse {
  answer_id: string;
  submitted_at: string;
  validation_status: string;
  title_found: boolean;
  artist_found: boolean;
}

@Injectable({ providedIn: 'root' })
export class RoomService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8000';

  createRoom(hostNickname: string): Observable<CreateRoomResponse> {
    return this.http.post<CreateRoomResponse>(`${this.apiUrl}/rooms`, {
      host_nickname: hostNickname,
    });
  }

  joinRoom(code: string, nickname: string): Observable<JoinRoomResponse> {
    return this.http.post<JoinRoomResponse>(`${this.apiUrl}/rooms/${code}/join`, { nickname });
  }

  submitAnswer(
    songId: string,
    participantId: string,
    text: string,
  ): Observable<SubmitAnswerResponse> {
    return this.http.post<SubmitAnswerResponse>(`${this.apiUrl}/songs/${songId}/answers`, {
      participant_id: participantId,
      text,
    });
  }
}
