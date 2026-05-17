import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { AppCardComponent } from './app-card.component';

@Component({
  standalone: true,
  imports: [AppCardComponent],
  template: `<app-card title="Ma carte" />`,
})
class CardWithTitleHost {}

@Component({
  standalone: true,
  imports: [AppCardComponent],
  template: `<app-card />`,
})
class CardNoTitleHost {}

@Component({
  standalone: true,
  imports: [AppCardComponent],
  template: `<app-card><p class="inner">Content</p></app-card>`,
})
class CardWithContentHost {}

describe('AppCardComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('should create', async () => {
    await TestBed.configureTestingModule({ imports: [CardNoTitleHost] }).compileComponents();
    const fixture = TestBed.createComponent(CardNoTitleHost);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('app-card')).not.toBeNull();
  });

  it('should apply card class on host element', async () => {
    await TestBed.configureTestingModule({ imports: [CardNoTitleHost] }).compileComponents();
    const fixture = TestBed.createComponent(CardNoTitleHost);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('app-card')?.classList.contains('card')).toBe(true);
  });

  it('should render title when title input is provided', async () => {
    await TestBed.configureTestingModule({ imports: [CardWithTitleHost] }).compileComponents();
    const fixture = TestBed.createComponent(CardWithTitleHost);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.card__title')?.textContent?.trim()).toBe('Ma carte');
  });

  it('should NOT render title element when title is not provided', async () => {
    await TestBed.configureTestingModule({ imports: [CardNoTitleHost] }).compileComponents();
    const fixture = TestBed.createComponent(CardNoTitleHost);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.card__title')).toBeNull();
  });

  it('should project content into the card body', async () => {
    await TestBed.configureTestingModule({ imports: [CardWithContentHost] }).compileComponents();
    const fixture = TestBed.createComponent(CardWithContentHost);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.inner')).not.toBeNull();
    expect(el.querySelector('.inner')?.textContent?.trim()).toBe('Content');
  });
});
