# SQLite-Specific Features

Use SQLite-specific features like LIMIT, and be aware of limited data types.

## SQLite-Specific Syntax:
- Use `LIMIT` for result limiting
- Be aware of SQLite's dynamic typing system
- Use SQLite-specific functions like `datetime()`, `julianday()`, `strftime()`
- Use `AUTOINCREMENT` for primary keys (though `INTEGER PRIMARY KEY` is usually sufficient)
- Use SQLite's flexible column affinity system
- Use `PRAGMA` statements for database configuration
- Use `ATTACH` and `DETACH` for multiple databases

## SQLite Limitations and Considerations:
- Limited data types (NULL, INTEGER, REAL, TEXT, BLOB)
- No native boolean type (use INTEGER 0/1)
- No native date/time types (use TEXT, REAL, or INTEGER)
- Limited ALTER TABLE support
- No RIGHT JOIN or FULL OUTER JOIN
- Case-insensitive LIKE by default
- Single writer, multiple readers concurrency model

## SQLite Best Practices:
- Use appropriate column affinity
- Consider using WITHOUT ROWID tables for certain use cases
- Use transactions for multiple operations
- Use `EXPLAIN QUERY PLAN` for optimization
- Be mindful of file-based nature and locking