---
title: "What Is a Price Graph? — Developer FAQ"
slug: "what-is-a-price-graph"
description: "FAQ explaining what a price graph is in e-commerce and price intelligence. Covers graph-based price relationships, product similarity networks, retailer relationship graphs, and how BuyWhere uses price graphs."
category: FAQ
tags:
  - "price graph"
  - "product relationship graph"
  - "price intelligence"
  - "product similarity graph"
  - "retailer graph"
  - "graph-based pricing"
  - "e-commerce graph"
schema_type: Article
published: true
updated: 2026-05-08
---

# What Is a Price Graph? — Developer FAQ

A price graph is a graph data structure that models the relationships between products, retailers, and prices in an e-commerce ecosystem. This FAQ covers what price graphs are, how they work, and how BuyWhere uses them for price intelligence.

---

## What Is a Price Graph?

A price graph is a network representation of products, retailers, and their price relationships. Instead of storing price data in flat tables, a price graph captures the connections between entities:

```
Nodes:
- Products (canonical products)
- Retailers
- Categories
- Brands

Edges:
- Product → Product: substitute relationships (same use case)
- Product → Retailer: retailer carries this product
- Retailer → Retailer: competitive relationship
- Product → Category: product belongs to category
- Product → Brand: product belongs to brand
```

The graph structure enables reasoning about price relationships that are difficult to express in tabular data.

---

## Graph Data Structure Basics

### Nodes and Edges

A graph consists of:

| Element | Description |
|---------|-------------|
| **Node (Vertex)** | An entity — a product, retailer, category, or brand |
| **Edge** | A relationship between two nodes |
| **Edge Weight** | Strength of relationship (e.g., similarity score, price difference) |
| **Direction** | Directed edges (A → B) or undirected (A — B) |

### Example Price Graph

```
                    ┌─────────────┐
                    │   Sony      │ ← Brand node
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │ WH-1000XM5  │ ← Product node
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ Amazon  │      │ Best Buy│      │ Walmart │
    │  $299   │      │  $312   │      │  $329   │
    └─────────┘      └─────────┘      └─────────┘
```

---

## Types of Price Graphs

### 1. Product Substitutability Graph

Models which products are substitutes for each other:

```
Edge: Product A — Product B
Edge weight: Substitutability score (how often buyers purchase one instead of the other)
```

This graph answers: "What is the substitute for Product X?"

### 2. Retailer Competition Graph

Models competitive relationships between retailers:

```
Edge: Retailer A — Retailer B
Edge weight: Overlap in product assortment (Jaccard similarity of SKUs)
```

This graph identifies which retailers compete most directly with each other.

### 3. Product Similarity Graph

Models similarity between products based on attributes:

```
Edge: Product A — Product B
Edge weight: Similarity score (based on brand, category, price range, attributes)
```

This graph enables "products similar to X" recommendations.

### 4. Price Movement Correlation Graph

Models how product prices move together:

```
Edge: Product A — Product B
Edge weight: Price correlation (do they tend to change price together?)
```

This graph identifies products affected by the same market forces.

---

## How Is a Price Graph Built?

### Node Creation

Nodes are created from canonical product data:

```
For each canonical product:
  Create a product node with attributes:
    - brand
    - category
    - price range
    - price corridor (floor, ceiling)
```

### Edge Creation

Edges are created through analysis:

| Edge Type | Creation Method |
|-----------|----------------|
| Substitutability | Co-purchase analysis (buyers who bought X also bought Y) |
| Similarity | Attribute matching (same brand, category, price range) |
| Competition | Assortment overlap (Jaccard similarity of retailer SKUs) |
| Price correlation | Time-series correlation of price movements |

### Graph Storage

Price graphs are stored in graph databases:

| Database | Use Case |
|----------|----------|
| **Neo4j** | General-purpose graph database |
| **Amazon Neptune** | Managed graph database |
| **RedisGraph** | Graph in Redis |
| **pgGraph** | Graph extension for PostgreSQL |

---

## What Can You Do with a Price Graph?

### 1. Substitute Product Identification

Find substitutes for a product:

```
Given: Product X
Query: Find all products connected to X with substitutability edges
Result: List of substitute products with substitutability scores
```

### 2. Competitive Retailer Analysis

Identify which retailers compete most directly:

```
Given: Retailer A
Query: Find retailers with highest assortment overlap with A
Result: Ranked list of direct competitors
```

### 3. Price Propagation Analysis

Understand how price changes propagate:

```
Event: Competitor X drops price on Product A
Query: Find all products connected to A (substitutes, competitors)
Result: Products likely to be affected by the price change
```

### 4. Assortment Gap Detection

Find product gaps in a retailer's assortment:

```
Given: Retailer A's assortment
Query: Find products in competitor assortments but not in A's assortment,
       where substitutability score to A's products is high
Result: Product gaps worth filling
```

### 5. Price Fairness Analysis

Evaluate whether a price is fair using substitute relationships:

