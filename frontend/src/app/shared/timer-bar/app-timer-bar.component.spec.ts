import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppTimerBarComponent } from './app-timer-bar.component';

async function setup() {
  await TestBed.configureTestingModule({ imports: [AppTimerBarComponent] }).compileComponents();
  const fixture: ComponentFixture<AppTimerBarComponent> = TestBed.createComponent(AppTimerBarComponent);
  // detectChanges is called after each test sets inputs to avoid NG0100
  const el = fixture.nativeElement as HTMLElement;
  return { fixture, el };
}

describe('AppTimerBarComponent — structure', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should create', async () => {
    const { fixture } = await setup();
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should expose data-testid="timer" for backwards compatibility', async () => {
    const { fixture, el } = await setup();
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="timer"]')).not.toBeNull();
  });

  it('should display timeLeft value in the timer element', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.timeLeft = 27;
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="timer"]')?.textContent?.trim()).toBe('27');
  });

  it('should render a progress track element', async () => {
    const { fixture, el } = await setup();
    fixture.detectChanges();
    expect(el.querySelector('.timer-bar__track')).not.toBeNull();
  });

  it('should render a progress fill element', async () => {
    const { fixture, el } = await setup();
    fixture.detectChanges();
    expect(el.querySelector('.timer-bar__fill')).not.toBeNull();
  });
});

describe('AppTimerBarComponent — progress', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should set fill width to 100% when progress=1', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 1;
    fixture.detectChanges();
    const fill = el.querySelector<HTMLElement>('.timer-bar__fill');
    expect(fill?.style.width).toBe('100%');
  });

  it('should set fill width to 50% when progress=0.5', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 0.5;
    fixture.detectChanges();
    const fill = el.querySelector<HTMLElement>('.timer-bar__fill');
    expect(fill?.style.width).toBe('50%');
  });

  it('should set fill width to 0% when progress=0', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 0;
    fixture.detectChanges();
    const fill = el.querySelector<HTMLElement>('.timer-bar__fill');
    expect(fill?.style.width).toBe('0%');
  });

  it('should add urgent class on fill when progress < 0.25', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 0.2;
    fixture.detectChanges();
    expect(el.querySelector('.timer-bar__fill--urgent')).not.toBeNull();
  });

  it('should add urgent class on timer text when progress < 0.25', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 0.1;
    fixture.detectChanges();
    expect(el.querySelector('.timer-bar__time--urgent')).not.toBeNull();
  });

  it('should NOT add urgent class when progress >= 0.25', async () => {
    const { fixture, el } = await setup();
    fixture.componentInstance.progress = 0.5;
    fixture.detectChanges();
    expect(el.querySelector('.timer-bar__fill--urgent')).toBeNull();
    expect(el.querySelector('.timer-bar__time--urgent')).toBeNull();
  });
});
