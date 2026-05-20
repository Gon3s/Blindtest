import { TestBed } from '@angular/core/testing';
import { ErrorService } from './error.service';

describe('ErrorService', () => {
  let service: ErrorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ErrorService);
  });

  describe('fromHttpError', () => {
    it('should return user-friendly message for room_not_found code', () => {
      const err = { error: { code: 'room_not_found', message: 'ignored' } };
      const msg = service.fromHttpError(err);
      expect(msg).toBe('Code de salle invalide. Vérifie le code et réessaie.');
    });

    it('should return user-friendly message for nickname_taken code', () => {
      const err = { error: { code: 'nickname_taken', message: 'ignored' } };
      const msg = service.fromHttpError(err);
      expect(msg).toBe('Ce pseudo est déjà pris. Choisis-en un autre.');
    });

    it('should return user-friendly message for room_already_started code', () => {
      const err = { error: { code: 'room_already_started', message: 'ignored' } };
      const msg = service.fromHttpError(err);
      expect(msg).toBe('La partie a déjà commencé. Tu ne peux plus rejoindre.');
    });

    it('should return user-friendly message for answer_too_late code', () => {
      const err = { error: { code: 'answer_too_late', message: 'ignored' } };
      const msg = service.fromHttpError(err);
      expect(msg).toBe('Trop tard ! La chanson est terminée.');
    });

    it('should fall back to message field when code is unknown', () => {
      const err = { error: { code: 'unknown_code', message: 'Un message quelconque' } };
      const msg = service.fromHttpError(err);
      expect(msg).toBe('Un message quelconque');
    });

    it('should handle legacy string detail format', () => {
      const err = { error: { detail: 'Erreur legacy' } };
      const msg = service.fromHttpError(err as never);
      expect(msg).toBe('Erreur legacy');
    });

    it('should return generic message when error is empty', () => {
      const msg = service.fromHttpError({});
      expect(msg.length).toBeGreaterThan(0);
      expect(msg).not.toContain('undefined');
    });

    it('should never return a stacktrace', () => {
      const err = { error: { code: 'room_not_found', message: 'RoomNotFoundError: ...' } };
      const msg = service.fromHttpError(err);
      expect(msg).not.toContain('RoomNotFoundError');
    });
  });

  describe('fromCode', () => {
    it('should return message for known code', () => {
      expect(service.fromCode('room_not_found')).toBeTruthy();
      expect(service.fromCode('nickname_taken')).toBeTruthy();
      expect(service.fromCode('answer_too_late')).toBeTruthy();
      expect(service.fromCode('not_host')).toBeTruthy();
    });

    it('should return null for unknown code', () => {
      expect(service.fromCode('completely_unknown_xyz')).toBeNull();
    });
  });

  describe('static messages', () => {
    it('should have wsDisconnected message', () => {
      expect(service.wsDisconnected.length).toBeGreaterThan(5);
      expect(service.wsDisconnected.toLowerCase()).toContain('connexion');
    });

    it('should have audioBlocked message', () => {
      expect(service.audioBlocked.length).toBeGreaterThan(5);
    });
  });
});
