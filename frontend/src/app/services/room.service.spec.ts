import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { OverrideAnswerResponse, RevealSongResponse, RoomService, SongSummaryResponse, StartSongResponse } from './room.service';
import { environment } from '../../environments/environment';

describe('RoomService', () => {
  let service: RoomService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RoomService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should create a room via POST /rooms', () => {
    const mockResponse = { room_id: 'uuid-room', code: 'ABC123', host_id: 'uuid-host' };

    service.createRoom('Alice').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/rooms`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ host_nickname: 'Alice' });
    req.flush(mockResponse);
  });

  it('should join a room via POST /rooms/:code/join', () => {
    const mockResponse = { room_id: 'uuid-room', participant_id: 'uuid-participant' };

    service.joinRoom('ABC123', 'Bob').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/rooms/ABC123/join`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ nickname: 'Bob' });
    req.flush(mockResponse);
  });

  it('should submit an answer via POST /songs/:id/answers', () => {
    const mockResponse = {
      answer_id: 'uuid-answer',
      submitted_at: '2026-01-01T12:00:00.000Z',
      validation_status: 'not_found',
      title_found: false,
      artist_found: false,
    };

    service.submitAnswer('song-uuid', 'participant-uuid', 'Daft Punk').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/songs/song-uuid/answers`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ participant_id: 'participant-uuid', text: 'Daft Punk' });
    req.flush(mockResponse);
  });

  it('should fetch full song summary via GET /songs/:id/summary', () => {
    const mockResponse: SongSummaryResponse = {
      song_id: 'song-uuid',
      title: 'Get Lucky',
      artist: 'Daft Punk',
      total_answers: 2,
      doubtful_count: 1,
      answers: [
        {
          answer_id: 'ans-1',
          participant_id: 'p1',
          nickname: 'Alice',
          text: 'get lucky',
          validation_status: 'found',
          title_found: true,
          artist_found: true,
        },
      ],
    };

    service.getSongSummary('song-uuid', 'host-uuid').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/songs/song-uuid/summary?host_id=host-uuid`,
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should override an answer via PATCH /songs/:id/answers/:answerId', () => {
    const mockResponse: OverrideAnswerResponse = {
      answer_id: 'ans-uuid',
      title_found: true,
      artist_found: true,
      validation_status: 'found',
      score: 2,
    };

    service
      .overrideAnswer('song-uuid', 'ans-uuid', 'host-uuid', true, true)
      .subscribe(res => {
        expect(res).toEqual(mockResponse);
      });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/songs/song-uuid/answers/ans-uuid`,
    );
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({
      host_id: 'host-uuid',
      title_accepted: true,
      artist_accepted: true,
    });
    req.flush(mockResponse);
  });

  it('should reveal a song via POST /songs/:id/reveal with round_finished and round_leaderboard', () => {
    const mockResponse: RevealSongResponse = {
      song_id: 'song-uuid',
      room_id: 'room-uuid',
      title: 'Get Lucky',
      artist: 'Daft Punk',
      player_results: [
        {
          participant_id: 'p1',
          nickname: 'Alice',
          answer: 'get lucky',
          title_found: true,
          artist_found: true,
          score: 200,
        },
      ],
      mini_leaderboard: [
        { rank: 1, participant_id: 'p1', nickname: 'Alice', total_points: 200 },
      ],
      round_finished: true,
      round_leaderboard: [
        { rank: 1, participant_id: 'p1', nickname: 'Alice', round_points: 200 },
      ],
    };

    service.revealSong('song-uuid', 'host-uuid').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/songs/song-uuid/reveal`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ host_id: 'host-uuid' });
    req.flush(mockResponse);
  });

  it('should start a song via POST including preview_url', () => {
    const mockResponse: StartSongResponse = {
      song_id: 'song-uuid',
      round_id: 'round-uuid',
      room_id: 'room-uuid',
      song_index: 0,
      started_at: '2026-01-01T12:00:00Z',
      ends_at: '2026-01-01T12:00:30Z',
      preview_url: 'https://cdn.deezer.com/preview.mp3',
    };

    service.startSong('round-uuid', 0).subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/rounds/round-uuid/songs/0/start`,
    );
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });

  it('should handle null preview_url in StartSongResponse', () => {
    const mockResponse: StartSongResponse = {
      song_id: 'song-uuid',
      round_id: 'round-uuid',
      room_id: 'room-uuid',
      song_index: 1,
      started_at: '2026-01-01T12:00:00Z',
      ends_at: '2026-01-01T12:00:30Z',
      preview_url: null,
    };

    service.startSong('round-uuid', 1).subscribe(res => {
      expect(res.preview_url).toBeNull();
    });

    const req = httpMock.expectOne(
      `${environment.apiBaseUrl}/rounds/round-uuid/songs/1/start`,
    );
    req.flush(mockResponse);
  });
});
