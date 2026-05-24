import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CreateRoomResponse {
  room_id: string;
  code: string;
  host_id: string;
  host_token: string;
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

export interface AnswerSummaryItem {
  answer_id: string;
  participant_id: string;
  nickname: string;
  text: string;
  validation_status: string;
  title_found: boolean;
  artist_found: boolean;
}

export interface SongSummaryResponse {
  song_id: string;
  title: string;
  artist: string;
  total_answers: number;
  doubtful_count: number;
  answers: AnswerSummaryItem[];
}

export interface OverrideAnswerResponse {
  answer_id: string;
  title_found: boolean;
  artist_found: boolean;
  validation_status: string;
  score: number;
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

export interface RevealSongResponse {
  song_id: string;
  room_id: string;
  title: string;
  artist: string;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
  round_finished: boolean;
  round_leaderboard: RoundLeaderboardItem[];
}

export interface StartRoundResponse {
  round_id: string;
  room_id: string;
  song_count: number;
  theme: string;
  answer_mode?: 'both' | 'title_only' | 'artist_only';
}

export interface StartSongResponse {
  song_id: string;
  round_id: string;
  room_id: string;
  song_index: number;
  started_at: string;
  ends_at: string;
  preview_url: string | null;
}

export interface ParticipantInfo {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

export interface CurrentSongInfo {
  song_id: string;
  song_index: number;
  round_id: string;
  ends_at: string;
  preview_url: string | null;
  total_songs: number;
}

export interface RoomStateResponse {
  room_id: string;
  code: string;
  status: string;
  participants: ParticipantInfo[];
  current_song: CurrentSongInfo | null;
}

@Injectable({ providedIn: 'root' })
export class RoomService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiBaseUrl;

  createRoom(hostNickname: string): Observable<CreateRoomResponse> {
    return this.http.post<CreateRoomResponse>(`${this.apiUrl}/rooms`, {
      host_nickname: hostNickname,
    });
  }

  joinRoom(code: string, nickname: string): Observable<JoinRoomResponse> {
    return this.http.post<JoinRoomResponse>(`${this.apiUrl}/rooms/${code}/join`, { nickname });
  }

  startRound(
    roomId: string,
    theme = 'Général',
    hostToken = '',
    answerMode: 'both' | 'title_only' | 'artist_only' = 'both',
  ): Observable<StartRoundResponse> {
    return this.http.post<StartRoundResponse>(`${this.apiUrl}/rooms/${roomId}/rounds`, {
      theme,
      host_token: hostToken,
      answer_mode: answerMode,
    });
  }

  startSong(roundId: string, songIndex: number): Observable<StartSongResponse> {
    return this.http.post<StartSongResponse>(
      `${this.apiUrl}/rounds/${roundId}/songs/${songIndex}/start`,
      {},
    );
  }

  getSongSummary(songId: string, hostId: string): Observable<SongSummaryResponse> {
    return this.http.get<SongSummaryResponse>(`${this.apiUrl}/songs/${songId}/summary`, {
      params: { host_id: hostId },
    });
  }

  overrideAnswer(
    songId: string,
    answerId: string,
    hostId: string,
    titleAccepted: boolean,
    artistAccepted: boolean,
  ): Observable<OverrideAnswerResponse> {
    return this.http.patch<OverrideAnswerResponse>(
      `${this.apiUrl}/songs/${songId}/answers/${answerId}`,
      { host_id: hostId, title_accepted: titleAccepted, artist_accepted: artistAccepted },
    );
  }

  revealSong(songId: string, hostId: string): Observable<RevealSongResponse> {
    return this.http.post<RevealSongResponse>(`${this.apiUrl}/songs/${songId}/reveal`, {
      host_id: hostId,
    });
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

  restartRound(
    roomId: string,
    theme: string,
    answerMode: 'both' | 'title_only' | 'artist_only' = 'both',
  ): Observable<StartRoundResponse> {
    return this.http.post<StartRoundResponse>(`${this.apiUrl}/rooms/${roomId}/restart`, {
      theme,
      answer_mode: answerMode,
    });
  }

  getRoomState(code: string): Observable<RoomStateResponse> {
    return this.http.get<RoomStateResponse>(`${this.apiUrl}/rooms/${code}`);
  }
}
