import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { of } from 'rxjs';
import { PlayPageComponent } from './play-page.component';
import { ConnectionStatus, WebSocketService, WsEvent } from '../../services/websocket.service';
import { SessionService } from '../../services/session.service';
import { AudioService } from '../../services/audio.service';
import {
  MiniLeaderboardItem,
  PlayerRevealItem,
  RevealSongResponse,
  RoundLeaderboardItem,
  RoomService,
  SongSummaryResponse,
  StartRoundResponse,
  SubmitAnswerResponse,
} from '../../services/room.service';

const BASE_NOW = new Date('2026-01-01T12:00:00.000Z');
const BASE_ENDS = new Date('2026-01-01T12:00:30.000Z'); // 30s later

function createWsMock() {
  const msgs = new Subject<WsEvent>();
  const connErrors = new Subject<string>();
  const connStatus = new BehaviorSubject<ConnectionStatus>('connected');
  const service = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    messages$: msgs.asObservable() as Observable<WsEvent>,
    connectionError$: connErrors.asObservable() as Observable<string>,
    connectionStatus$: connStatus.asObservable() as Observable<ConnectionStatus>,
  };
  return { service, msgs, connErrors, connStatus };
}

const noopRoomService = { submitAnswer: vi.fn() };

function createRoomServiceMock() {
  const subject = new Subject<SubmitAnswerResponse>();
  const service = { submitAnswer: vi.fn().mockReturnValue(subject.asObservable()) };
  return { service, subject };
}

interface SetupOpts {
  song_index?: number;
  total_songs?: number;
  ends_at?: string;
}

async function configureTestBed(opts: SetupOpts = {}) {
  const { service, msgs, connErrors } = createWsMock();

  history.replaceState(
    {
      room_id: 'room-uuid',
      nickname: 'Alice',
      song_index: opts.song_index ?? 0,
      total_songs: opts.total_songs ?? 10,
      ends_at: opts.ends_at ?? BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: {
          paramMap: of({ get: (k: string) => (k === 'code' ? 'ABC123' : null) }),
        },
      },
      { provide: WebSocketService, useValue: service },
      { provide: RoomService, useValue: noopRoomService },
    ],
  }).compileComponents();

  return { service, msgs, connErrors };
}

function mountFixture(): ComponentFixture<PlayPageComponent> {
  const fixture = TestBed.createComponent(PlayPageComponent);
  fixture.detectChanges();
  return fixture;
}

// ─── Timer ────────────────────────────────────────────────────────────────────

describe('PlayPageComponent — timer', () => {
  afterEach(() => {
    history.replaceState(null, '');
    vi.useRealTimers();
    TestBed.resetTestingModule();
  });

  it('should display the initial countdown in seconds', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(BASE_NOW);
    await configureTestBed({ ends_at: BASE_ENDS.toISOString() });
    const fixture = mountFixture();
    const el = fixture.nativeElement as HTMLElement;
    const timer = el.querySelector('[data-testid="timer"]');
    expect(timer?.textContent?.trim()).toBe('30');
  });

  it('should decrement by 1 after each second', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(BASE_NOW);
    await configureTestBed({ ends_at: BASE_ENDS.toISOString() });
    const fixture = mountFixture();
    const el = fixture.nativeElement as HTMLElement;

    vi.advanceTimersByTime(1000);
    fixture.detectChanges();

    expect(el.querySelector('[data-testid="timer"]')?.textContent?.trim()).toBe('29');
  });

  it('should not go below 0', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(BASE_NOW);
    await configureTestBed({ ends_at: BASE_ENDS.toISOString() });
    const fixture = mountFixture();
    const el = fixture.nativeElement as HTMLElement;

    vi.advanceTimersByTime(60_000);
    fixture.detectChanges();

    expect(Number(el.querySelector('[data-testid="timer"]')?.textContent?.trim())).toBe(0);
  });

  it('should display 0 when song.locked event is received before interval fires', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(BASE_NOW);
    const { msgs } = await configureTestBed({ ends_at: BASE_ENDS.toISOString() });
    const fixture = mountFixture();
    const el = fixture.nativeElement as HTMLElement;

    // Advance almost to the end but not past it (interval hasn't fired yet for the last tick)
    vi.advanceTimersByTime(29_800);
    fixture.detectChanges();

    // song.locked arrives while ~200ms remain — Math.ceil(0.2) would show 1 without the fix
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();

    expect(Number(el.querySelector('[data-testid="timer"]')?.textContent?.trim())).toBe(0);
  });
});

