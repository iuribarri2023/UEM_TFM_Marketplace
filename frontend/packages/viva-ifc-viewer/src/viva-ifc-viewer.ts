export interface VivaIfcModelInput {
  id: string;
  name: string;
  bytes: Uint8Array;
}

export interface VivaIfcViewerOptions {
  background?: 'light' | 'dark';
}

interface Runtime {
  initialize(container: HTMLElement, options?: VivaIfcViewerOptions): Promise<void>;
  load(model: VivaIfcModelInput): Promise<void>;
  clear(): Promise<void>;
  fitToModel(): Promise<void>;
  dispose(): Promise<void>;
}

export type VivaIfcRuntimeFactory = () => Runtime;

export class VivaIfcViewer {
  private readonly runtime: Runtime;
  private initialized = false;
  private disposed = false;

  constructor(runtimeFactory: VivaIfcRuntimeFactory = createThatOpenRuntime) {
    this.runtime = runtimeFactory();
  }

  async initialize(container: HTMLElement, options?: VivaIfcViewerOptions): Promise<void> {
    if (this.disposed) {
      throw new Error('Viewer has been disposed.');
    }
    if (this.initialized) {
      return;
    }
    await this.runtime.initialize(container, options);
    this.initialized = true;
  }

  async load(model: VivaIfcModelInput): Promise<void> {
    this.assertReady();
    if (model.bytes.byteLength === 0) {
      throw new Error('IFC model bytes are empty.');
    }
    await this.runtime.load(model);
  }

  async clear(): Promise<void> {
    if (this.initialized && !this.disposed) {
      await this.runtime.clear();
    }
  }

  async fitToModel(): Promise<void> {
    this.assertReady();
    await this.runtime.fitToModel();
  }

  async dispose(): Promise<void> {
    if (this.disposed) {
      return;
    }
    if (this.initialized) {
      await this.runtime.dispose();
    }
    this.disposed = true;
    this.initialized = false;
  }

  private assertReady(): void {
    if (!this.initialized || this.disposed) {
      throw new Error('Initialize the IFC viewer before using it.');
    }
  }
}

function createThatOpenRuntime(): Runtime {
  let components: any;
  let world: any;
  let fragments: any;
  let ifcLoader: any;

  return {
    async initialize(container: HTMLElement, options?: VivaIfcViewerOptions): Promise<void> {
      const [OBC, THREE] = await Promise.all([import('@thatopen/components'), import('three')]);
      components = new OBC.Components();
      const worlds = components.get(OBC.Worlds);
      world = worlds.create();
      world.scene = new OBC.SimpleScene(components);
      world.scene.setup();
      world.scene.three.background = new THREE.Color(
        options?.background === 'dark' ? 0x202722 : 0xe9ede6,
      );
      world.renderer = new OBC.SimpleRenderer(components, container);
      world.camera = new OBC.OrthoPerspectiveCamera(components);
      await world.camera.controls.setLookAt(16, 12, 16, 0, 0, 0);
      components.init();
      components.get(OBC.Grids).create(world);

      fragments = components.get(OBC.FragmentsManager);
      const workerUrl = await OBC.FragmentsManager.getWorker();
      fragments.init(workerUrl);
      world.camera.controls.addEventListener('update', () => fragments.core.update());
      fragments.list.onItemSet.add(({ value: model }: { value: any }) => {
        model.useCamera(world.camera.three);
        world.scene.three.add(model.object);
        fragments.core.update(true);
      });
      fragments.core.models.materials.list.onItemSet.add(({ value: material }: { value: any }) => {
        if (!('isLodMaterial' in material && material.isLodMaterial)) {
          material.polygonOffset = true;
          material.polygonOffsetUnits = 1;
          material.polygonOffsetFactor = 1;
        }
      });

      ifcLoader = components.get(OBC.IfcLoader);
      await ifcLoader.setup({
        autoSetWasm: false,
        wasm: {
          path: 'https://unpkg.com/web-ifc@0.0.77/',
          absolute: true,
        },
      });
    },

    async load(model: VivaIfcModelInput): Promise<void> {
      await this.clear();
      await ifcLoader.load(model.bytes, false, model.id, {
        userData: { name: model.name },
        processData: {
          progressCallback: () => undefined,
        },
      });
      await this.fitToModel();
    },

    async clear(): Promise<void> {
      if (!fragments?.list) {
        return;
      }
      for (const [modelId] of fragments.list) {
        fragments.core.disposeModel(modelId);
      }
      fragments.core.update(true);
    },

    async fitToModel(): Promise<void> {
      if (!world?.camera?.controls) {
        return;
      }
      await world.camera.controls.setLookAt(16, 12, 16, 0, 0, 0, true);
      fragments?.core?.update(true);
    },

    async dispose(): Promise<void> {
      await this.clear();
      fragments?.dispose?.();
      components?.dispose?.();
      components = undefined;
      world = undefined;
      fragments = undefined;
      ifcLoader = undefined;
    },
  };
}
