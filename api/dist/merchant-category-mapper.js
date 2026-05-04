"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.mapToCanonical = mapToCanonical;
const category_vocabulary_1 = require("./category-vocabulary");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const KEYWORD_PATTERNS = [
    { canonical: 'electronics', keywords: ['phone', 'laptop', 'tablet', 'camera', 'audio', 'headphone', 'wearable', 'tv', 'computer', 'gadget', 'tech', 'electronic', 'drone', 'charger', 'cable', 'speaker', 'monitor', 'keyboard', 'mouse', 'printer', 'hard drive', 'ssd', 'ram', 'graphics'] },
    { canonical: 'fashion', keywords: ['clothing', 'apparel', 'shoe', 'bag', 'jewelry', 'watch', 'accessory', 'dress', 'shirt', 'pant', 'jean', 'fashion', 'wear', 'sneaker', 'boot', 'sandals', 't-shirt', 'jacket', 'coat', 'suit', 'tie', 'scarf', 'hat', 'belt', 'wallet', 'sunglasses'] },
    { canonical: 'home-living', keywords: ['furniture', 'decor', 'kitchen', 'bedding', 'bath', 'lighting', 'home', 'garden', 'furnish', 'couch', 'sofa', 'table', 'chair', 'cabinet', 'shelf', 'curtain', 'towel', 'linen', 'pillow', 'blanket', 'rug', 'lamp', 'mirror', 'vase', 'plant'] },
    { canonical: 'beauty', keywords: ['skincare', 'makeup', 'cosmetic', 'haircare', 'fragrance', 'beauty', 'nail', 'lipstick', 'moisturizer', 'serum', 'sunscreen', 'foundation', 'mascara', 'eyeshadow', 'shampoo', 'conditioner', 'deodorant', 'lotion', 'cream', 'face wash'] },
    { canonical: 'sports-outdoors', keywords: ['sport', 'fitness', 'gym', 'camping', 'hiking', 'cycling', 'outdoor', 'exercise', 'yoga', 'athletic', 'bike', 'tent', 'backpack', 'treadmill', 'dumbbell', 'barbell', 'mat', 'helmet', 'racket', 'ball', 'swim'] },
    { canonical: 'groceries', keywords: ['food', 'beverage', 'snack', 'grocery', 'drink', 'fresh', 'frozen', 'dairy', 'bread', 'rice', 'oil', 'sauce', 'spice', 'cereal', 'pasta', 'noodle', 'canned', 'organic', 'coffee', 'tea', 'juice', 'water', 'milk', 'egg', 'butter', 'cheese', 'yogurt'] },
    { canonical: 'baby-kids', keywords: ['baby', 'kids', 'toy', 'diaper', 'stroller', 'crib', 'infant', 'toddler', 'children', 'play', 'car seat', 'bottle', 'pacifier', 'baby wipe', 'nursery', 'playpen', 'high chair'] },
    { canonical: 'automotive', keywords: ['car', 'automotive', 'motor', 'tire', 'oil', 'battery', 'auto', 'vehicle', 'garage', 'detailing', 'windshield', 'brake', 'engine', 'transmission', 'exhaust', 'motorcycle', 'scooter', 'helmet'] },
    { canonical: 'books-media', keywords: ['book', 'magazine', 'music', 'movie', 'dvd', 'cd', 'vinyl', 'audiobook', 'comic', 'novel', 'ebook', 'textbook', 'journal', 'manga', 'blu-ray', 'video game'] },
    { canonical: 'health-wellness', keywords: ['vitamin', 'supplement', 'health', 'wellness', 'medical', 'personal care', 'first aid', 'fitness tracker', 'protein', 'mineral', 'herbal', 'probiotic', 'mask', 'hand sanitizer', 'thermometer', 'blood pressure'] },
    { canonical: 'pets', keywords: ['pet', 'dog', 'cat', 'fish', 'bird', 'aquarium', 'pet food', 'pet toy', 'pet bed', 'leash', 'collar', 'litter', 'aquarium', 'hamster', 'reptile', 'turtle'] },
    { canonical: 'office-stationery', keywords: ['office', 'stationery', 'printer', 'paper', 'pen', 'pencil', 'desk', 'filing', 'shipping', 'envelope', 'marker', 'notebook', 'binder', 'stapler', 'tape', 'scissors', 'calculator', 'folder'] },
];
const CONFIG_BASE = path.resolve(__dirname, '../../config');
const merchantMappingCache = new Map();
function loadMappingFile(merchant) {
    if (merchantMappingCache.has(merchant)) {
        return merchantMappingCache.get(merchant);
    }
    const merchantToFile = {
        lazada: 'category-mapping-lazada-sg.json',
        shopee: 'category-mapping-shopee-sg.json',
        amazon_sg: 'category-mapping-amazon-sg.json',
        'amazon-sg': 'category-mapping-amazon-sg.json',
    };
    const filename = merchantToFile[merchant];
    if (!filename) {
        merchantMappingCache.set(merchant, []);
        return [];
    }
    try {
        const filePath = path.join(CONFIG_BASE, filename);
        const content = fs.readFileSync(filePath, 'utf-8');
        const data = JSON.parse(content);
        merchantMappingCache.set(merchant, data.mappings);
        return data.mappings;
    }
    catch {
        merchantMappingCache.set(merchant, []);
        return [];
    }
}
function keywordScore(merchantCat, pattern) {
    const lower = merchantCat.toLowerCase();
    let score = 0;
    for (const kw of pattern.keywords) {
        if (lower.includes(kw)) {
            score++;
        }
    }
    return score;
}
function mapToCanonical(merchant, merchantCategory) {
    if (!merchantCategory)
        return 'uncategorized';
    // 1. Try exact match from mapping file
    const mappings = loadMappingFile(merchant);
    const lowerMerchantCat = merchantCategory.toLowerCase().trim();
    const exactMatch = mappings.find(m => m.merchant_cat.toLowerCase() === lowerMerchantCat);
    if (exactMatch) {
        const resolved = (0, category_vocabulary_1.resolveSlug)(exactMatch.canonical);
        if (resolved)
            return resolved;
    }
    // 2. Try partial match from mapping file
    const partialMatch = mappings.find(m => lowerMerchantCat.includes(m.merchant_cat.toLowerCase()) ||
        m.merchant_cat.toLowerCase().includes(lowerMerchantCat));
    if (partialMatch) {
        const resolved = (0, category_vocabulary_1.resolveSlug)(partialMatch.canonical);
        if (resolved)
            return resolved;
    }
    // 3. Keyword scoring fallback
    let bestScore = 0;
    let bestMatch = null;
    for (const pattern of KEYWORD_PATTERNS) {
        const score = keywordScore(merchantCategory, pattern);
        if (score > bestScore || (score === bestScore && score > 0 && bestMatch === null)) {
            bestScore = score;
            bestMatch = pattern.canonical;
        }
    }
    if (bestMatch && bestScore > 0) {
        return bestMatch;
    }
    return 'uncategorized';
}