// ─── Answer field ─────────────────────────────────────────────────────────────

describe('PlayPageComponent — answer field', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should show an active answer input while playing', async () => {
    await configureTestBed();
    const fixture = mountFixture();
    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '[data-testid="answer-input"]',
    );
    expect(input).not.toBeNull();
    expect(input?.disabled).toBe(false);
  });

  it('should hide the answer input after song.locked event', async () => {
    const { msgs } = await configureTestBed();
    const fixture = mountFixture();

    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();

    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '[data-testid="answer-input"]',
    );
    expect(input).toBeNull();
  });
});

// ─── song.started event ───────────────────────────────────────────────────────

describe('PlayPageComponent — song.started', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should display song number and total on init', async () => {
    await configureTestBed({ song_index: 0, total_songs: 10 });
    const fixture = mountFixture();
    const songNum = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="song-number"]',
    );
    expect(songNum?.textContent).toContain('1');
    expect(songNum?.textContent).toContain('10');
  });

  it('should update song number on song.started event', async () => {
    const { msgs } = await configureTestBed({ song_index: 0, total_songs: 10 });
    const fixture = mountFixture();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 2,
        round_id: 'round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
      },
    });
    fixture.detectChanges();

    const songNum = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="song-number"]',
    );
    expect(songNum?.textContent).toContain('3'); // index 2 → display 3
  });

  it('should re-enable input on song.started after a lock', async () => {
    const { msgs } = await configureTestBed({ song_index: 0 });
    const fixture = mountFixture();

    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid-2',
        song_index: 1,
        round_id: 'round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
      },
    });
    fixture.detectChanges();

    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '[data-testid="answer-input"]',
    );
    expect(input?.disabled).toBe(false);
  });
});

// ─── Lobby navigation ─────────────────────────────────────────────────────────

describe('PlayPageComponent — WebSocket connection', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should connect to WebSocket with room_id from state', async () => {
    const { service } = await configureTestBed();
    mountFixture();
    expect(service.connect).toHaveBeenCalledWith('room-uuid');
  });

  it('should set connectionError signal on WS disconnect', async () => {
    const { connErrors } = await configureTestBed();
    const fixture = mountFixture();

    connErrors.next('Connexion perdue. Actualise la page pour rejoindre.');
    fixture.detectChanges();

    expect(fixture.componentInstance.connectionError()).toBe(
      'Connexion perdue. Actualise la page pour rejoindre.',
    );
  });

  it('should redirect to / if no room_id and no code in state', async () => {
    history.replaceState({}, '');
    const { service, msgs } = createWsMock();

    await TestBed.configureTestingModule({
      imports: [PlayPageComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => null } },
            paramMap: of({ get: () => null }),
          },
        },
        { provide: WebSocketService, useValue: service },
        { provide: RoomService, useValue: noopRoomService },
      ],
    }).compileComponents();

    mountFixture();
    const router = TestBed.inject(Router);
    expect(service.connect).not.toHaveBeenCalled();
    expect(router.url).toBe('/');

    void msgs;
  });

  it('should redirect to /lobby/:code if no room_id but code present in route', async () => {
    history.replaceState({}, '');
    const { service, msgs } = createWsMock();

    await TestBed.configureTestingModule({
      imports: [PlayPageComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: (k: string) => (k === 'code' ? 'ABC123' : null) } },
            paramMap: of({ get: (k: string) => (k === 'code' ? 'ABC123' : null) }),
          },
        },
        { provide: WebSocketService, useValue: service },
        { provide: RoomService, useValue: noopRoomService },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(PlayPageComponent);
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');
    fixture.detectChanges();

    expect(service.connect).not.toHaveBeenCalled();
    expect(navigateSpy).toHaveBeenCalledWith(['/lobby', 'ABC123']);

    void msgs;
  });
});

