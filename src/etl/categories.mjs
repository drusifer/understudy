import { readFile } from 'node:fs/promises';
import { parse } from 'yaml';
import { RunError, UsageError } from '../errors.mjs';

export const MISC_CATEGORY = 'Misc';
export const MISC_SUBCATEGORY = 'Other or not yet classified';
export const DEFAULT_JEV_BATCH_SIZE = 5;
export const TAXONOMY_PATH = new URL('taxonomy.yaml', import.meta.url);

/**
 * Read the versioned decision list and reject malformed choice sets.
 */
export async function loadTaxonomy(file = TAXONOMY_PATH) {
  const taxonomy = parse(await readFile(file, 'utf8'));
  if (!taxonomy?.version || !Array.isArray(taxonomy.categories) || taxonomy.categories.length === 0) {
    throw new UsageError('Category taxonomy must include a version and categories.');
  }
  const keys = new Set();
  for (const category of taxonomy.categories) {
    if (!category.name || !Array.isArray(category.subcategories) || category.subcategories.length === 0) {
      throw new UsageError('Every taxonomy category must have a name and at least one subcategory.');
    }
    for (const subcategory of category.subcategories) {
      if (!subcategory.name || !subcategory.guidance) {
        throw new UsageError('Every taxonomy subcategory must have a name and guidance.');
      }
      const key = pairKey(category.name, subcategory.name);
      if (keys.has(key)) throw new UsageError(`Category taxonomy contains a duplicate option: ${key}`);
      keys.add(key);
    }
  }
  if (!keys.has(pairKey(MISC_CATEGORY, MISC_SUBCATEGORY))) {
    throw new UsageError(`Category taxonomy must include ${MISC_CATEGORY} / ${MISC_SUBCATEGORY}.`);
  }
  return taxonomy;
}

function pairKey(category, subcategory) {
  return `${category}::${subcategory}`;
}

function choiceSet(taxonomy) {
  const criteria = {};
  const pairs = new Map();
  for (const category of taxonomy.categories) {
    for (const subcategory of category.subcategories) {
      const key = pairKey(category.name, subcategory.name);
      criteria[key] = `${category.name} / ${subcategory.name}: ${subcategory.guidance}`;
      pairs.set(key, { category: category.name, subcategory: subcategory.name });
    }
  }
  return { criteria, pairs };
}

function distinctMerchants(candidates) {
  const merchants = new Map();
  for (const candidate of candidates) {
    const merchantKey = String(candidate.merchant_key ?? '').trim().toLowerCase();
    if (!merchantKey) continue;
    const existing = merchants.get(merchantKey);
    if (existing) {
      existing.transaction_count += Number(candidate.transaction_count) || 0;
    } else {
      merchants.set(merchantKey, {
        merchant_key: merchantKey,
        merchant: String(candidate.merchant ?? '').trim(),
        transaction_count: Number(candidate.transaction_count) || 0,
      });
    }
  }
  return merchants.values().toArray().toSorted((left, right) => left.merchant_key.localeCompare(right.merchant_key));
}

/**
 * Ask Jev about distinct merchants in bounded batches and validate every returned choice.
 */
export async function classifyMerchants({ candidates, taxonomy, judge, batchSize = DEFAULT_JEV_BATCH_SIZE, onBatchComplete }) {
  if (!Number.isSafeInteger(batchSize) || batchSize < 1) throw new UsageError('Jev batch size must be a positive whole number.');
  const merchants = distinctMerchants(candidates);
  const { criteria, pairs } = choiceSet(taxonomy);
  const mappings = [];
  for (let offset = 0; offset < merchants.length; offset += batchSize) {
    const batch = merchants.slice(offset, offset + batchSize);
    const batchStartedAt = Date.now();
    const state = { merchants: {} };
    const questions = {};
    const questionToMerchant = new Map();
    for (const [index, merchant] of batch.entries()) {
      const id = `merchant_${index + 1}`;
      state.merchants[id] = { descriptor: merchant.merchant, transaction_count: merchant.transaction_count };
      questions[id] = {
        type: 'choice',
        instructions: `Choose the single best category and subcategory for merchants.${id}. Use only an offered pair.`,
        criteria,
      };
      questionToMerchant.set(id, merchant);
    }

    let response;
    try {
      response = await judge.systemOne({ state, questions });
    } catch (error) {
      throw new RunError('Jev category request failed; this run is incomplete.', { cause: error });
    }
    for (const [id, merchant] of questionToMerchant) {
      const answer = response.answers?.[id];
      const pair = pairs.get(answer?.choice);
      const chosen = pair ?? pairs.get(pairKey(MISC_CATEGORY, MISC_SUBCATEGORY));
      mappings.push({
        merchant_key: merchant.merchant_key,
        merchant: merchant.merchant,
        category: chosen.category,
        subcategory: chosen.subcategory,
        classification_status: pair ? 'classified' : 'fallback_misc',
        confidence: Number.isFinite(answer?.confidence) ? answer.confidence : null,
        taxonomy_version: taxonomy.version,
        decision_model: response.model ?? null,
        review_required: !pair,
      });
    }
    await onBatchComplete?.({
      batch: Math.floor(offset / batchSize) + 1,
      total_batches: Math.ceil(merchants.length / batchSize),
      merchant_count: batch.length,
      duration_ms: Date.now() - batchStartedAt,
    });
  }
  return mappings;
}
