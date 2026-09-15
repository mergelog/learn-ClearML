import {defineConfig} from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: [
      'src/app/webapp-common/experiments/containers/experiment-info-execution/execution-requirements-state.spec.ts'
    ]
  }
});