// ─── Submit answer ─────────────────────────────────────────────────────────────

async function configureTestBedWithService(opts: SetupOpts = {}) {
  const { service: wsService, msgs } = createWsMock();
  const { service: roomService, subject: submitSubject } = createRoomServiceMock();

  history.replaceState(
    {
      room_id: 'room-uuid',
      participant_id: 'participant-uuid',
      nickname: 'Alice',
      song_id: 'song-uuid',
      song_index: opts.song_index ?? 0,
      total_songs: opts.total_songs ?? 10,
      ends_at: opts.ends_at ?? BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: {
          paramMap: of({ get: (k: string) => (k === 'code' ? 'ABC123' : null) }),
        },
      },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  return { wsService, msgs, roomService, submitSubject };
}

describe('PlayPageComponent — submit answer', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should show a submit button', async () => {
    await configureTestBedWithService();
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="submit-btn"]'),
    ).not.toBeNull();
  });

  it('should call submitAnswer with correct args on button click', async () => {
    const { roomService } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Daft Punk');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    expect(roomService.submitAnswer).toHaveBeenCalledWith(
      'song-uuid',
      'participant-uuid',
      'Daft Punk',
    );
  });
});

// ─── Feedback ─────────────────────────────────────────────────────────────────

describe('PlayPageComponent — feedback', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should announce feedback to screen readers via role="status"', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Daft Punk');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'not_found',
      title_found: false,
      artist_found: false,
    });
    fixture.detectChanges();

    const feedback = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="feedback"]',
    );
    expect(feedback?.getAttribute('role')).toBe('status');
  });

  it('should show no feedback initially', async () => {
    await configureTestBedWithService();
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback"]'),
    ).toBeNull();
  });

  it('should show "Pas encore !" when nothing found', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Wrong');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'not_found',
      title_found: false,
      artist_found: false,
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback-not-found"]'),
    ).not.toBeNull();
  });

  it('should show "Titre trouvé !" when title_found', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Get Lucky');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'partial',
      title_found: true,
      artist_found: false,
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback-title-found"]'),
    ).not.toBeNull();
  });

  it('should show "Artiste trouvé !" when artist_found', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Daft Punk');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'partial',
      title_found: false,
      artist_found: true,
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback-artist-found"]'),
    ).not.toBeNull();
  });

  it('should show "Bravo ! Tout trouvé !" when both found', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Get Lucky Daft Punk');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'found',
      title_found: true,
      artist_found: true,
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback-both-found"]'),
    ).not.toBeNull();
  });

  it('should clear feedback on song.started event', async () => {
    const { msgs, submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Wrong');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.next({
      answer_id: 'uuid',
      submitted_at: 'ts',
      validation_status: 'not_found',
      title_found: false,
      artist_found: false,
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback"]'),
    ).not.toBeNull();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid-2',
        song_index: 1,
        round_id: 'round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
      },
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="feedback"]'),
    ).toBeNull();
  });
});

// ─── Submit errors ─────────────────────────────────────────────────────────────

describe('PlayPageComponent — submit errors', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should not call service and show error for empty answer', async () => {
    const { roomService } = await configureTestBedWithService();
    const fixture = mountFixture();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();
    fixture.detectChanges();

    expect(roomService.submitAnswer).not.toHaveBeenCalled();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="submit-error"]'),
    ).not.toBeNull();
  });

  it('should show "Trop tard !" for 409 response', async () => {
    const { submitSubject } = await configureTestBedWithService();
    const fixture = mountFixture();
    fixture.componentInstance.answer.set('Daft Punk');
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="submit-btn"]')
      ?.click();

    submitSubject.error({
      status: 409,
      error: { code: 'answer_too_late', message: 'Trop tard ! La chanson est terminée.' },
    });
    fixture.detectChanges();

    const errorEl = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="submit-error"]',
    );
    expect(errorEl?.textContent).toContain('Trop tard');
  });
});

// ─── Reveal (T-033) ───────────────────────────────────────────────────────────

