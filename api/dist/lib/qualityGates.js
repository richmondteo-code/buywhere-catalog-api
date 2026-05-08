"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isValidHttpUrl = isValidHttpUrl;
exports.isValidImageUrl = isValidImageUrl;
exports.gateG1_RequiredFields = gateG1_RequiredFields;
exports.gateG2_ValidUrl = gateG2_ValidUrl;
exports.gateG3_CanonicalCategory = gateG3_CanonicalCategory;
exports.gateG4_PriceSanity = gateG4_PriceSanity;
exports.gateG5_ImageAvailability = gateG5_ImageAvailability;
exports.gateG6_DuplicateSkipped = gateG6_DuplicateSkipped;
exports.calculateCompletenessScore = calculateCompletenessScore;
exports.buildQualityFlags = buildQualityFlags;
exports.runQualityGates = runQualityGates;
exports.gateResultsToIngestResult = gateResultsToIngestResult;
const CANONICAL_CATEGORIES = new Set([
    'Electronics', 'Fashion', 'Beauty', 'Home', 'Sports', 'Toys',
    'Grocery', 'Books', 'Stationery', 'Pet Supplies', 'Baby & Kids',
    'Health', 'Automotive', 'Garden', 'Office', 'Food & Beverage',
    'Uncategorized',
]);
const MAX_PRICE_BY_CATEGORY = {
    Electronics: 100000,
    Fashion: 10000,
    Beauty: 5000,
    Home: 50000,
    Sports: 20000,
    Toys: 5000,
    Grocery: 5000,
    Books: 1000,
    Stationery: 1000,
    'Pet Supplies': 5000,
    'Baby & Kids': 5000,
    Health: 10000,
    Automotive: 100000,
    Garden: 20000,
    Office: 5000,
    'Food & Beverage': 5000,
    Uncategorized: 1000000,
};
function isValidHttpUrl(url) {
    try {
        const parsed = new URL(url);
        return parsed.protocol === 'http:' || parsed.protocol === 'https:';
    }
    catch {
        return false;
    }
}
function isValidImageUrl(url) {
    if (!url)
        return false;
    try {
        const parsed = new URL(url);
        return ['http:', 'https:'].includes(parsed.protocol);
    }
    catch {
        return false;
    }
}
function gateG1_RequiredFields(title, price, url) {
    const missing = [];
    if (!title || String(title).trim() === '')
        missing.push('title');
    if (price === undefined || price === null)
        missing.push('price');
    if (!url || String(url).trim() === '')
        missing.push('url');
    if (missing.length > 0) {
        return {
            passed: false,
            gate: 'G1',
            message: `Missing required fields: ${missing.join(', ')}`,
            severity: 'error',
        };
    }
    return { passed: true, gate: 'G1', severity: 'info' };
}
function gateG2_ValidUrl(url) {
    if (!url || !isValidHttpUrl(url)) {
        return {
            passed: false,
            gate: 'G2',
            message: 'product_url is not a valid HTTP(S) URL',
            severity: 'error',
        };
    }
    return { passed: true, gate: 'G2', severity: 'info' };
}
function gateG3_CanonicalCategory(category) {
    if (!category) {
        return {
            passed: true,
            gate: 'G3',
            message: 'No category provided (will route to Uncategorized)',
            severity: 'warning',
        };
    }
    if (!CANONICAL_CATEGORIES.has(category)) {
        return {
            passed: true,
            gate: 'G3',
            message: `Category "${category}" not in canonical vocabulary`,
            severity: 'warning',
        };
    }
    return { passed: true, gate: 'G3', severity: 'info' };
}
function gateG4_PriceSanity(price, category) {
    if (price === undefined || price === null) {
        return { passed: true, gate: 'G4', severity: 'info' };
    }
    if (price <= 0) {
        return {
            passed: false,
            gate: 'G4',
            message: 'Price must be > 0',
            severity: 'error',
        };
    }
    const maxPrice = category ? (MAX_PRICE_BY_CATEGORY[category] || 100000) : 100000;
    if (price > maxPrice) {
        return {
            passed: true,
            gate: 'G4',
            message: `Price ${price} exceeds category max ${maxPrice}`,
            severity: 'warning',
        };
    }
    return { passed: true, gate: 'G4', severity: 'info' };
}
async function gateG5_ImageAvailability(imageUrl) {
    if (!imageUrl) {
        return {
            passed: true,
            gate: 'G5',
            message: 'No image_url provided',
            severity: 'info',
        };
    }
    if (!isValidImageUrl(imageUrl)) {
        return {
            passed: true,
            gate: 'G5',
            message: 'image_url is not a valid HTTP(S) URL',
            severity: 'warning',
        };
    }
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        const response = await fetch(imageUrl, {
            method: 'HEAD',
            signal: controller.signal,
            redirect: 'follow',
        });
        clearTimeout(timeout);
        if (response.ok) {
            return { passed: true, gate: 'G5', severity: 'info' };
        }
        return {
            passed: true,
            gate: 'G5',
            message: `image_url returned HTTP ${response.status}`,
            severity: 'warning',
        };
    }
    catch {
        return {
            passed: true,
            gate: 'G5',
            message: 'image_url not accessible (fetch failed)',
            severity: 'warning',
        };
    }
}
function gateG6_DuplicateSkipped(isExistingSku) {
    if (isExistingSku) {
        return {
            passed: true,
            gate: 'G6',
            message: 'SKU already exists, will update',
            severity: 'info',
        };
    }
    return { passed: true, gate: 'G6', severity: 'info' };
}
function calculateCompletenessScore(product, p0Fields = ['title', 'price', 'url', 'currency'], p1Fields = ['image_url', 'category', 'merchant_id'], p2Fields = ['description', 'brand']) {
    let score = 0;
    const allFields = [...p0Fields, ...p1Fields, ...p2Fields];
    for (const field of allFields) {
        const value = product[field];
        if (value !== undefined && value !== null && value !== '') {
            if (p0Fields.includes(field)) {
                score += 40;
            }
            else if (p1Fields.includes(field)) {
                score += 35;
            }
            else {
                score += 25;
            }
        }
    }
    return Math.min(100, score);
}
function buildQualityFlags(results, completenessScore) {
    const flags = {
        g1_required_fields: true,
        g2_valid_url: true,
        g3_canonical_category: true,
        g4_price_sanity: true,
        g5_image_available: null,
        g6_duplicate_skipped: false,
        completeness_score: completenessScore,
    };
    for (const r of results) {
        if (!r.passed) {
            if (r.gate === 'G1')
                flags.g1_required_fields = false;
            if (r.gate === 'G2')
                flags.g2_valid_url = false;
            if (r.gate === 'G3')
                flags.g3_canonical_category = false;
            if (r.gate === 'G4')
                flags.g4_price_sanity = false;
        }
        if (r.gate === 'G5') {
            flags.g5_image_available = r.passed ? true : false;
        }
        if (r.gate === 'G6') {
            flags.g6_duplicate_skipped = !r.passed;
        }
    }
    return flags;
}
async function runQualityGates(product, existingSku = false) {
    const results = [];
    results.push(gateG1_RequiredFields(product.title, product.price, product.url));
    results.push(gateG2_ValidUrl(product.url));
    results.push(gateG3_CanonicalCategory(product.category));
    results.push(gateG4_PriceSanity(product.price, product.category));
    const g5Result = await gateG5_ImageAvailability(product.image_url);
    results.push(g5Result);
    results.push(gateG6_DuplicateSkipped(existingSku));
    const completenessScore = calculateCompletenessScore(product);
    const flags = buildQualityFlags(results, completenessScore);
    return { results, flags };
}
function gateResultsToIngestResult(results) {
    const rejected = results.some(r => !r.passed && r.severity === 'error');
    const errors = results
        .filter(r => !r.passed && r.severity === 'error')
        .map(r => ({ gate: r.gate, message: r.message || '' }));
    const warnings = results
        .filter(r => !r.passed && r.severity === 'warning')
        .map(r => ({ gate: r.gate, message: r.message || '' }));
    return { rejected, errors, warnings };
}
