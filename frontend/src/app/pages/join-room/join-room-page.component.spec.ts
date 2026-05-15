import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { JoinRoomPageComponent } from './join-room-page.component';
import { RoomService } from '../../services/room.service';

@Component({ standalone: true, template: '' })
class StubLobbyComponent {}

describe('JoinRoomPageComponent', () => {
  let fixture: ComponentFixture<JoinRoomPageComponent>;
  let component: JoinRoomPageComponent;
  let router: Router;
  let mockRoomService: { joinRoom: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    mockRoomService = { joinRoom: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [JoinRoomPageComponent],
      providers: [
        provideRouter([{ path: 'lobby/:code', component: StubLobbyComponent }]),
        { provide: RoomService, useValue: mockRoomService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(JoinRoomPageComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display room code input', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('input[name="code"]')).toBeTruthy();
  });

  it('should display nickname input', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('input[name="nickname"]')).toBeTruthy();
  });

  it('should display a submit button', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('button[type="submit"]')).toBeTruthy();
  });

  it('should call joinRoom with uppercased code and trimmed nickname', () => {
    mockRoomService.joinRoom.mockReturnValue(of({ room_id: 'uuid1', participant_id: 'uuid3' }));
    component.code = 'abc123';
    component.nickname = '  Bob  ';
    component.submit();
    expect(mockRoomService.joinRoom).toHaveBeenCalledWith('ABC123', 'Bob');
  });

  it('should not call joinRoom when code is blank', () => {
    component.code = '';
    component.nickname = 'Bob';
    component.submit();
    expect(mockRoomService.joinRoom).not.toHaveBeenCalled();
  });

  it('should not call joinRoom when nickname is blank', () => {
    component.code = 'ABC123';
    component.nickname = '';
    component.submit();
    expect(mockRoomService.joinRoom).not.toHaveBeenCalled();
  });

  it('should navigate to /lobby/:code on success', () => {
    mockRoomService.joinRoom.mockReturnValue(of({ room_id: 'uuid1', participant_id: 'uuid3' }));
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.code = 'ABC123';
    component.nickname = 'Bob';
    component.submit();
    expect(navigateSpy).toHaveBeenCalledWith(
      ['/lobby', 'ABC123'],
      expect.objectContaining({ state: expect.objectContaining({ role: 'player' }) }),
    );
  });

  it('should display error detail from API on failure', () => {
    mockRoomService.joinRoom.mockReturnValue(
      throwError(() => ({ error: { detail: 'Salle introuvable' } })),
    );
    component.code = 'ABC123';
    component.nickname = 'Bob';
    component.submit();
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[role="alert"]')?.textContent?.trim()).toBe('Salle introuvable');
  });

  it('should display generic error when no detail provided', () => {
    mockRoomService.joinRoom.mockReturnValue(throwError(() => ({})));
    component.code = 'ABC123';
    component.nickname = 'Bob';
    component.submit();
    expect(component.error()).toContain('Erreur');
  });
});
