import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { of } from 'rxjs';
import { PlayPageComponent } from './play-page.component';
import { WebSocketService, WsEvent } from '../../services/websocket.service';
import { RoomService, SubmitAnswerResponse } from '../../services/room.service';

const BASE_NOW = new Date('2026-01-01T12:00:00.000Z');
const BASE_ENDS = new Date('2026-01-01T12:00:30.000Z'); // 30s later

function createWsMock() {
  const msgs = new Subject<WsEvent>();
  const service = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    messages$: msgs.asObservable() as Observable<WsEvent>,
  };
  return { service, msgs };
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
  const { service, msgs } = createWsMock();

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

  return { service, msgs };
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

  it('should disable the answer input after song.locked event', async () => {
    const { msgs } = await configureTestBed();
    const fixture = mountFixture();

    msgs.next({ event: 'song.locked', data: { song_id: 'song-uuid', round_id: 'round-uuid' } });
    fixture.detectChanges();

    const input = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      '[data-testid="answer-input"]',
    );
    expect(input?.disabled).toBe(true);
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
    const songNum = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="song-number"]');
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

    const songNum = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="song-number"]');
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

  it('should redirect to / if no room_id in state', async () => {
    history.replaceState({}, '');
    const { service, msgs } = createWsMock();

    await TestBed.configureTestingModule({
      imports: [PlayPageComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of({ get: () => null }) },
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

    submitSubject.error({ status: 409 });
    fixture.detectChanges();

    const errorEl = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="submit-error"]',
    );
    expect(errorEl?.textContent).toContain('Trop tard');
  });
});
