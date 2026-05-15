import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { of } from 'rxjs';
import { LobbyPageComponent } from './lobby-page.component';
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

async function setup(role: 'host' | 'player', nickname = 'Alice') {
  const { service, msgs } = createWsMock();

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
    ],
  }).compileComponents();

  const fixture: ComponentFixture<LobbyPageComponent> = TestBed.createComponent(LobbyPageComponent);
  fixture.detectChanges();
  return { fixture, service, msgs };
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
});
