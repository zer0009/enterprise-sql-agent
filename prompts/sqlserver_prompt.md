# SQL Server-Specific Features

Use SQL Server-specific features like TOP instead of LIMIT, and T-SQL syntax.

## SQL Server-Specific Syntax:
- Use `TOP` instead of `LIMIT` for result limiting
- Use T-SQL specific functions and procedures
- Use `IDENTITY` for auto-incrementing columns
- Use SQL Server-specific data types (NVARCHAR, DATETIME2, etc.)
- Use `OUTPUT` clause instead of `RETURNING`
- Use `MERGE` statement for upsert operations
- Use Common Table Expressions (CTEs) and window functions
- Use `TRY...CATCH` for error handling

## SQL Server T-SQL Features:
- Use stored procedures and user-defined functions
- Use table variables and temporary tables
- Use `CROSS APPLY` and `OUTER APPLY`
- Use `PIVOT` and `UNPIVOT` operations
- Use `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()` window functions
- Use `STRING_AGG()` for string concatenation (SQL Server 2017+)
- Use `IIF()` and `CHOOSE()` functions

## SQL Server Best Practices:
- Use appropriate indexing strategies (clustered, non-clustered)
- Use `SET NOCOUNT ON` in stored procedures
- Use parameterized queries to prevent SQL injection
- Use `EXPLAIN` or execution plans for optimization
- Consider SQL Server's specific transaction isolation levels
- Use appropriate data types for performance