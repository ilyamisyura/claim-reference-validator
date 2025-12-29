import { defineConfig } from 'orval';

const FILTERS = {
  mode: 'exclude' as const,
  tags: ['internal'],
};

// Keep only paths starting with a given prefix, e.g. /api/v1
const versionTransformer = (prefix: string) => (doc: any) => {
  const newPaths: Record<string, any> = {};

  for (const [path, pathItem] of Object.entries(doc.paths ?? {})) {
    if (path.startsWith(prefix)) {
      newPaths[path] = pathItem;
    }
  }

  return {
    ...doc,
    paths: newPaths,
  };
};

export default defineConfig({
  // =======================
  // v1: TS client + TS models
  // =======================
  v1: {
    input: {
      target: 'http://localhost:8000/openapi.json',
      filters: FILTERS,
      override: {
        transformer: versionTransformer('/api/v1'),
      },
    },
    output: {
      client: 'vue-query',
      mode: 'tags',
      target: 'lib/api/v1/endpoints',
      schemas: 'lib/api/v1/models',
      prettier: true,
      clean: true,
    },
  },

  // =======================
  // v1: Zod schemas
  // =======================
  v1Zod: {
    input: {
      target: 'http://localhost:8000/openapi.json',
      filters: FILTERS,
      override: {
        transformer: versionTransformer('/api/v1'),
      },
    },
    output: {
      client: 'zod',
      mode: 'tags',
      target: 'lib/api/v1/zod',
      prettier: true,
      clean: true,
    },
  },
});
