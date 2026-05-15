import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Observable, of, Subject } from 'rxjs';
import { LobbyPageComponent } from './lobby-page.component';
import { WebSocketService, WsEvent } from '../../services/websocket.service';

describe('LobbyPageComponent', () => {
  let fixture: ComponentFixture<LobbyPageComponent>;
  let wsMessages$: Subject<WsEvent>;
  let mockWsService: {
    connect: ReturnType<typeof vi.fn>;
    disconnect: ReturnType<typeof vi.fn>;
    messages$: Observable<WsEvent>;
  };

  beforeEach(async () => {
    wsMessages$ = new Subject<WsEvent>();
    mockWsService = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      messages$: wsMessages$.asObservable(),
    };

    history.replaceState({ room_id: 'test-room-uuid', role: 'host' }, '');

    await TestBed.configureTestingModule({
      imports: [LobbyPageComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of({ get: (key: string) => (key === 'code' ? 'ABC123' : null) }),
          },
        },
        { provide: WebSocketService, useValue: mockWsService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LobbyPageComponent);
    fixture.detectChanges();
  });

  afterEach(() => {
    history.replaceState(null, '');
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display the room code', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('ABC123');
  });

  it('should display a waiting message', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('attente');
  });

  it('should connect to WebSocket on init with the room_id from state', () => {
    expect(mockWsService.connect).toHaveBeenCalledWith('test-room-uuid');
  });

  it('should update participants list on room.state event', () => {
    wsMessages$.next({
      event: 'room.state',
      data: {
        room_id: 'test-room-uuid',
        participants: [{ participant_id: 'p1', nickname: 'Alice', is_host: true }],
      },
    });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Alice');
  });

  it('should add a participant on participant.joined event', () => {
    wsMessages$.next({
      event: 'room.state',
      data: { room_id: 'test-room-uuid', participants: [] },
    });
    wsMessages$.next({
      event: 'participant.joined',
      data: { participant_id: 'p2', nickname: 'Bob', is_host: false },
    });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Bob');
  });
});
