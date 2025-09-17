# Oracle-Specific Features

Use Oracle-specific features like ROWNUM instead of LIMIT, and Oracle SQL syntax.

## Oracle-Specific Syntax:
- Use `ROWNUM` or `ROW_NUMBER() OVER()` instead of `LIMIT` for result limiting
- Use Oracle-specific functions like `NVL()`, `NVL2()`, `DECODE()`
- Use `SEQUENCE` objects for auto-incrementing values
- Use Oracle-specific data types (VARCHAR2, NUMBER, DATE, TIMESTAMP, etc.)
- Use `DUAL` table for single-row queries
- Use Oracle's hierarchical queries with `CONNECT BY`
- Use `MERGE` statement for upsert operations
- Use Oracle's analytic functions and window functions

## Oracle SQL Features:
- Use PL/SQL for stored procedures and functions
- Use `CASE` expressions and `DECODE()` function
- Use Oracle's date arithmetic and functions
- Use `LISTAGG()` for string aggregation
- Use `PIVOT` and `UNPIVOT` operations
- Use Oracle's regular expression functions (REGEXP_LIKE, REGEXP_SUBSTR, etc.)
- Use `WITH` clause for Common Table Expressions

## Oracle Pagination Patterns:
```sql
-- Oracle 12c+ (use OFFSET/FETCH)
SELECT * FROM table_name 
ORDER BY column_name 
OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY;

-- Pre-12c (use ROWNUM)
SELECT * FROM (
  SELECT a.*, ROWNUM rnum FROM (
    SELECT * FROM table_name ORDER BY column_name
  ) a WHERE ROWNUM <= 20
) WHERE rnum >= 11;
```

## Oracle Best Practices:
- Use appropriate indexing strategies (B-tree, bitmap, function-based)
- Use Oracle's optimizer hints when necessary
- Use `EXPLAIN PLAN` for query optimization
- Consider Oracle's specific transaction isolation levels
- Use appropriate data types for performance and storage
- Use Oracle's partitioning features for large tables