const mockRevealEvent: WsEvent = {
  event: 'song.revealed',
  data: {
    song_id: 'song-uuid',
    title: 'Get Lucky',
    artist: 'Daft Punk',
    player_results: [
      {
        participant_id: 'p1',
        nickname: 'Alice',
        answer: 'get lucky daft punk',
        title_found: true,
        artist_found: true,
        score: 2,
      },
      {
        participant_id: 'p2',
        nickname: 'Bob',
        answer: 'get luckky',
        title_found: false,
        artist_found: false,
        score: 0,
      },
    ] as PlayerRevealItem[],
    mini_leaderboard: [
      { rank: 1, participant_id: 'p1', nickname: 'Alice', total_points: 5 },
      { rank: 2, participant_id: 'p2', nickname: 'Bob', total_points: 2 },
    ] as MiniLeaderboardItem[],
  } as RevealSongResponse,
};

async function configureRevealTestBed(opts: { isHost?: boolean } = {}) {
  const { service: wsService, msgs } = createWsMock();
  const summarySubject = new Subject<SongSummaryResponse>();
  const revealApiSubject = new Subject<RevealSongResponse>();
  const roomService = {
    submitAnswer: vi.fn(),
    getSongSummary: vi.fn().mockReturnValue(summarySubject.asObservable()),
    overrideAnswer: vi.fn(),
    startSong: vi.fn(),
    revealSong: vi.fn().mockReturnValue(revealApiSubject.asObservable()),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      song_id: 'song-uuid',
      participant_id: 'p1',
      is_host: opts.isHost ?? false,
      host_id: 'host-uuid',
      round_id: 'round-uuid',
      song_index: 0,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => null }) } },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  return { wsService, msgs, roomService, summarySubject, revealApiSubject };
}

describe('PlayPageComponent — reveal (T-033)', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should show reveal section after song.revealed event (player)', async () => {
    const { msgs } = await configureRevealTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockRevealEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="reveal-section"]'),
    ).not.toBeNull();
  });

  it('should display correct title and artist in reveal section', async () => {
    const { msgs } = await configureRevealTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockRevealEvent);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[data-testid="revealed-title"]')?.textContent?.trim()).toBe(
      'Get Lucky',
    );
    expect(el.querySelector('[data-testid="revealed-artist"]')?.textContent?.trim()).toBe(
      'Daft Punk',
    );
  });

  it('should display current player score in reveal section', async () => {
    const { msgs } = await configureRevealTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockRevealEvent);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[data-testid="my-score"]')?.textContent).toContain('2');
  });

  it('should display mini leaderboard with all entries', async () => {
    const { msgs } = await configureRevealTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockRevealEvent);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const rows = el.querySelectorAll('[data-testid="leaderboard-row"]');
    expect(rows.length).toBe(2);
    expect(rows[0].querySelector('[data-testid="leaderboard-nickname"]')?.textContent?.trim()).toBe(
      'Alice',
    );
    expect(rows[0].querySelector('[data-testid="leaderboard-points"]')?.textContent).toContain('5');
    expect(rows[1].querySelector('[data-testid="leaderboard-nickname"]')?.textContent?.trim()).toBe(
      'Bob',
    );
  });

  it('should show next-song CTA for host after song.revealed', async () => {
    const { msgs } = await configureRevealTestBed({ isHost: true });
    const fixture = mountFixture();

    msgs.next(mockRevealEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="next-song-btn"]'),
    ).not.toBeNull();
  });
});

// ─── Round Leaderboard (T-035) ────────────────────────────────────────────────

const mockLastRevealEvent: WsEvent = {
  event: 'song.revealed',
  data: {
    song_id: 'song-10',
    title: 'Last Song',
    artist: 'Artist',
    player_results: [] as PlayerRevealItem[],
    mini_leaderboard: [
      { rank: 1, participant_id: 'p1', nickname: 'Alice', total_points: 50 },
      { rank: 2, participant_id: 'p2', nickname: 'Bob', total_points: 35 },
      { rank: 3, participant_id: 'p3', nickname: 'Carol', total_points: 20 },
    ] as MiniLeaderboardItem[],
  },
};

