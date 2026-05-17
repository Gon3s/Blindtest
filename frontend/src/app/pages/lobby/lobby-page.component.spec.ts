import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { of } from 'rxjs';
import { LobbyPageComponent } from './lobby-page.component';
import { AudioService } from '../../services/audio.service';
import { RoomService } from '../../services/room.service';
import { WebSocketService, WsEvent } from '../../services/websocket.service';

function createWsMock() {
  const msgs = new Subject<WsEvent>();
  const service = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    messages$: msgs.asObservable() as Observable<WsEvent>,
  };
  return { service, msgs };
}

function createAudioMock() {
  return { play: vi.fn(), stop: vi.fn() };
}

function createRoomServiceMock() {
  return { startRound: vi.fn().mockReturnValue(of({})) };
}

async function setup(role: 'host' | 'player', nickname = 'Alice') {
  const { service, msgs } = createWsMock();
  const audioService = createAudioMock();
  const roomService = createRoomServiceMock();

  history.replaceState({ room_id: 'room-uuid', role, nickname }, '');

  await TestBed.configureTestingModule({
    imports: [LobbyPageComponent],
    providers: [
      provideRouter([]),
      {
        provide: ActivatedRoute,
        useValue: {
          paramMap: of({ get: (k: string) => (k === 'code' ? 'ABC123' : null) }),
        },
      },
      { provide: WebSocketService, useValue: service },
      { provide: AudioService, useValue: audioService },
      { provide: RoomService, useValue: roomService },
    ],
  }).compileComponents();

  const fixture: ComponentFixture<LobbyPageComponent> = TestBed.createComponent(LobbyPageComponent);
  fixture.detectChanges();
  const { Router } = await import('@angular/router');
  const router = TestBed.inject(Router);
  return { fixture, service, msgs, audioService, router, roomService };
}

describe('LobbyPageComponent — host view', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should create', async () => {
    const { fixture } = await setup('host');
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display the room code', async () => {
    const { fixture } = await setup('host');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('ABC123');
  });

  it('should connect to WebSocket with room_id from state', async () => {
    const { service } = await setup('host');
    expect(service.connect).toHaveBeenCalledWith('room-uuid');
  });

  it('should show the "Lancer la manche" CTA button', async () => {
    const { fixture } = await setup('host');
    const btn = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="start-round"]');
    expect(btn).not.toBeNull();
  });

  it('should update participants list on room.state event', async () => {
    const { fixture, msgs } = await setup('host');
    msgs.next({
      event: 'room.state',
      data: {
        room_id: 'room-uuid',
        participants: [{ participant_id: 'p1', nickname: 'Alice', is_host: true }],
      },
    });
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Alice');
  });

  it('should add a participant on participant.joined event', async () => {
    const { fixture, msgs } = await setup('host');
    msgs.next({ event: 'room.state', data: { room_id: 'room-uuid', participants: [] } });
    msgs.next({
      event: 'participant.joined',
      data: { participant_id: 'p2', nickname: 'Bob', is_host: false },
    });
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Bob');
  });
});

