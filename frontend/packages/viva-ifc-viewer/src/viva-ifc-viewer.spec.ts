import { describe, expect, it } from 'vitest';
import { VivaIfcViewer, type VivaIfcModelInput } from './viva-ifc-viewer';

function createMockRuntime() {
  const calls: string[] = [];
  return {
    calls,
    runtime: {
      initialize: async () => {
        calls.push('initialize');
      },
      load: async (model: VivaIfcModelInput) => {
        calls.push(`load:${model.id}`);
      },
      clear: async () => {
        calls.push('clear');
      },
      fitToModel: async () => {
        calls.push('fit');
      },
      dispose: async () => {
        calls.push('dispose');
      },
    },
  };
}

describe('VivaIfcViewer', () => {
  it('runs framework-independent lifecycle calls in order', async () => {
    const mock = createMockRuntime();
    const viewer = new VivaIfcViewer(() => mock.runtime);

    await viewer.initialize({} as HTMLElement);
    await viewer.load({ id: 'asset-1', name: 'model.ifc', bytes: new Uint8Array([1]) });
    await viewer.fitToModel();
    await viewer.dispose();

    expect(mock.calls).toEqual(['initialize', 'load:asset-1', 'fit', 'dispose']);
  });

  it('rejects load before initialize', async () => {
    const mock = createMockRuntime();
    const viewer = new VivaIfcViewer(() => mock.runtime);

    await expect(
      viewer.load({ id: 'asset-1', name: 'model.ifc', bytes: new Uint8Array([1]) }),
    ).rejects.toThrow('Initialize');
  });

  it('rejects empty model bytes', async () => {
    const mock = createMockRuntime();
    const viewer = new VivaIfcViewer(() => mock.runtime);
    await viewer.initialize({} as HTMLElement);

    await expect(
      viewer.load({ id: 'asset-1', name: 'model.ifc', bytes: new Uint8Array() }),
    ).rejects.toThrow('empty');
  });
});
