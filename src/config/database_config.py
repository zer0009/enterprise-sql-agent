#!/usr/bin/env python3
"""
Database Configuration Module
Handles database type detection, configuration loading, and connection management
for multiple database types including PostgreSQL, MySQL, SQLite, SQL Server, Oracle, and MongoDB.
"""

import os
import urllib.parse
from enum import Enum
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQLSERVER = "mssql"
    ORACLE = "oracle"
    MONGODB = "mongodb"

class DatabaseConfig:
    """Database configuration class"""
    def __init__(self, db_type: DatabaseType, **kwargs):
        self.db_type = db_type
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port')
        self.database = kwargs.get('database')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.connection_string = kwargs.get('connection_string')
        self.file_path = kwargs.get('file_path')  # For SQLite
        
        # Set default ports if not provided
        if not self.port:
            self.port = self._get_default_port()
    
    def _get_default_port(self) -> str:
        """Get default port for database type"""
        defaults = {
            DatabaseType.POSTGRESQL: '5432',
            DatabaseType.MYSQL: '3306',
            DatabaseType.SQLSERVER: '1433',
            DatabaseType.ORACLE: '1521',
            DatabaseType.MONGODB: '27017'
        }
        return defaults.get(self.db_type, '5432')

class DatabaseManager:
    """Manages database connections and configurations"""
    
    def __init__(self):
        self.database_drivers = self._detect_available_drivers()
    
    def _detect_available_drivers(self) -> dict:
        """Detect available database drivers"""
        drivers = {}
        
        # PostgreSQL
        try:
            import psycopg2
            drivers['postgresql'] = 'psycopg2'
        except ImportError:
            try:
                import pg8000
                drivers['postgresql'] = 'pg8000'
            except ImportError:
                pass
        
        # MySQL
        try:
            import pymysql
            drivers['mysql'] = 'pymysql'
        except ImportError:
            try:
                import MySQLdb
                drivers['mysql'] = 'MySQLdb'
            except ImportError:
                pass
        
        # SQL Server
        try:
            import pyodbc
            drivers['mssql'] = 'pyodbc'
        except ImportError:
            try:
                import pymssql
                drivers['mssql'] = 'pymssql'
            except ImportError:
                pass
        
        # Oracle
        try:
            import cx_Oracle
            drivers['oracle'] = 'cx_Oracle'
        except ImportError:
            pass
        
        # SQLite (built-in)
        drivers['sqlite'] = 'sqlite3'
        
        return drivers
    
    def detect_database_type(self) -> Optional[DatabaseType]:
        """Auto-detect database type from environment variables"""
        # Check for explicit database type
        db_type_env = os.getenv('DATABASE_TYPE', '').lower()
        if db_type_env:
            try:
                return DatabaseType(db_type_env)
            except ValueError:
                pass
        
        # Auto-detect based on available environment variables
        if any(os.getenv(key) for key in ['POSTGRES_HOST', 'POSTGRES_URL', 'POSTGRESQL_URL']):
            return DatabaseType.POSTGRESQL
        elif any(os.getenv(key) for key in ['MYSQL_HOST', 'MYSQL_URL']):
            return DatabaseType.MYSQL
        elif os.getenv('SQLITE_PATH') or os.getenv('SQLITE_FILE'):
            return DatabaseType.SQLITE
        elif any(os.getenv(key) for key in ['SQLSERVER_HOST', 'MSSQL_HOST', 'SQLSERVER_URL']):
            return DatabaseType.SQLSERVER
        elif any(os.getenv(key) for key in ['ORACLE_HOST', 'ORACLE_URL']):
            return DatabaseType.ORACLE
        elif any(os.getenv(key) for key in ['MONGODB_HOST', 'MONGODB_URL']):
            return DatabaseType.MONGODB
        
        # Default to PostgreSQL if no specific type detected
        return DatabaseType.POSTGRESQL
    
    def load_database_config(self, db_type: DatabaseType) -> DatabaseConfig:
        """Load database configuration based on type"""
        if db_type == DatabaseType.POSTGRESQL:
            return DatabaseConfig(
                db_type=db_type,
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', os.getenv('POSTGRES_DATABASE')),
                username=os.getenv('POSTGRES_USER', os.getenv('POSTGRES_USERNAME')),
                password=os.getenv('POSTGRES_PASSWORD'),
                connection_string=os.getenv('POSTGRES_URL', os.getenv('POSTGRESQL_URL'))
            )
        
        elif db_type == DatabaseType.MYSQL:
            return DatabaseConfig(
                db_type=db_type,
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=os.getenv('MYSQL_PORT', '3306'),
                database=os.getenv('MYSQL_DB', os.getenv('MYSQL_DATABASE')),
                username=os.getenv('MYSQL_USER', os.getenv('MYSQL_USERNAME')),
                password=os.getenv('MYSQL_PASSWORD'),
                connection_string=os.getenv('MYSQL_URL')
            )
        
        elif db_type == DatabaseType.SQLITE:
            return DatabaseConfig(
                db_type=db_type,
                file_path=os.getenv('SQLITE_PATH', os.getenv('SQLITE_FILE', 'database.db'))
            )
        
        elif db_type == DatabaseType.SQLSERVER:
            return DatabaseConfig(
                db_type=db_type,
                host=os.getenv('SQLSERVER_HOST', os.getenv('MSSQL_HOST', 'localhost')),
                port=os.getenv('SQLSERVER_PORT', os.getenv('MSSQL_PORT', '1433')),
                database=os.getenv('SQLSERVER_DB', os.getenv('MSSQL_DB')),
                username=os.getenv('SQLSERVER_USER', os.getenv('MSSQL_USER')),
                password=os.getenv('SQLSERVER_PASSWORD', os.getenv('MSSQL_PASSWORD')),
                connection_string=os.getenv('SQLSERVER_URL', os.getenv('MSSQL_URL'))
            )
        
        elif db_type == DatabaseType.ORACLE:
            return DatabaseConfig(
                db_type=db_type,
                host=os.getenv('ORACLE_HOST', 'localhost'),
                port=os.getenv('ORACLE_PORT', '1521'),
                database=os.getenv('ORACLE_DB', os.getenv('ORACLE_SID')),
                username=os.getenv('ORACLE_USER', os.getenv('ORACLE_USERNAME')),
                password=os.getenv('ORACLE_PASSWORD'),
                connection_string=os.getenv('ORACLE_URL')
            )
        
        elif db_type == DatabaseType.MONGODB:
            return DatabaseConfig(
                db_type=db_type,
                host=os.getenv('MONGODB_HOST', 'localhost'),
                port=os.getenv('MONGODB_PORT', '27017'),
                database=os.getenv('MONGODB_DB'),
                username=os.getenv('MONGODB_USER'),
                password=os.getenv('MONGODB_PASSWORD'),
                connection_string=os.getenv('MONGODB_URL')
            )
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def build_connection_string(self, config: DatabaseConfig) -> str:
        """Build connection string for the database"""
        if config.connection_string:
            return config.connection_string
        
        if config.db_type == DatabaseType.POSTGRESQL:
            driver = self.database_drivers.get('postgresql', 'psycopg2')
            return f"postgresql+{driver}://{config.username}:{urllib.parse.quote_plus(config.password)}@{config.host}:{config.port}/{config.database}"
        
        elif config.db_type == DatabaseType.MYSQL:
            driver = self.database_drivers.get('mysql', 'pymysql')
            return f"mysql+{driver}://{config.username}:{urllib.parse.quote_plus(config.password)}@{config.host}:{config.port}/{config.database}"
        
        elif config.db_type == DatabaseType.SQLITE:
            return f"sqlite:///{config.file_path}"
        
        elif config.db_type == DatabaseType.SQLSERVER:
            if 'pyodbc' in self.database_drivers.get('mssql', ''):
                # URL encode the connection string for ODBC
                driver_name = "ODBC Driver 17 for SQL Server"
                return f"mssql+pyodbc://{config.username}:{urllib.parse.quote_plus(config.password)}@{config.host}:{config.port}/{config.database}?driver={urllib.parse.quote_plus(driver_name)}"
            else:
                return f"mssql+pymssql://{config.username}:{urllib.parse.quote_plus(config.password)}@{config.host}:{config.port}/{config.database}"
        
        elif config.db_type == DatabaseType.ORACLE:
            return f"oracle+cx_oracle://{config.username}:{urllib.parse.quote_plus(config.password)}@{config.host}:{config.port}/{config.database}"
        
        else:
            raise ValueError(f"Cannot build connection string for {config.db_type}")
    
    def test_database_connection(self, config: DatabaseConfig) -> bool:
        """Test database connection with specific drivers"""
        try:
            if config.db_type == DatabaseType.POSTGRESQL:
                if 'psycopg2' in self.database_drivers.get('postgresql', ''):
                    import psycopg2
                    test_conn = psycopg2.connect(
                        host=config.host,
                        port=config.port,
                        database=config.database,
                        user=config.username,
                        password=config.password
                    )
                    test_conn.close()
                    return True
            
            elif config.db_type == DatabaseType.MYSQL:
                if 'pymysql' in self.database_drivers.get('mysql', ''):
                    import pymysql
                    test_conn = pymysql.connect(
                        host=config.host,
                        port=int(config.port),
                        database=config.database,
                        user=config.username,
                        password=config.password
                    )
                    test_conn.close()
                    return True
            
            elif config.db_type == DatabaseType.SQLITE:
                import sqlite3
                test_conn = sqlite3.connect(config.file_path)
                test_conn.close()
                return True
            
            # For other databases, test with SQLAlchemy engine
            connection_string = self.build_connection_string(config)
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
            
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
    
    def show_driver_installation_help(self, db_type: DatabaseType):
        """Show installation help for database drivers"""
        help_text = {
            DatabaseType.POSTGRESQL: "pip install psycopg2-binary",
            DatabaseType.MYSQL: "pip install pymysql",
            DatabaseType.SQLSERVER: "pip install pyodbc",
            DatabaseType.ORACLE: "pip install cx_Oracle",
            DatabaseType.MONGODB: "pip install pymongo"
        }
        
        if db_type in help_text:
            print(f"Install the required driver with: {help_text[db_type]}")
    
    def is_driver_available(self, db_type: DatabaseType) -> bool:
        """Check if driver is available for database type"""
        driver_key = db_type.value
        return driver_key in self.database_drivers