```
Given: Product A at price P at Retailer X
Query: Find average price of substitutes to A
Result: Is P above or below substitute average?
```

---

## Price Graph and Price Intelligence

The price graph enables intelligence that flat data cannot easily provide:

### Competitive Price Response

When a competitor drops a price, the graph identifies affected products:

```
1. Competitor drops price on Product A
2. Graph query: Find products connected to A (substitutes)
3. For each substitute product:
   - Find its retailers
   - Calculate impact of A's price drop
4. Generate competitive response recommendations
```

### Market Structure Analysis

The graph reveals market structure:

```
Connected components: Products that cluster together (substitutes)
Bridge products: Connect different clusters (cross-category)
Isolated products: Few substitutes (unique market position)
```

### Price Monitoring Prioritisation

Products in the graph are prioritised by their centrality:

```
Central products: Many substitutes, many competitors — high monitoring priority
Peripheral products: Few connections — lower monitoring priority
```

---

## What Is a Product Similarity Graph?

A product similarity graph connects products that share attributes or are frequently purchased together:

### Similarity Signals

| Signal | Description |
|--------|-------------|
| **Co-purchase** | Products frequently bought together |
| **Attribute similarity** | Same brand, category, price range |
| **Title similarity** | Similar product names |
| **Image similarity** | Visually similar products |
| **Review similarity** | Similar review patterns |

### Graph Construction

```
For each pair of products (A, B):
  Calculate similarity score from multiple signals
  If similarity > threshold:
    Create edge: A — B with weight = similarity
```

### Applications

- **"Customers who viewed this also viewed..."** recommendations
- **Competitive pricing**: Understand pricing pressure from similar products
- **Substitute identification**: Find products that can replace each other

---

## What Is a Retailer Relationship Graph?

A retailer relationship graph models how retailers relate to each other:

### Retailer-Relationship Types

| Relationship | Edge Type | Weight |
|-------------|-----------|--------|
| **Direct competition** | Undirected | Assortment overlap (Jaccard) |
| **Price leadership** | Directed | Price change causation |
| **Channel relationship** | Directed | Supplier → Retailer |

### Direct Competition Graph

```
For each pair of retailers (A, B):
  Calculate assortment overlap: |A ∩ B| / |A ∪ B|
  If overlap > threshold:
    Create edge: A — B with weight = overlap
```

### Price Leadership

Some retailers (market leaders) influence others:

```
When market leader raises price:
  - Followers may also raise price (if price elastic)
  - The graph models this directional influence
```

---

## BuyWhere's Use of Price Graphs

BuyWhere uses price graphs for several intelligence applications:

### Substitute Product Resolution

When matching products across retailers, substitutes help resolve ambiguity:

```
Product: "Sony WH-1000XM5"
Query: Find substitute products
Result: Bose QC45, Apple AirPods Max, Sennheiser HD 660S

These substitutes provide context for whether a price is competitive.
```

### Competitive Intelligence

Retailer relationship graph identifies direct competitors:

```
For Retailer X:
  Query: Retailers with highest assortment overlap
  Result: Ranked list of direct competitors for targeted monitoring
```

### Price Anomaly Detection

Graph-connected products show correlated price movements:

```
Normal: Products in same cluster have correlated prices
Anomaly: Product price deviates from cluster average without explanation
Signal: Possible pricing error or competitor price manipulation
```

---

## Graph Query Examples

### Find Substitutes

```graphql
{
  product(id: "PRD-SONY-WH1000XM5-BLK") {
    substitutes(first: 5) {
      product { name }
      score
    }
  }
}
```

### Find Direct Competitors

```graphql
{
  retailer(id: "retailer-amazon") {
    competitors(first: 5) {
      retailer { name }
      overlap
    }
  }
}
```

### Price Impact Analysis

```graphql
{
  product(id: "PRD-SONY-WH1000XM5-BLK") {
    priceDropAt(retailer: "Amazon") {
      affectedProducts {
        product { name }
        estimatedImpact
      }
    }
  }
}
```

---

## Limitations of Price Graphs

### 1. Graph Sparsity

Not all products have substitute relationships in the graph. New products, niche products, and unique products may have few or no connections.

### 2. Dynamic Graph Changes

Product assortments change constantly. The graph can become stale quickly without regular updates.

### 3. Similarity vs. Substitutability

Products that are similar are not always substitutes. A $500 headphone and a $50 headphone may be similar but not substitutable (different buyer segments).

### 4. Computational Cost

Graph algorithms are computationally expensive at scale. A graph with millions of products and billions of edges requires significant infrastructure.

---

## Related Questions

- [What Is Competitive Price Intelligence](/pages/what-is-competitive-price-intelligence)
- [What Is a Price Benchmark](/pages/what-is-a-price-benchmark)
- [What Is Product Matching](/pages/what-is-product-matching)
- [What Is a Product Taxonomy](/pages/what-is-product-taxonomy)