describe('LobbyPageComponent — player waiting view', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should create', async () => {
    const { fixture } = await setup('player', 'Charlie');
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display own nickname', async () => {
    const { fixture } = await setup('player', 'Charlie');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Charlie');
  });

  it('should display a waiting message', async () => {
    const { fixture } = await setup('player', 'Charlie');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('attente');
  });

  it('should NOT show the "Lancer la manche" button', async () => {
    const { fixture } = await setup('player', 'Charlie');
    const btn = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="start-round"]');
    expect(btn).toBeNull();
  });

  it('should connect to WebSocket with room_id from state', async () => {
    const { service } = await setup('player', 'Charlie');
    expect(service.connect).toHaveBeenCalledWith('room-uuid');
  });

  it('should update participants list on room.state event', async () => {
    const { fixture, msgs } = await setup('player', 'Charlie');
    msgs.next({
      event: 'room.state',
      data: {
        room_id: 'room-uuid',
        participants: [
          { participant_id: 'p1', nickname: 'Alice', is_host: true },
          { participant_id: 'p2', nickname: 'Charlie', is_host: false },
        ],
      },
    });
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Charlie');
  });

  it('should navigate to /play/:code on song.started event', async () => {
    const { fixture, msgs, router } = await setup('player', 'Charlie');
    const navigateSpy = vi.spyOn(router, 'navigate');

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 0,
        round_id: 'round-uuid',
        started_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 30_000).toISOString(),
        preview_url: null,
      },
    });
    fixture.detectChanges();

    expect(navigateSpy).toHaveBeenCalledWith(
      ['/play', 'ABC123'],
      expect.objectContaining({
        state: expect.objectContaining({ room_id: 'room-uuid', song_index: 0 }),
      }),
    );
  });
});

describe('LobbyPageComponent — audio (T-042)', () => {
  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('should call audioService.play() with preview_url on song.started', async () => {
    const { fixture, msgs, audioService, router } = await setup('player', 'Charlie');
    vi.spyOn(router, 'navigate');

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 0,
        round_id: 'round-uuid',
        started_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 30_000).toISOString(),
        preview_url: 'https://example.com/preview.mp3',
      },
    });
    fixture.detectChanges();

    expect(audioService.play).toHaveBeenCalledWith('https://example.com/preview.mp3');
  });

  it('should NOT call audioService.play() when preview_url is null', async () => {
    const { fixture, msgs, audioService, router } = await setup('player', 'Charlie');
    vi.spyOn(router, 'navigate');

    msgs.next({
      event: 'song.started',
      data: {
        song_id: 'song-uuid',
        song_index: 0,
        round_id: 'round-uuid',
        started_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 30_000).toISOString(),
        preview_url: null,
      },
    });
    fixture.detectChanges();

    expect(audioService.play).not.toHaveBeenCalled();
  });

  it('should NOT call audioService.play() on component init', async () => {
    const { audioService } = await setup('player', 'Charlie');
    expect(audioService.play).not.toHaveBeenCalled();
  });
});

describe('LobbyPageComponent — T-060 theme field', () => {
  const twoParticipants = [
    { participant_id: 'p1', nickname: 'Alice', is_host: true },
    { participant_id: 'p2', nickname: 'Bob', is_host: false },
  ];

  afterEach(() => {
    history.replaceState(null, '');
    TestBed.resetTestingModule();
  });

  it('désactive le bouton si thème vide', async () => {
    const { fixture, msgs } = await setup('host');
    msgs.next({ event: 'room.state', data: { room_id: 'room-uuid', participants: twoParticipants } });
    fixture.detectChanges();

    const btn = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="start-round"]');
    expect(btn?.getAttribute('aria-disabled')).toBe('true');
  });

  it('active le bouton si thème non vide et participants >= 2', async () => {
    const { fixture, msgs } = await setup('host');
    msgs.next({ event: 'room.state', data: { room_id: 'room-uuid', participants: twoParticipants } });
    fixture.detectChanges();

    fixture.componentInstance.theme.set('Pop');
    fixture.detectChanges();

    const btn = (fixture.nativeElement as HTMLElement).querySelector('[data-testid="start-round"]');
    expect(btn?.getAttribute('aria-disabled')).toBeNull();
  });

  it('passe le thème saisi à startRound', async () => {
    const { fixture, msgs, roomService } = await setup('host');
    msgs.next({ event: 'room.state', data: { room_id: 'room-uuid', participants: twoParticipants } });
    fixture.detectChanges();

    fixture.componentInstance.theme.set('Pop');
    fixture.detectChanges();

    fixture.componentInstance.startRound();

    expect(roomService.startRound).toHaveBeenCalledWith('room-uuid', 'Pop');
  });
});
