import { TestBed } from '@angular/core/testing';
import { WebSocketService, WsEvent } from './websocket.service';

interface MockSocket {
  url: string;
  onmessage: ((event: MessageEvent) => void) | null;
  close: ReturnType<typeof vi.fn>;
}

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockSocket: MockSocket;
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    mockSocket = { url: '', onmessage: null, close: vi.fn() };
    originalWebSocket = window.WebSocket;
    (window as unknown as Record<string, unknown>)['WebSocket'] = function (url: string) {
      mockSocket.url = url;
      return mockSocket;
    };

    TestBed.configureTestingModule({});
    service = TestBed.inject(WebSocketService);
  });

  afterEach(() => {
    (window as unknown as Record<string, unknown>)['WebSocket'] = originalWebSocket;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should connect with correct WebSocket URL', () => {
    service.connect('my-room-id');
    expect(mockSocket.url).toBe('ws://localhost:8000/ws/rooms/my-room-id');
  });

  it('should emit messages from the WebSocket', async () => {
    service.connect('my-room-id');

    const messagePromise = new Promise<WsEvent>(resolve => {
      service.messages$.subscribe(resolve);
    });

    mockSocket.onmessage!(
      { data: JSON.stringify({ event: 'room.state', data: {} }) } as MessageEvent,
    );

    const event = await messagePromise;
    expect(event.event).toBe('room.state');
  });

  it('should close the socket on disconnect', () => {
    service.connect('my-room-id');
    service.disconnect();
    expect(mockSocket.close).toHaveBeenCalled();
  });
});
