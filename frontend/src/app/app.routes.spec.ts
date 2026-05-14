import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

describe('App routes', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('should resolve the home route at root path', async () => {
    const router = TestBed.inject(Router);
    const navigated = await router.navigate(['/']);
    expect(navigated).toBe(true);
  });

  it('should redirect unknown paths to root', async () => {
    const router = TestBed.inject(Router);
    const navigated = await router.navigate(['/unknown-path']);
    expect(navigated).toBe(true);
  });
});
