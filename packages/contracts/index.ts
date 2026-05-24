/**
 * Shared API & WebSocket contracts for Blindtest MVP.
 *
 * Source of truth: backend Pydantic schemas in backend/src/api/schemas/.
 * Do NOT add fields here that are not in the backend schemas.
 * See docs/api-contracts.md for the full contract reference.
 */

// ── HTTP request bodies ───────────────────────────────────────────────────────

export interface CreateRoomRequest {
  host_nickname: string;
}

export interface JoinRoomRequest {
  nickname: string;
}

export interface StartRoundRequest {
  theme: string;
}

export interface SubmitAnswerRequest {
  participant_id: string;
  text: string;
}

export interface RevealSongRequest {
  host_id: string;
}

export interface OverrideAnswerRequest {
  host_id: string;
  title_accepted: boolean;
  artist_accepted: boolean;
}

// ── HTTP response bodies ──────────────────────────────────────────────────────

export interface CreateRoomResponse {
  room_id: string;
  code: string;
  host_id: string;
}

export interface JoinRoomResponse {
  room_id: string;
  participant_id: string;
}

export interface StartRoundResponse {
  round_id: string;
  room_id: string;
  song_count: number;
  theme: string;
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

export interface SubmitAnswerResponse {
  answer_id: string;
  submitted_at: string;
  validation_status: ValidationStatus;
  title_found: boolean;
  artist_found: boolean;
}

export interface AnswerSummaryItem {
  answer_id: string;
  participant_id: string;
  nickname: string;
  text: string;
  validation_status: ValidationStatus;
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
  validation_status: ValidationStatus;
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
  cover_url: string | null;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
  round_finished: boolean;
  round_leaderboard: RoundLeaderboardItem[];
}

// ── WebSocket event payloads ──────────────────────────────────────────────────

export type ValidationStatus = 'not_found' | 'found' | 'doubtful';

export interface Participant {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

export interface WsRoomStateData {
  room_id: string;
  participants: Participant[];
}

export interface WsParticipantJoinedData {
  participant_id: string;
  nickname: string;
  is_host: boolean;
}

export interface WsRoundStartedData {
  round_id: string;
  theme: string;
  song_count: number;
}

export interface WsSongStartedData {
  song_id: string;
  song_index: number;
  round_id: string;
  started_at: string;
  ends_at: string;
  preview_url: string | null;
}

export interface WsSongLockedData {
  song_id: string;
  round_id: string;
}

export interface WsSongRevealedData {
  song_id: string;
  title: string;
  artist: string;
  cover_url: string | null;
  player_results: PlayerRevealItem[];
  mini_leaderboard: MiniLeaderboardItem[];
}

export interface WsRoundFinishedData {
  room_id: string;
  round_leaderboard: RoundLeaderboardItem[];
}

export type WsEvent =
  | { event: 'room.state'; data: WsRoomStateData }
  | { event: 'participant.joined'; data: WsParticipantJoinedData }
  | { event: 'round.started'; data: WsRoundStartedData }
  | { event: 'song.started'; data: WsSongStartedData }
  | { event: 'song.locked'; data: WsSongLockedData }
  | { event: 'song.revealed'; data: WsSongRevealedData }
  | { event: 'round.finished'; data: WsRoundFinishedData };