const mockRoundFinishedEvent: WsEvent = {
  event: 'round.finished',
  data: {
    room_id: 'room-uuid',
    round_leaderboard: [
      { rank: 1, participant_id: 'p1', nickname: 'Alice', round_points: 15 },
      { rank: 2, participant_id: 'p2', nickname: 'Bob', round_points: 10 },
      { rank: 3, participant_id: 'p3', nickname: 'Carol', round_points: 5 },
    ] as RoundLeaderboardItem[],
  },
};

const mockRoundFinishedTieEvent: WsEvent = {
  event: 'round.finished',
  data: {
    room_id: 'room-uuid',
    round_leaderboard: [
      { rank: 1, participant_id: 'p1', nickname: 'Alice', round_points: 15 },
      { rank: 1, participant_id: 'p2', nickname: 'Bob', round_points: 15 },
      { rank: 3, participant_id: 'p3', nickname: 'Carol', round_points: 5 },
    ] as RoundLeaderboardItem[],
  },
};

async function configureRoundTestBed(opts: { isHost?: boolean } = {}) {
  const { service: wsService, msgs } = createWsMock();
  const roomService = {
    submitAnswer: vi.fn(),
    getSongSummary: vi.fn(),
    overrideAnswer: vi.fn(),
    startSong: vi.fn(),
    revealSong: vi.fn(),
    startRound: vi.fn(),
    restartRound: vi.fn().mockReturnValue(new Subject<StartRoundResponse>().asObservable()),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      song_id: 'song-uuid',
      participant_id: 'p1',
      is_host: opts.isHost ?? false,
      host_id: 'host-uuid',
      round_id: 'round-uuid',
      song_index: 9,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => null }) } },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  return { wsService, msgs, roomService };
}

describe('PlayPageComponent — round leaderboard (T-035)', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should show round leaderboard section after round.finished event', async () => {
    const { msgs } = await configureRoundTestBed();
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '[data-testid="round-leaderboard-section"]',
      ),
    ).not.toBeNull();
  });

  it('should display players in rank order (rank 1 first)', async () => {
    const { msgs } = await configureRoundTestBed();
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="round-leaderboard-row"]',
    );
    expect(rows.length).toBe(3);
    expect(
      rows[0].querySelector('[data-testid="round-leaderboard-nickname"]')?.textContent?.trim(),
    ).toBe('Alice');
    expect(
      rows[1].querySelector('[data-testid="round-leaderboard-nickname"]')?.textContent?.trim(),
    ).toBe('Bob');
    expect(
      rows[2].querySelector('[data-testid="round-leaderboard-nickname"]')?.textContent?.trim(),
    ).toBe('Carol');
  });

  it('should display same rank number for tied players', async () => {
    const { msgs } = await configureRoundTestBed();
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedTieEvent);
    fixture.detectChanges();

    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="round-leaderboard-row"]',
    );
    expect(
      rows[0].querySelector('[data-testid="round-leaderboard-rank"]')?.textContent?.trim(),
    ).toBe('1');
    expect(
      rows[1].querySelector('[data-testid="round-leaderboard-rank"]')?.textContent?.trim(),
    ).toBe('1');
    expect(
      rows[2].querySelector('[data-testid="round-leaderboard-rank"]')?.textContent?.trim(),
    ).toBe('3');
  });

  it('should show round_points (score manche) for each player', async () => {
    const { msgs } = await configureRoundTestBed();
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="round-leaderboard-row"]',
    );
    expect(
      rows[0].querySelector('[data-testid="round-leaderboard-round-points"]')?.textContent,
    ).toContain('15');
    expect(
      rows[1].querySelector('[data-testid="round-leaderboard-round-points"]')?.textContent,
    ).toContain('10');
    expect(
      rows[2].querySelector('[data-testid="round-leaderboard-round-points"]')?.textContent,
    ).toContain('5');
  });

  it('should show total_points (score global) for each player from last mini_leaderboard', async () => {
    const { msgs } = await configureRoundTestBed();
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="round-leaderboard-row"]',
    );
    expect(
      rows[0].querySelector('[data-testid="round-leaderboard-total-points"]')?.textContent,
    ).toContain('50');
    expect(
      rows[1].querySelector('[data-testid="round-leaderboard-total-points"]')?.textContent,
    ).toContain('35');
    expect(
      rows[2].querySelector('[data-testid="round-leaderboard-total-points"]')?.textContent,
    ).toContain('20');
  });

  it('should show "Nouvelle manche" CTA for host', async () => {
    const { msgs } = await configureRoundTestBed({ isHost: true });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="new-round-btn"]'),
    ).not.toBeNull();
  });

  it('should NOT show "Nouvelle manche" CTA for player', async () => {
    const { msgs } = await configureRoundTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="new-round-btn"]'),
    ).toBeNull();
  });
});

