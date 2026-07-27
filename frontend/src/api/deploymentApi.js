/**
 * deploymentApi.js
 * Re-exports real API functions from executionApi.js.
 * Strict zero-mock governance policy.
 */
export {
  getExecutionDbHealth,
  getDeployments,
  getDeploymentById,
  pauseExecution,
  stopExecution,
} from './executionApi';
