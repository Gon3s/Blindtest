import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { CreateRoomPageComponent } from './create-room-page.component';
import { RoomService } from '../../services/room.service';

@Component({ standalone: true, template: '' })
class StubLobbyComponent {}

describe('CreateRoomPageComponent', () => {
  let fixture: ComponentFixture<CreateRoomPageComponent>;
  let component: CreateRoomPageComponent;
  let router: Router;
  let mockRoomService: { createRoom: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    mockRoomService = { createRoom: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [CreateRoomPageComponent],
      providers: [
        provideRouter([{ path: 'lobby/:code', component: StubLobbyComponent }]),
        { provide: RoomService, useValue: mockRoomService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CreateRoomPageComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display nickname input', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('input[name="nickname"]')).toBeTruthy();
  });

  it('should display a submit button', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('button[type="submit"]')).toBeTruthy();
  });

  it('should call createRoom with trimmed nickname on submit', () => {
    mockRoomService.createRoom.mockReturnValue(
      of({ room_id: 'uuid1', code: 'ABC123', host_id: 'uuid2' }),
    );
    component.nickname = '  Alice  ';
    component.submit();
    expect(mockRoomService.createRoom).toHaveBeenCalledWith('Alice');
  });

  it('should not call createRoom when nickname is blank', () => {
    component.nickname = '   ';
    component.submit();
    expect(mockRoomService.createRoom).not.toHaveBeenCalled();
  });

  it('should navigate to /lobby/:code on success', () => {
    mockRoomService.createRoom.mockReturnValue(
      of({ room_id: 'uuid1', code: 'ABC123', host_id: 'uuid2' }),
    );
    const navigateSpy = vi.spyOn(router, 'navigate');
    component.nickname = 'Alice';
    component.submit();
    expect(navigateSpy).toHaveBeenCalledWith(
      ['/lobby', 'ABC123'],
      expect.objectContaining({ state: expect.objectContaining({ role: 'host' }) }),
    );
  });

  it('should display error detail from API on failure', () => {
    mockRoomService.createRoom.mockReturnValue(
      throwError(() => ({ error: { detail: 'Nickname invalide' } })),
    );
    component.nickname = 'Alice';
    component.submit();
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[role="alert"]')?.textContent?.trim()).toBe('Nickname invalide');
  });

  it('should display generic error when no detail provided', () => {
    mockRoomService.createRoom.mockReturnValue(throwError(() => ({})));
    component.nickname = 'Alice';
    component.submit();
    expect(component.error()).toContain('Erreur');
  });
});
