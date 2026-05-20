import { TestBed } from '@angular/core/testing';
import { Session, SessionService } from './session.service';

describe('SessionService', () => {
  let service: SessionService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SessionService);
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('saves player session to localStorage', () => {
    const session: Session = {
      roomCode: 'ABC123',
      roomId: 'room-uuid',
      role: 'player',
      participantId: 'player-uuid',
      nickname: 'Alice',
    };
    service.saveSession(session);
    const raw = localStorage.getItem('blindtest_session');
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw!);
    expect(parsed.roomCode).toBe('ABC123');
    expect(parsed.role).toBe('player');
    expect(parsed.nickname).toBe('Alice');
  });

  it('saves host session with hostToken to localStorage', () => {
    const session: Session = {
      roomCode: 'XYZ789',
      roomId: 'room-uuid-2',
      role: 'host',
      participantId: 'host-uuid',
      hostToken: 'my-secret-token',
      nickname: 'Bob',
    };
    service.saveSession(session);
    const parsed = JSON.parse(localStorage.getItem('blindtest_session')!);
    expect(parsed.role).toBe('host');
    expect(parsed.hostToken).toBe('my-secret-token');
  });

  it('loads existing session from localStorage', () => {
    const session: Session = {
      roomCode: 'ABC123',
      roomId: 'room-uuid',
      role: 'player',
      participantId: 'player-uuid',
      nickname: 'Alice',
    };
    service.saveSession(session);
    const loaded = service.loadSession();
    expect(loaded).not.toBeNull();
    expect(loaded?.roomCode).toBe('ABC123');
    expect(loaded?.nickname).toBe('Alice');
    expect(loaded?.participantId).toBe('player-uuid');
  });

  it('returns null when no session in localStorage', () => {
    expect(service.loadSession()).toBeNull();
  });

  it('clears session from localStorage', () => {
    service.saveSession({
      roomCode: 'ABC123',
      roomId: 'r',
      role: 'player',
      participantId: 'p',
      nickname: 'Alice',
    });
    service.clearSession();
    expect(service.loadSession()).toBeNull();
    expect(localStorage.getItem('blindtest_session')).toBeNull();
  });
});
