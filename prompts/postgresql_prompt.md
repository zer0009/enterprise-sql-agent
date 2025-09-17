# PostgreSQL Database Adapter

## Essential PostgreSQL Syntax:
- **Result Limiting**: Use `LIMIT` clause (mandatory for all queries)
- **Case-Insensitive Search**: Use `ILIKE` operator for pattern matching
- **String Operations**: Use `||` for concatenation, double quotes for identifiers
- **Date/Time Functions**: Use `EXTRACT()`, `DATE_PART()`, `DATE_TRUNC()`, `INTERVAL`
- **Boolean Logic**: Use `TRUE`/`FALSE` literals

## PostgreSQL-Specific Query Patterns:
- **JSON/JSONB Operations**: Use `->`, `->>`, `@>`, `?` operators for JSON data
- **Array Operations**: Use `ANY()`, `ALL()`, `array_agg()`, `unnest()` for array handling
- **Window Functions**: `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`, `NTILE()` for analytics
- **Common Table Expressions**: Use `WITH` clause for complex queries
- **Recursive Queries**: Support for recursive CTEs for hierarchical data
- **Full-Text Search**: Use `to_tsvector()`, `to_tsquery()`, `@@` for text search

## Data Type Handling:
- **Identifiers**: Use double quotes for column/table names with special characters
- **UUID**: Native UUID support for unique identifiers
- **JSONB**: Preferred over JSON for better indexing and performance
- **Arrays**: Native array support with indexing capabilities
- **Network Types**: INET/CIDR for IP address storage
- **Temporal Types**: TIMESTAMP WITH TIME ZONE for timezone-aware dates
- **Precision Numbers**: NUMERIC for exact decimal calculations

## Query Optimization Guidelines:
- Use `EXPLAIN ANALYZE` for performance analysis
- Leverage appropriate index types: B-tree, GIN, GiST, Hash
- Consider partial indexes for filtered data scenarios
- Use materialized views for expensive aggregations
- Apply proper maintenance with `VACUUM` and `ANALYZE`

## Common Functions:
- **String**: `CONCAT()`, `SUBSTRING()`, `REGEXP_REPLACE()`, `STRING_AGG()`
- **Mathematical**: `ROUND()`, `CEIL()`, `FLOOR()`, `RANDOM()`
- **Aggregate**: `ARRAY_AGG()`, `JSON_AGG()`, statistical functions
- **Date/Time**: `NOW()`, `CURRENT_DATE`, `AGE()`, `GENERATE_SERIES()`