// ─── New Round (T-037) ───────────────────────────────────────────────────────

async function configureNewRoundTestBed(opts: { isHost?: boolean } = {}) {
  const { service: wsService, msgs } = createWsMock();
  const restartSubject = new Subject<StartRoundResponse>();
  const roomService = {
    submitAnswer: vi.fn(),
    getSongSummary: vi.fn(),
    overrideAnswer: vi.fn(),
    startSong: vi.fn(),
    revealSong: vi.fn(),
    startRound: vi.fn(),
    restartRound: vi.fn().mockReturnValue(restartSubject.asObservable()),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      song_id: 'song-uuid',
      participant_id: 'p1',
      is_host: opts.isHost ?? false,
      host_id: 'host-uuid',
      round_id: 'round-uuid',
      song_index: 9,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => null }) } },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  return { wsService, msgs, roomService, restartSubject };
}

describe('PlayPageComponent — new round (T-037)', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should show theme input for host in round-leaderboard section after round.finished', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="new-round-theme-input"]'),
    ).not.toBeNull();
  });

  it('should default the theme input to "Général"', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '[data-testid="new-round-theme-input"]',
    );
    expect(input?.value).toBe('Général');
  });

  it('should call restartRound with room id and current theme when host clicks launch', async () => {
    const { msgs, roomService } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="new-round-btn"]')
      ?.click();

    expect(roomService.restartRound).toHaveBeenCalledWith('room-uuid', 'Général', 'both');
  });

  it('should reset to answer view for players after song.started from new round', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: false });
    const fixture = mountFixture();

    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '[data-testid="round-leaderboard-section"]',
      ),
    ).not.toBeNull();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'new-song-uuid',
        song_index: 0,
        round_id: 'new-round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
      },
    });
    fixture.detectChanges();

    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '[data-testid="round-leaderboard-section"]',
      ),
    ).toBeNull();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="answer-input"]'),
    ).not.toBeNull();
  });
});

// ─── Thèmes prédéfinis nouvelle manche (T-112) ───────────────────────────────

describe('PlayPageComponent — T-112 thèmes prédéfinis nouvelle manche', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('affiche 10 puces de thèmes dans la section nouvelle manche pour le host', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();
    const chips = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="new-round-theme-chip"]',
    );
    expect(chips.length).toBe(10);
  });

  it('ne montre pas de puces de thèmes pour un joueur', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: false });
    const fixture = mountFixture();
    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();
    const chips = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="new-round-theme-chip"]',
    );
    expect(chips.length).toBe(0);
  });

  it('clic sur la première puce met à jour newRoundTheme à "Pop 90s"', async () => {
    const { msgs } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();
    const chip = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
      '[data-testid="new-round-theme-chip"]',
    );
    chip?.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.newRoundTheme()).toBe('Pop 90s');
  });

  it('restartRound utilise le thème sélectionné via puce', async () => {
    const { msgs, roomService } = await configureNewRoundTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next(mockLastRevealEvent);
    msgs.next(mockRoundFinishedEvent);
    fixture.detectChanges();
    const chip = (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
      '[data-testid="new-round-theme-chip"]',
    );
    chip?.click();
    fixture.detectChanges();
    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('[data-testid="new-round-btn"]')
      ?.click();
    expect(roomService.restartRound).toHaveBeenCalledWith('room-uuid', 'Pop 90s', 'both');
  });
});

