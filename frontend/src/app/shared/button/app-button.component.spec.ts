import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AppButtonComponent } from './app-button.component';

@Component({
  standalone: true,
  imports: [AppButtonComponent],
  template: `<app-button variant="primary">Click me</app-button>`,
})
class ButtonHostComponent {}

async function setupDirect() {
  await TestBed.configureTestingModule({ imports: [AppButtonComponent] }).compileComponents();
  const fixture: ComponentFixture<AppButtonComponent> = TestBed.createComponent(AppButtonComponent);
  const el = fixture.nativeElement as HTMLElement;
  return { fixture, el, component: fixture.componentInstance };
}

describe('AppButtonComponent — structure', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should create', async () => {
    const { component, fixture } = await setupDirect();
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should have class "btn" on host element', async () => {
    const { el, fixture } = await setupDirect();
    fixture.detectChanges();
    expect(el.classList.contains('btn')).toBe(true);
  });

  it('should have role="button" on host for accessibility', async () => {
    const { el, fixture } = await setupDirect();
    fixture.detectChanges();
    expect(el.getAttribute('role')).toBe('button');
  });

  it('should have tabindex="0" by default', async () => {
    const { el, fixture } = await setupDirect();
    fixture.detectChanges();
    expect(el.getAttribute('tabindex')).toBe('0');
  });

  it('should project content into host', async () => {
    await TestBed.configureTestingModule({ imports: [ButtonHostComponent] }).compileComponents();
    const fixture = TestBed.createComponent(ButtonHostComponent);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('app-button')?.textContent?.trim()).toContain('Click me');
  });
});

describe('AppButtonComponent — variants', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should apply btn-primary class for primary variant', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'primary';
    fixture.detectChanges();
    expect(el.classList.contains('btn-primary')).toBe(true);
  });

  it('should apply btn-secondary class for secondary variant', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'secondary';
    fixture.detectChanges();
    expect(el.classList.contains('btn-secondary')).toBe(true);
  });

  it('should apply btn-success class for success variant', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'success';
    fixture.detectChanges();
    expect(el.classList.contains('btn-success')).toBe(true);
  });

  it('should apply btn-danger class for danger variant', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'danger';
    fixture.detectChanges();
    expect(el.classList.contains('btn-danger')).toBe(true);
  });

  it('should apply btn-ghost class for ghost variant', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'ghost';
    fixture.detectChanges();
    expect(el.classList.contains('btn-ghost')).toBe(true);
  });
});

describe('AppButtonComponent — outputs', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should emit clicked on host click when enabled', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.variant = 'primary';
    fixture.detectChanges();
    const spy = vi.fn();
    fixture.componentInstance.clicked.subscribe(spy);
    el.click();
    expect(spy).toHaveBeenCalledOnce();
  });

  it('should NOT emit clicked when disabled=true', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.disabled = true;
    fixture.detectChanges();
    const spy = vi.fn();
    fixture.componentInstance.clicked.subscribe(spy);
    el.click();
    expect(spy).not.toHaveBeenCalled();
  });

  it('should NOT emit clicked when loading=true', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.loading = true;
    fixture.detectChanges();
    const spy = vi.fn();
    fixture.componentInstance.clicked.subscribe(spy);
    el.click();
    expect(spy).not.toHaveBeenCalled();
  });
});

describe('AppButtonComponent — disabled state', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should set aria-disabled when disabled=true', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.disabled = true;
    fixture.detectChanges();
    expect(el.getAttribute('aria-disabled')).toBe('true');
  });

  it('should set tabindex="-1" when disabled', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.disabled = true;
    fixture.detectChanges();
    expect(el.getAttribute('tabindex')).toBe('-1');
  });

  it('should NOT have aria-disabled when enabled', async () => {
    const { fixture, el } = await setupDirect();
    fixture.detectChanges();
    expect(el.getAttribute('aria-disabled')).toBeNull();
  });
});

describe('AppButtonComponent — loading state', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should show spinner when loading=true', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.loading = true;
    fixture.detectChanges();
    expect(el.querySelector('.btn__spinner')).not.toBeNull();
  });

  it('should NOT show spinner when loading=false', async () => {
    const { fixture, el } = await setupDirect();
    fixture.detectChanges();
    expect(el.querySelector('.btn__spinner')).toBeNull();
  });

  it('should set aria-disabled when loading=true', async () => {
    const { fixture, el } = await setupDirect();
    fixture.componentInstance.loading = true;
    fixture.detectChanges();
    expect(el.getAttribute('aria-disabled')).toBe('true');
  });
});
