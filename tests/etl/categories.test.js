import test from 'node:test';
import assert from 'node:assert/strict';
import { classifyMerchants, loadTaxonomy, MISC_CATEGORY, MISC_SUBCATEGORY } from '../../src/etl/categories.mjs';

test('taxonomy provides the required category and subcategory choices with Misc fallback', async () => {
  const taxonomy = await loadTaxonomy();
  const options = taxonomy.categories.flatMap((category) => category.subcategories.map((subcategory) => `${category.name}::${subcategory.name}`));
  assert.equal(taxonomy.version, 'household-transactions-v1');
  assert.ok(options.includes(`${MISC_CATEGORY}::${MISC_SUBCATEGORY}`));
  assert.ok(options.includes('Food & Dining::Groceries'));
  assert.ok(options.includes('Transportation::Rideshare'));
  assert.ok(options.includes('Personal & Family::Childcare'));
  assert.ok(options.length > 40, 'taxonomy should provide a rich bounded set of options');
});

test('classifies distinct merchants in bounded batches and routes invalid choices to Misc for review', async () => {
  const taxonomy = await loadTaxonomy();
  const calls = [];
  const judge = {
    async systemOne(request) {
      calls.push(request);
      const ids = Object.keys(request.questions);
      const choices = calls.length === 1
        ? ['Food & Dining::Coffee', 'Transportation::Fuel']
        : ['made-up-category'];
      return {
        model: 'scripted',
        answers: Object.fromEntries(ids.map((id, index) => [id, { choice: choices[index], confidence: 0.91 }])),
      };
    },
  };
  const mappings = await classifyMerchants({
    taxonomy,
    judge,
    batchSize: 2,
    candidates: [
      { merchant_key: 'coffee shop', merchant: 'Coffee Shop', transaction_count: 2 },
      { merchant_key: 'fuel stop', merchant: 'Fuel Stop', transaction_count: 1 },
      { merchant_key: 'coffee shop', merchant: 'COFFEE SHOP', transaction_count: 3 },
      { merchant_key: 'unknown merchant', merchant: 'Unknown Merchant', transaction_count: 1 },
    ],
  });

  assert.equal(calls.length, 2, 'three distinct merchant keys require two requests at batch size two');
  assert.equal(Object.keys(calls[0].questions).length, 2);
  assert.equal(calls[0].state.merchants.merchant_1.transaction_count, 5, 'duplicate merchant rows are presented once with their combined count');
  assert.equal(mappings.length, 3);
  assert.deepEqual(mappings.map(({ category, subcategory, classification_status, review_required }) => ({ category, subcategory, classification_status, review_required })), [
    { category: 'Food & Dining', subcategory: 'Coffee', classification_status: 'classified', review_required: false },
    { category: 'Transportation', subcategory: 'Fuel', classification_status: 'classified', review_required: false },
    { category: MISC_CATEGORY, subcategory: MISC_SUBCATEGORY, classification_status: 'fallback_misc', review_required: true },
  ]);
});

test('an empty Jev answer uses Misc and marks the decision for review', async () => {
  const taxonomy = await loadTaxonomy();
  const mappings = await classifyMerchants({
    taxonomy,
    candidates: [{ merchant_key: 'shop', merchant: 'Shop', transaction_count: 1 }],
    judge: { async systemOne() { return { answers: {} }; } },
  });
  assert.equal(mappings[0].category, MISC_CATEGORY);
  assert.equal(mappings[0].subcategory, MISC_SUBCATEGORY);
  assert.equal(mappings[0].review_required, true);
});

test('Jev service failures fail the category stage instead of silently classifying everything Misc', async () => {
  const taxonomy = await loadTaxonomy();
  await assert.rejects(classifyMerchants({
    taxonomy,
    candidates: [{ merchant_key: 'shop', merchant: 'Shop', transaction_count: 1 }],
    judge: { async systemOne() { throw new Error('offline'); } },
  }), /Jev category request failed/);
});
