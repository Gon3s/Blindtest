import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { HomePageComponent } from './home-page.component';

describe('HomePageComponent', () => {
  let fixture: ComponentFixture<HomePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomePageComponent],
      providers: [provideRouter([])],
    }).compileComponents();
    fixture = TestBed.createComponent(HomePageComponent);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display app title', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('h1')?.textContent).toContain('Blindtest');
  });

  it('should have a link to create a room', () => {
    const el = fixture.nativeElement as HTMLElement;
    const link = el.querySelector('a[href="/create"]');
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain('Créer');
  });

  it('should have a link to join a room', () => {
    const el = fixture.nativeElement as HTMLElement;
    const link = el.querySelector('a[href="/join"]');
    expect(link).toBeTruthy();
    expect(link?.textContent).toContain('Rejoindre');
  });
});
