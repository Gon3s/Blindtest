import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { RoomService } from './room.service';

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

    const req = httpMock.expectOne('http://localhost:8000/rooms');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ host_nickname: 'Alice' });
    req.flush(mockResponse);
  });

  it('should join a room via POST /rooms/:code/join', () => {
    const mockResponse = { room_id: 'uuid-room', participant_id: 'uuid-participant' };

    service.joinRoom('ABC123', 'Bob').subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne('http://localhost:8000/rooms/ABC123/join');
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

    const req = httpMock.expectOne('http://localhost:8000/songs/song-uuid/answers');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ participant_id: 'participant-uuid', text: 'Daft Punk' });
    req.flush(mockResponse);
  });
});
