import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { LobbyPageComponent } from './lobby-page.component';

describe('LobbyPageComponent', () => {
  let fixture: ComponentFixture<LobbyPageComponent>;

  beforeEach(async () => {
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
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LobbyPageComponent);
    fixture.detectChanges();
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
});
