import { TestBed } from '@angular/core/testing';
import { ConnectionStatus, WebSocketService, WsEvent } from './websocket.service';
import { environment } from '../../environments/environment';

interface MockSocket {
  url: string;
  onopen: (() => void) | null;
  onmessage: ((event: MessageEvent) => void) | null;
  onclose: ((event: Partial<CloseEvent>) => void) | null;
  onerror: (() => void) | null;
  close: ReturnType<typeof vi.fn>;
}

function createMockSocket(url: string): MockSocket {
  return { url, onopen: null, onmessage: null, onclose: null, onerror: null, close: vi.fn() };
}

describe('WebSocketService', () => {
  let service: WebSocketService;
  let sockets: MockSocket[];
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    sockets = [];
    originalWebSocket = window.WebSocket;
    (window as unknown as Record<string, unknown>)['WebSocket'] = function (url: string) {
      const socket = createMockSocket(url);
      sockets.push(socket);
      return socket;
    };

    TestBed.configureTestingModule({});
    service = TestBed.inject(WebSocketService);
  });

  afterEach(() => {
    (window as unknown as Record<string, unknown>)['WebSocket'] = originalWebSocket;
    vi.useRealTimers();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should connect with correct WebSocket URL', () => {
    service.connect('my-room-id');
    expect(sockets[0].url).toBe(`${environment.wsBaseUrl}/ws/rooms/my-room-id`);
  });

  it('should emit messages from the WebSocket', async () => {
    service.connect('my-room-id');

    const messagePromise = new Promise<WsEvent>((resolve) => {
      service.messages$.subscribe(resolve);
    });

    sockets[0].onmessage!({
      data: JSON.stringify({ event: 'room.state', data: {} }),
    } as MessageEvent);

    const event = await messagePromise;
    expect(event.event).toBe('room.state');
  });

  it('should close the socket on disconnect', () => {
    service.connect('my-room-id');
    service.disconnect();
    expect(sockets[0].close).toHaveBeenCalled();
  });

  // ---- Connection status ----

  describe('connection status', () => {
    it('starts as disconnected', () => {
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      expect(statuses[0]).toBe('disconnected');
    });

    it('becomes connecting on connect()', () => {
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      expect(statuses).toContain('connecting');
    });

    it('becomes connected on onopen', () => {
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      sockets[0].onopen!();
      expect(statuses[statuses.length - 1]).toBe('connected');
    });

    it('becomes disconnected on intentional disconnect()', () => {
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      sockets[0].onopen!();
      service.disconnect();
      expect(statuses[statuses.length - 1]).toBe('disconnected');
    });
  });

  // ---- Reconnection ----

  describe('reconnection', () => {
    it('becomes reconnecting on unexpected close', () => {
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      sockets[0].onopen!();
      sockets[0].onclose!({ wasClean: false });
      expect(statuses[statuses.length - 1]).toBe('reconnecting');
    });

    it('attempts reconnect after delay', () => {
      vi.useFakeTimers();
      service.connect('room-1');
      sockets[0].onopen!();
      sockets[0].onclose!({ wasClean: false });
      expect(sockets.length).toBe(1);
      vi.advanceTimersByTime(2000);
      expect(sockets.length).toBe(2);
    });

    it('resets attempt counter on successful reconnect', () => {
      vi.useFakeTimers();
      service.connect('room-1');
      sockets[0].onopen!();
      sockets[0].onclose!({ wasClean: false });
      vi.advanceTimersByTime(2000);
      sockets[1].onopen!();
      sockets[1].onclose!({ wasClean: false });
      vi.advanceTimersByTime(2000);
      expect(sockets.length).toBe(3);
    });

    it('does not reconnect on clean close', () => {
      vi.useFakeTimers();
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      sockets[0].onopen!();
      sockets[0].onclose!({ wasClean: true });
      vi.advanceTimersByTime(5000);
      expect(sockets.length).toBe(1);
      expect(statuses[statuses.length - 1]).toBe('disconnected');
    });

    it('does not reconnect after intentional disconnect()', () => {
      vi.useFakeTimers();
      service.connect('room-1');
      sockets[0].onopen!();
      service.disconnect();
      vi.advanceTimersByTime(5000);
      expect(sockets.length).toBe(1);
    });

    it('becomes error after max reconnection attempts', () => {
      vi.useFakeTimers();
      const statuses: ConnectionStatus[] = [];
      service.connectionStatus$.subscribe((s) => statuses.push(s));
      service.connect('room-1');
      for (let i = 0; i < 5; i++) {
        sockets[i].onclose!({ wasClean: false });
        vi.advanceTimersByTime(2000);
      }
      sockets[5].onclose!({ wasClean: false });
      expect(statuses[statuses.length - 1]).toBe('error');
    });
  });

  // ---- JSON protection ----

  describe('json parse protection', () => {
    it('ignores invalid JSON without throwing', () => {
      service.connect('room-1');
      const messages: WsEvent[] = [];
      service.messages$.subscribe((m) => messages.push(m));
      expect(() => {
        sockets[0].onmessage!({ data: 'not-valid-json{{' } as MessageEvent);
      }).not.toThrow();
      expect(messages.length).toBe(0);
    });

    it('emits valid messages after invalid JSON', () => {
      service.connect('room-1');
      const messages: WsEvent[] = [];
      service.messages$.subscribe((m) => messages.push(m));
      sockets[0].onmessage!({ data: 'invalid' } as MessageEvent);
      sockets[0].onmessage!({
        data: JSON.stringify({ event: 'room.state', data: {} }),
      } as MessageEvent);
      expect(messages.length).toBe(1);
      expect(messages[0].event).toBe('room.state');
    });
  });
});
