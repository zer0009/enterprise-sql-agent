# MongoDB-Specific Features

Use MongoDB-specific features and SQL interface for document database operations.

## MongoDB SQL Interface:
- Use SQL-like syntax through MongoDB's SQL interface
- Be aware that MongoDB is a document database, not relational
- Use dot notation for nested document fields
- Use MongoDB-specific functions for document operations
- Use `$` operators for MongoDB query operations
- Use aggregation pipeline operations when available

## MongoDB Document Structure:
- Documents are stored as BSON (Binary JSON)
- Fields can contain arrays, nested documents, and various data types
- Use `_id` field as the primary key (ObjectId by default)
- Schema is flexible and can vary between documents
- Use embedded documents vs. references based on access patterns

## MongoDB Query Patterns:
- Use find() operations for document retrieval
- Use aggregation pipeline for complex queries
- Use indexing on frequently queried fields
- Use projection to limit returned fields
- Use sort, limit, and skip for pagination

## MongoDB-Specific Considerations:
- No traditional JOINs (use $lookup in aggregation)
- No foreign key constraints
- Use denormalization for performance
- Consider document size limits (16MB per document)
- Use appropriate read/write concerns
- Use sharding for horizontal scaling

## MongoDB Best Practices:
- Design schema based on query patterns
- Use compound indexes for multi-field queries
- Use covered queries when possible
- Consider using MongoDB's text search capabilities
- Use appropriate data types (ObjectId, Date, etc.)
- Monitor query performance with explain()