// ─── T-123 clearSession on quit ───────────────────────────────────────────────

async function configureQuitTestBed() {
  const { service: wsService } = createWsMock();
  const sessionService = {
    clearSession: vi.fn(),
    loadSession: vi.fn().mockReturnValue(null),
    saveSession: vi.fn(),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      nickname: 'Alice',
      song_index: 0,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: { paramMap: of({ get: (k: string) => (k === 'code' ? 'ABC123' : null) }) },
      },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: noopRoomService },
      { provide: SessionService, useValue: sessionService },
    ],
  }).compileComponents();

  return { sessionService };
}

describe('PlayPageComponent — T-123 clearSession on quit', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('clears session when user clicks Quitter from play', async () => {
    const { sessionService } = await configureQuitTestBed();
    const fixture = mountFixture();
    fixture.componentInstance.quit();
    expect(sessionService.clearSession).toHaveBeenCalled();
  });

  it('navigates to / after quit from play', async () => {
    await configureQuitTestBed();
    const fixture = mountFixture();
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');
    fixture.componentInstance.quit();
    expect(navigateSpy).toHaveBeenCalledWith(['/']);
  });
});

// ─── Audio (T-042) ────────────────────────────────────────────────────────────

async function configureAudioTestBed() {
  const { service: wsService, msgs } = createWsMock();
  const audioService = { play: vi.fn(), stop: vi.fn() };
  const roomService = {
    submitAnswer: vi.fn(),
    getSongSummary: vi.fn(),
    overrideAnswer: vi.fn(),
    startSong: vi.fn(),
    revealSong: vi.fn(),
    restartRound: vi.fn(),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      participant_id: 'p1',
      is_host: false,
      host_id: 'host-uuid',
      round_id: 'round-uuid',
      song_index: 0,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => null }) } },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
      { provide: AudioService, useValue: audioService },
    ],
  }).compileComponents();

  return { msgs, audioService };
}

describe('PlayPageComponent — audio (T-042)', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should start audio playback on song.started when preview_url is provided', async () => {
    const { msgs, audioService } = await configureAudioTestBed();
    mountFixture();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 0,
        round_id: 'round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
        preview_url: 'https://example.com/preview.mp3',
      },
    });

    expect(audioService.play).toHaveBeenCalledWith('https://example.com/preview.mp3');
  });

  it('should stop audio on song.locked', async () => {
    const { msgs, audioService } = await configureAudioTestBed();
    mountFixture();

    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });

    expect(audioService.stop).toHaveBeenCalled();
  });

  it('should not start audio when preview_url is null', async () => {
    const { msgs, audioService } = await configureAudioTestBed();
    mountFixture();

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 0,
        round_id: 'round-uuid',
        started_at: BASE_NOW.toISOString(),
        ends_at: BASE_ENDS.toISOString(),
        preview_url: null,
      },
    });

    expect(audioService.play).not.toHaveBeenCalled();
  });

  it('should not start audio on component init (no song.started received)', async () => {
    const { audioService } = await configureAudioTestBed();
    mountFixture();

    expect(audioService.play).not.toHaveBeenCalled();
  });
});

// ─── T-113 Host UX ───────────────────────────────────────────────────────────

