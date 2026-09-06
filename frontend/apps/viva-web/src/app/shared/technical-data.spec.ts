import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TechnicalDataComponent } from './technical-data';

describe('TechnicalDataComponent', () => {
  let fixture: ComponentFixture<TechnicalDataComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [TechnicalDataComponent] });
    fixture = TestBed.createComponent(TechnicalDataComponent);
  });

  it('renders nested objects, arrays, booleans, nulls, and metric-like values', () => {
    fixture.componentRef.setInput('title', 'Technical');
    fixture.componentRef.setInput('data', {
      thermal: { value: 0.28, unit: 'W/m2K' },
      layers: ['outer', { insulation: true }],
      note: null,
    });
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Technical');
    expect(text).toContain('0.28');
    expect(text).toContain('W/m2K');
    expect(text).toContain('outer');
    expect(text).toContain('Yes');
    expect(text).toContain('Unavailable');
  });
});
