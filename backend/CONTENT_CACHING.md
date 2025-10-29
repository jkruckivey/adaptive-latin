# Content Caching System

## Overview

The content caching system dramatically reduces AI generation costs by intelligently reusing content. It implements a **hybrid waterfall approach**:

1. **Pre-generated content** (FREE, instant) - Created ahead of time
2. **Cached content** (FREE, instant) - Previously generated and proven effective
3. **Fresh AI generation** (COSTS $$$, slow) - Only when needed

## Architecture

### Components

```
content_cache.py         - Core caching logic and database operations
smart_content_retrieval.py  - Waterfall retrieval logic
content_cache_schema.sql    - SQLite database schema
pregenerate_content.py      - Script to pre-generate content
```

### Database Schema

**content_cache table**:
- Stores all generated content with tags
- Tracks usage count and effectiveness score
- Enables intelligent retrieval

**content_usage table**:
- Tracks when content is shown to learners
- Records outcomes (did learner succeed after viewing?)
- Calculates effectiveness metrics

## Cost Savings

**Before caching**:
- 100 learners × 7 concepts × 10 AI calls = 7,000 calls
- At $0.015/call = **$105 per 100 learners**

**After caching**:
- Pre-gen covers 30%: 2,100 calls → FREE
- Cache covers 50%: 3,500 calls → FREE
- Only 20% fresh: 1,400 calls → $21
- **Total: $21 per 100 learners (80% savings)**

## Usage

### 1. Pre-Generate Content

Run the pre-generation script to create initial content:

```bash
# Pre-generate for all concepts
python -m backend.scripts.pregenerate_content --course latin-grammar --concepts all

# Pre-generate for specific concepts
python -m backend.scripts.pregenerate_content --course latin-grammar --concepts concept-001,concept-002

# Dry run (see plan without generating)
python -m backend.scripts.pregenerate_content --course latin-grammar --concepts all --dry-run
```

This generates 4 explanations per concept (one for each learning style):
- Visual learners
- Reading learners
- Dialogue learners
- Kinesthetic learners

**Cost**: ~$0.015 × 4 learning styles × 7 concepts = ~$0.42 one-time

### 2. Use Smart Content Retrieval

In your application code:

```python
from backend.app.smart_content_retrieval import get_smart_content

# Get content with automatic caching
result = get_smart_content(
    learner_id="learner-123",
    concept_id="concept-001",
    course_id="latin-grammar",
    stage="start",
    learning_style="visual"
)

if result["success"]:
    content = result["content"]
    source = result["source"]  # "pre-generated", "cache", or "fresh-ai"
    cost = result["cost"]  # 0.0 for cached, 0.015 for fresh

    print(f"Content from: {source} (cost: ${cost})")
```

### 3. Track Effectiveness

When you know if content was effective:

```python
from backend.app.content_cache import update_content_effectiveness

# After learner completes assessment
update_content_effectiveness(
    usage_id=result["usage_id"],  # From get_smart_content response
    was_effective=True,  # Did learner pass after viewing?
    learner_score=0.92,
    time_to_mastery=2.5  # Hours
)
```

The system automatically:
- Updates effectiveness scores
- Adjusts cache hit rates
- Removes ineffective content from rotation

### 4. Monitor Cache Performance

View statistics:

```bash
# Via API
curl http://localhost:8000/cache/stats

# With course filter
curl http://localhost:8000/cache/stats?course_id=latin-grammar
```

Returns:

```json
{
  "success": true,
  "stats": {
    "total_cached_items": 156,
    "average_usage_per_item": 8.3,
    "average_effectiveness": 0.84,
    "total_cache_hits": 1,294,
    "estimated_cost_savings": "$19.41"
  }
}
```

## Content Library Structure

```
resource-bank/
  latin-grammar/
    concept-001/
      content-library/          ← NEW
        explanations/
          visual.json           ← Pre-generated
          reading.json          ← Pre-generated
          dialogue.json         ← Pre-generated
          kinesthetic.json      ← Pre-generated
        questions/
          question-bank.json    ← Future: reusable questions
        examples/
          examples-bank.json    ← Future: reusable examples
```