async function configureHostUxTestBed(opts: { isHost?: boolean } = {}) {
  const { service: wsService, msgs } = createWsMock();
  const summarySubject = new Subject<SongSummaryResponse>();
  const roomService = {
    submitAnswer: vi.fn(),
    getSongSummary: vi.fn().mockReturnValue(summarySubject.asObservable()),
    overrideAnswer: vi.fn(),
    startSong: vi.fn(),
    revealSong: vi.fn().mockReturnValue(new Subject().asObservable()),
    restartRound: vi.fn().mockReturnValue(new Subject().asObservable()),
  };

  history.replaceState(
    {
      room_id: 'room-uuid',
      song_id: 'song-uuid',
      participant_id: 'p1',
      is_host: opts.isHost ?? false,
      host_id: 'host-uuid',
      round_id: 'round-uuid',
      song_index: 0,
      total_songs: 10,
      ends_at: BASE_ENDS.toISOString(),
    },
    '',
  );

  await TestBed.configureTestingModule({
    imports: [PlayPageComponent],
    providers: [
      provideRouter([]),
      { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => null }) } },
      { provide: WebSocketService, useValue: wsService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  return { msgs, roomService, summarySubject };
}

describe('PlayPageComponent — T-113 Host UX', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('host voit bannière "Tu joues aussi" pendant la chanson', async () => {
    await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="host-play-banner"]'),
    ).not.toBeNull();
  });

  it('host voit formulaire de réponse avant verrouillage', async () => {
    await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="answer-input"]'),
    ).not.toBeNull();
  });

  it('joueur normal ne voit pas la bannière host pendant la chanson', async () => {
    await configureHostUxTestBed({ isHost: false });
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="host-play-banner"]'),
    ).toBeNull();
  });

  it('après verrouillage, host voit le mode correction', async () => {
    const { msgs } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '[data-testid="host-correction-section"]',
      ),
    ).not.toBeNull();
  });

  it("après verrouillage, joueur normal voit le message d'attente", async () => {
    const { msgs } = await configureHostUxTestBed({ isHost: false });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="locked-waiting"]'),
    ).not.toBeNull();
  });

  it('host voit état de chargement du résumé après verrouillage', async () => {
    const { msgs } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="summary-loading"]'),
    ).not.toBeNull();
  });

  it('host voit erreur si getSongSummary échoue', async () => {
    const { msgs, summarySubject } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    summarySubject.error(new Error('Network error'));
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="summary-error"]'),
    ).not.toBeNull();
  });

  it('host voit bouton Révéler dans le mode correction', async () => {
    const { msgs } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="reveal-btn"]'),
    ).not.toBeNull();
  });

  it('joueur normal ne voit pas le bouton Révéler après verrouillage', async () => {
    const { msgs } = await configureHostUxTestBed({ isHost: false });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="reveal-btn"]'),
    ).toBeNull();
  });

  it("host voit indicateur d'étapes", async () => {
    await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="host-step-indicator"]'),
    ).not.toBeNull();
  });

  it("joueur normal ne voit pas l'indicateur d'étapes host", async () => {
    await configureHostUxTestBed({ isHost: false });
    const fixture = mountFixture();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="host-step-indicator"]'),
    ).toBeNull();
  });

  it('host voit la liste des réponses après chargement du résumé', async () => {
    const { msgs, summarySubject } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    summarySubject.next({
      song_id: 'song-uuid',
      title: 'Get Lucky',
      artist: 'Daft Punk',
      total_answers: 2,
      doubtful_count: 0,
      answers: [
        {
          answer_id: 'a1',
          participant_id: 'p1',
          nickname: 'Alice',
          text: 'get lucky',
          validation_status: 'found',
          title_found: true,
          artist_found: false,
        },
        {
          answer_id: 'a2',
          participant_id: 'p2',
          nickname: 'Bob',
          text: 'daft punk',
          validation_status: 'not_found',
          title_found: false,
          artist_found: false,
        },
      ],
    });
    fixture.detectChanges();
    const items = (fixture.nativeElement as HTMLElement).querySelectorAll(
      '[data-testid="summary-item"]',
    );
    expect(items.length).toBe(2);
    expect(items[0].querySelector('.play__summary-nickname')?.textContent?.trim()).toBe('Alice');
    expect(items[1].querySelector('.play__summary-nickname')?.textContent?.trim()).toBe('Bob');
  });

  it('host voit message vide si résumé chargé sans réponses', async () => {
    const { msgs, summarySubject } = await configureHostUxTestBed({ isHost: true });
    const fixture = mountFixture();
    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    summarySubject.next({
      song_id: 'song-uuid',
      title: 'Get Lucky',
      artist: 'Daft Punk',
      total_answers: 0,
      doubtful_count: 0,
      answers: [],
    });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="summary-empty"]'),
    ).not.toBeNull();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('[data-testid="summary-list"]'),
    ).toBeNull();
  });
});
