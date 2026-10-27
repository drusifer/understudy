import { RunError, UsageError } from './errors.mjs';

const API_KEY = 'TYPESAFE_API_KEY';

/**
 * Create the shared TypeSafe client used by both sketches and ETL judgments.
 */
export async function createJevJudge(environment) {
  const { TypeSafeClient } = await import('@typesafe-ai/sdk');
  try {
    return new TypeSafeClient({ apiKey: environment[API_KEY] });
  } catch (error) {
    throw new UsageError(`Jev could not be set up: ${error.message}`);
  }
}

/**
 * Convert SDK failures to the run-level failure used by Understudy.
 */
export function reportJevFailures(judge) {
  return {
    async systemOne(request) {
      try {
        return await judge.systemOne(request);
      } catch (error) {
        throw new RunError(`Jev request failed: ${error.message}`, { outcome: 'jev-error', cause: error });
      }
    },
  };
}
