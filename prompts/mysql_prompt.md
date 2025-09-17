# MySQL Database Adapter

## Essential MySQL Syntax:
- **Result Limiting**: Use `LIMIT` clause for controlling result sets
- **Case Sensitivity**: Be aware of case sensitivity in table/column names (OS-dependent)
- **Identifier Quoting**: Use backticks (`) for identifiers with special characters
- **String Operations**: Use `CONCAT()` for concatenation, MySQL string functions
- **Date Handling**: Use `DATE_FORMAT()`, `STR_TO_DATE()` for date operations

## MySQL-Specific Query Patterns:
- **Auto-Increment**: Use `AUTO_INCREMENT` for primary key generation
- **String Aggregation**: Use `GROUP_CONCAT()` for combining strings in groups
- **Upsert Operations**: Use `ON DUPLICATE KEY UPDATE` for insert-or-update logic
- **Regular Expressions**: Use `REGEXP` or `RLIKE` for pattern matching
- **JSON Operations**: Use `JSON_EXTRACT()`, `JSON_SEARCH()` (MySQL 5.7+)

## Data Type Handling:
- **Integer Types**: TINYINT, SMALLINT, MEDIUMINT, INT, BIGINT
- **Text Types**: VARCHAR, TEXT, MEDIUMTEXT, LONGTEXT
- **Date Types**: DATE, TIME, DATETIME, TIMESTAMP, YEAR
- **Numeric Types**: DECIMAL, FLOAT, DOUBLE for precision control
- **Binary Types**: BINARY, VARBINARY, BLOB variants

## Query Optimization Guidelines:
- Choose appropriate storage engines (InnoDB for transactions, MyISAM for read-heavy)
- Consider MySQL's SQL mode settings and their impact
- Use proper indexing strategies (B-tree, Full-text, Spatial)
- Optimize queries for MySQL's query execution planner
- Monitor performance with `EXPLAIN` and `SHOW PROCESSLIST`

## Common Functions:
- **String**: `CONCAT()`, `SUBSTRING()`, `REPLACE()`, `TRIM()`
- **Mathematical**: `ROUND()`, `CEIL()`, `FLOOR()`, `RAND()`
- **Date/Time**: `NOW()`, `CURDATE()`, `DATE_ADD()`, `DATEDIFF()`
- **Aggregate**: `GROUP_CONCAT()`, `COUNT()`, `SUM()`, `AVG()`
- **Conditional**: `IF()`, `CASE`, `COALESCE()`, `NULLIF()`