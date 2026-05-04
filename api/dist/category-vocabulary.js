"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CANONICAL_CATEGORIES = void 0;
exports.isValidSlug = isValidSlug;
exports.resolveSlug = resolveSlug;
exports.CANONICAL_CATEGORIES = [
    'electronics',
    'fashion',
    'home-living',
    'beauty',
    'sports-outdoors',
    'groceries',
    'baby-kids',
    'automotive',
    'books-media',
    'health-wellness',
    'pets',
    'office-stationery',
];
const CATEGORY_SET = new Set(exports.CANONICAL_CATEGORIES);
const LEGACY_ALIASES = {
    'health-beauty': 'beauty',
    'kids-baby': 'baby-kids',
    'pet-supplies': 'pets',
    'office': 'office-stationery',
    'books': 'books-media',
    'media': 'books-media',
    'health': 'health-wellness',
    'wellness': 'health-wellness',
    'home': 'home-living',
    'sports': 'sports-outdoors',
    'baby': 'baby-kids',
};
function isValidSlug(slug) {
    const resolved = LEGACY_ALIASES[slug] ?? slug;
    return CATEGORY_SET.has(resolved);
}
function resolveSlug(slug) {
    const resolved = LEGACY_ALIASES[slug] ?? slug;
    if (CATEGORY_SET.has(resolved)) {
        return resolved;
    }
    return null;
}
