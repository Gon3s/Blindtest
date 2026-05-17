import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppBadgeComponent } from './app-badge.component';

async function setup() {
  await TestBed.configureTestingModule({ imports: [AppBadgeComponent] }).compileComponents();
  const fixture: ComponentFixture<AppBadgeComponent> = TestBed.createComponent(AppBadgeComponent);
  const el = fixture.nativeElement as HTMLElement;
  return { fixture, el };
}

describe('AppBadgeComponent — structure', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should create', async () => {
    const { fixture } = await setup();
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should display the text input', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.text = 'found';
    fixture.detectChanges();
    expect(el.textContent?.trim()).toContain('found');
  });

  it('should apply badge class on host', async () => {
    const { fixture, el } = await setup();
    fixture.detectChanges();
    expect(el.classList.contains('badge')).toBe(true);
  });
});

describe('AppBadgeComponent — variants', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should apply badge--success for success variant', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.variant = 'success';
    fixture.detectChanges();
    expect(el.classList.contains('badge--success')).toBe(true);
  });

  it('should apply badge--danger for danger variant', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.variant = 'danger';
    fixture.detectChanges();
    expect(el.classList.contains('badge--danger')).toBe(true);
  });

  it('should apply badge--warning for warning variant', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.variant = 'warning';
    fixture.detectChanges();
    expect(el.classList.contains('badge--warning')).toBe(true);
  });

  it('should apply badge--info for info variant', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.variant = 'info';
    fixture.detectChanges();
    expect(el.classList.contains('badge--info')).toBe(true);
  });

  it('should apply badge--neutral for neutral variant (default)', async () => {
    const { fixture, el } = await setup();
    fixture.detectChanges();
    expect(el.classList.contains('badge--neutral')).toBe(true);
  });
});