## Effectiveness Scoring

Content effectiveness is calculated based on learner outcomes:

```python
# Raw success rate
success_rate = successful_outcomes / total_uses

# Confidence factor (more data = more confidence)
confidence = min(1.0, total_uses / 10.0)

# Final score (weighted by confidence)
effectiveness_score = (success_rate × confidence) + (0.5 × (1 - confidence))
```

- New content starts at 0.5 effectiveness
- Score improves with positive outcomes
- Requires 10+ uses for full confidence
- Content below 0.6 is not reused

## Cache Strategy

### When to Use Pre-generated
- ✅ Initial explanations (stage="start")
- ✅ Standard content (no mistakes/remediation)
- ❌ Personalized remediation
- ❌ Specific error responses

### When to Use Cache
- ✅ Common learning paths
- ✅ Proven effective content (0.7+ score)
- ✅ Standard assessments
- ❌ Novel situations
- ❌ Edge cases

### When to Generate Fresh
- ✅ First encounter of rare combination
- ✅ Highly personalized interventions
- ✅ Cache miss with no good match
- ✅ Complex multi-step reasoning
- ✅ User explicitly requests variation

## Advanced: Cache Warming

For production, pre-warm cache with common paths:

```python
from backend.app.smart_content_retrieval import get_smart_content

# Simulate common learning paths
learning_styles = ["visual", "reading", "dialogue", "kinesthetic"]
concepts = ["concept-001", "concept-002", "concept-003"]

for concept_id in concepts:
    for style in learning_styles:
        get_smart_content(
            learner_id=f"cache-warm-{style}",
            concept_id=concept_id,
            course_id="latin-grammar",
            stage="start",
            learning_style=style
        )
```

## Monitoring

### Key Metrics

1. **Cache Hit Rate**: % of requests served from cache
   - Target: 70%+ after warmup

2. **Average Effectiveness**: Quality of cached content
   - Target: 0.75+

3. **Cost Per Learner**: Total AI costs / learners
   - Target: <$0.25 per learner

4. **Cache Size**: Total cached items
   - Monitor: Keep below 10,000 items

### Alerts

Set up alerts for:
- Cache hit rate <50% (too many misses)
- Average effectiveness <0.70 (low quality)
- Cache size >10,000 (cleanup needed)

## Maintenance

### Pruning Old Content

```sql
-- Remove rarely used, low effectiveness content
DELETE FROM content_cache
WHERE usage_count < 3
AND effectiveness_score < 0.5
AND created_at < datetime('now', '-30 days');
```

### Refreshing Content

Periodically regenerate content for concepts with updates:

```bash
python -m backend.scripts.pregenerate_content \
  --course latin-grammar \
  --concepts concept-001 \
  --force-refresh
```

## Troubleshooting

### Cache Not Working

1. Check database exists: `ls -la backend/content_cache.db`
2. Check initialization logs: Look for "Content cache database initialized"
3. Verify permissions: Database must be writable

### Low Hit Rate

1. Insufficient pre-generation: Run pregenerate script
2. Too many unique paths: Adjust tags to be more general
3. Effectiveness threshold too high: Lower min_effectiveness parameter

### High Costs

1. Cache disabled: Check startup logs
2. force_fresh=True somewhere: Review code
3. No matching content: Pre-generate more variations

## Best Practices

1. **Pre-generate on deployment**: Run script after each course update
2. **Monitor effectiveness**: Track and improve low-scoring content
3. **Periodic cleanup**: Remove stale content monthly
4. **A/B test thresholds**: Experiment with effectiveness cutoffs
5. **Log cache performance**: Track hit rates per endpoint

## Future Enhancements

- [ ] Question bank pre-generation
- [ ] Example bank pre-generation
- [ ] Distributed caching (Redis)
- [ ] ML-powered effectiveness prediction
- [ ] Automatic content refresh
- [ ] Content versioning
