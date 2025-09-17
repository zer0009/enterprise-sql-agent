# Enterprise SQL Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Beta%20Testing-yellow.svg)
![PostgreSQL](https://img.shields.io/badge/Tested%20on-PostgreSQL-blue.svg)
![AI](https://img.shields.io/badge/AI-Powered-orange.svg)
![Security](https://img.shields.io/badge/Security-Enterprise%20Grade-red.svg)

**A powerful AI-powered SQL agent that enables natural language querying across multiple database types with enterprise-grade security and performance monitoring.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#️-architecture) • [Security](#-security) • [Contributing](#-contributing)

</div>

---

## 🚀 Overview

The Enterprise SQL Agent is an advanced AI-powered tool that transforms natural language questions into optimized SQL queries across multiple database platforms. Built with enterprise-grade security, comprehensive error recovery, and intelligent performance monitoring, it provides a seamless interface for data exploration and analysis.

> **⚠️ Beta Status**: This project is currently in beta testing phase. Only PostgreSQL has been fully tested and is production-ready. Other database types are planned for future releases.

### Key Highlights

- **🔒 Enterprise Security**: Multi-layer SQL injection prevention with 50+ attack pattern detection
- **🗄️ Multi-Database Support**: PostgreSQL, MySQL, SQLite, SQL Server, Oracle, and MongoDB
- **🤖 AI-Powered**: Google Gemini 2.0 Flash and OpenAI GPT-4 integration
- **⚡ Performance Monitoring**: Real-time query optimization and validation tracking
- **🛡️ Error Recovery**: Intelligent query correction and retry mechanisms
- **📊 Industry-Aware**: Context-aware prompts for finance, healthcare, retail, and more

## ✨ Features

### 🗄️ **Multi-Database Support**
- **PostgreSQL** - ✅ **Tested & Ready** - Full support with advanced features
- **MySQL** - 🚧 **Planned** - Optimized for performance and compatibility
- **SQLite** - 🚧 **Planned** - Perfect for development and small-scale applications
- **SQL Server** - 🚧 **Planned** - Enterprise-grade Microsoft SQL Server support
- **Oracle** - 🚧 **Planned** - Comprehensive Oracle Database integration
- **MongoDB** - 🚧 **Planned** - NoSQL document database support

### 🤖 **AI-Powered Intelligence**
- **Natural Language Processing** - Convert questions to SQL queries
- **Semantic Table Selection** - AI-powered table and column discovery
- **Query Optimization** - Automatic query performance improvements
- **Context Awareness** - Industry-specific prompt templates
- **Conversation Memory** - Maintains context across queries

### 🛡️ **Enterprise Security**
- **SQL Injection Prevention** - 50+ attack pattern detection
- **Query Validation** - Multi-layer security checking
- **Access Control** - Role-based permissions (RBAC)
- **Audit Logging** - Comprehensive security event tracking
- **Resource Limits** - Query complexity and execution time controls

### ⚡ **Performance & Monitoring**
- **Real-time Metrics** - Query performance tracking
- **Validation Compliance** - Methodology adherence monitoring
- **Error Recovery** - Automatic query correction and retry
- **Caching** - Intelligent query result caching
- **Optimization Suggestions** - Performance improvement recommendations

### 🎯 **Advanced Features**
- **Industry Templates** - Specialized prompts for different sectors
- **Response Formatting** - Structured, user-friendly output
- **Interactive Mode** - Command-line interface with helpful commands
- **API Integration** - RESTful service endpoints
- **Extensible Architecture** - Plugin system for custom functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- **PostgreSQL database** (currently the only tested database)
- AI model API key (Google Gemini or OpenAI)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/zer0009/enterprise-sql-agent.git
   cd enterprise-sql-agent
   ```

2. **Install dependencies**
   ```bash
   pip install langchain langchain-community sqlalchemy python-dotenv
   pip install psycopg2-binary pymysql pyodbc cx-Oracle pymongo
   ```

3. **Configure environment**
```bash
cp env.template .env
   # Edit .env with your database and API credentials
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

### Configuration

Create a `.env` file with your settings:

```env
# Database Configuration
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_DB=your_database
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# AI Model Configuration (Choose one)
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-2.0-flash

# OR
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Advanced Settings
MAX_QUERY_RETRIES=3
QUERY_TIMEOUT=90
ENABLE_SEMANTIC_TABLE_SELECTION=true
ENABLE_QUERY_VALIDATION=true
```

## 📖 Usage

### Interactive Mode

Start the agent and ask questions in natural language:

```bash
python src/main.py
```

```
🎯 Enterprise SQL Agent - Interactive Mode
============================================================
🤔 Ask a question: Show me all customers from New York
🤔 Ask a question: What are the top 10 products by sales?
🤔 Ask a question: How many orders were placed last month?
```

### Available Commands

- `tables` - List all available tables
- `schema <table>` - Show detailed schema for a table
- `help` - Display help information
- `quit` - Exit the application

### Example Queries

```sql
-- Natural language queries that get converted to SQL
"Show me all users who registered this month"
"What's the average order value by customer?"
"List the top 5 products by revenue"
"How many customers are in each state?"
"Find all orders with a total value over $1000"
```

## 🏗️ Architecture

### Project Structure

```
enterprise-sql-agent/
├── src/
│   ├── main.py                    # Application entry point
│   ├── agents/
│   │   ├── sql_agent.py          # Core EnterpriseSQLAgent class
│   │   ├── prompt_manager.py     # Prompt template management
│   │   └── response_formatter.py # Response formatting and parsing
│   ├── config/
│   │   └── database_config.py    # Database configuration management
│   ├── database/
│   │   ├── tools/
│   │   │   ├── secure_sql_tool.py      # Security-enhanced SQL execution
│   │   │   ├── enhanced_sql_tool.py    # Error recovery and correction
│   │   │   └── sql_injection_patterns.py # Attack pattern detection
│   │   └── connection.py         # Database connection utilities
│   ├── llm/
│   │   └── models/
│   │       └── llm_setup.py      # Language model configuration
│   ├── services/
│   │   └── agent_service.py      # Agent management service
│   └── utils/
│       ├── performance_monitor.py # Performance tracking
│       └── security_monitor.py   # Security event monitoring
├── prompts/                      # Prompt templates
│   ├── system_message.md
│   ├── human_message.md
│   └── industries/              # Industry-specific prompts
└── vector_store_data/           # Semantic embeddings storage
```

### Core Components

#### 🧠 **EnterpriseSQLAgent**
The main agent class that orchestrates all functionality:
- Database connection management
- LLM integration and configuration
- Query processing and validation
- Response formatting and delivery

#### 🛡️ **Security Layer**
Comprehensive security implementation:
- **SecureUniversalSQLTool**: Multi-layer security validation
- **SQL Injection Detection**: 50+ attack pattern recognition
- **Query Validation**: Length, complexity, and syntax checking
- **Access Control**: Role-based permissions and audit logging

#### ⚡ **Performance Monitoring**
Real-time performance tracking:
- Query execution time monitoring
- Validation compliance tracking
- Optimization suggestion generation
- Statistical analysis and reporting

#### 🎯 **Error Recovery**
Intelligent error handling and correction:
- Automatic query syntax correction
- Retry mechanisms with exponential backoff
- Context-aware error suggestions
- Graceful degradation strategies

## 🔒 Security

### Security Features

- **SQL Injection Prevention**: Advanced pattern matching for all major attack types
- **Query Validation**: Multi-layer security checking with risk assessment
- **Access Control**: Role-based permissions and authentication
- **Audit Logging**: Comprehensive security event tracking
- **Resource Limits**: Query complexity and execution time controls

### Security Patterns Detected

- Classic injection (tautology-based)
- Union-based injection
- Boolean-based blind injection
- Time-based injection
- Error-based injection
- NoSQL injection patterns
- Code execution attempts
- Information disclosure

### Security Configuration

```env
# Security Settings
ALLOWED_QUERY_TYPES=SELECT
BLOCKED_KEYWORDS=DROP,DELETE,TRUNCATE,ALTER,CREATE,INSERT,UPDATE
MAX_QUERY_LENGTH=5000
MAX_LIMIT_VALUE=1000
ENABLE_QUERY_VALIDATION=true
```

## 📊 Performance Monitoring

### Metrics Tracked

- **Query Performance**: Execution time, response time, throughput
- **Validation Compliance**: Methodology adherence rates
- **Error Rates**: Failed queries and recovery success
- **Optimization**: Query improvement suggestions
- **Security**: Blocked queries and threat detection

### Performance Dashboard

The agent provides real-time performance insights:

```
📊 Performance Summary:
  Total Queries: 1,247
  Average Response Time: 1.2s
  Validation Compliance: 94.3%
  Security Events Blocked: 23
  Query Optimizations Applied: 156
```

## 🎯 Industry Support

### Specialized Prompts

The agent includes industry-specific prompt templates for:

- **Finance**: Banking, investment, and financial services
- **Healthcare**: Medical records and patient data
- **Retail**: E-commerce and inventory management
- **Manufacturing**: Production and supply chain
- **Logistics**: Shipping and distribution
- **SaaS**: Software service analytics

### Context-Aware Queries

The agent automatically detects industry context and optimizes queries accordingly:

```python
# Automatically detects healthcare context
"Show me patient records from last month"
# Generates HIPAA-compliant queries with proper data handling

# Detects retail context
"What are the top-selling products this quarter?"
# Optimizes for sales and inventory data structures
```

## 🔧 Configuration

### Database Configuration

| Database | Status | Driver Required | Configuration |
|----------|--------|----------------|---------------|
| PostgreSQL | ✅ **Tested** | `psycopg2-binary` | Host, Port, Database, User, Password |
| MySQL | 🚧 **Planned** | `pymysql` | Host, Port, Database, User, Password |
| SQLite | 🚧 **Planned** | Built-in | File path |
| SQL Server | 🚧 **Planned** | `pyodbc` | Host, Port, Database, User, Password |
| Oracle | 🚧 **Planned** | `cx-Oracle` | Host, Port, SID, User, Password |
| MongoDB | 🚧 **Planned** | `pymongo` | Host, Port, Database, User, Password |

### AI Model Configuration

| Provider | Models | Recommended |
|----------|--------|-------------|
| Google Gemini | gemini-2.0-flash, gemini-1.5-pro | ✅ Yes |
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo | Alternative |

### Advanced Settings

```env
# Agent Behavior
MAX_QUERY_RETRIES=3
QUERY_TIMEOUT=90
ENABLE_SEMANTIC_TABLE_SELECTION=true
ENABLE_QUERY_VALIDATION=true
ENABLE_ERROR_RECOVERY=true

# Performance
ENABLE_QUERY_CACHING=true
CACHE_TTL=3600
MAX_CACHE_SIZE=1000

# Security
ENABLE_SECURITY_MONITORING=true
LOG_SECURITY_EVENTS=true
SECURITY_LOG_LEVEL=INFO
```

## 🧪 Testing Status

### Current Testing Status

| Component | Status | Notes |
|-----------|--------|-------|
| **PostgreSQL** | ✅ **Fully Tested** | Production-ready with comprehensive testing |
| **MySQL** | 🚧 **Planned** | Support planned for next release |
| **SQLite** | 🚧 **Planned** | Support planned for next release |
| **SQL Server** | 🚧 **Planned** | Support planned for next release |
| **Oracle** | 🚧 **Planned** | Support planned for next release |
| **MongoDB** | 🚧 **Planned** | Support planned for next release |
| **Security Features** | ✅ **Tested** | Comprehensive security testing completed |
| **AI Integration** | ✅ **Tested** | Google Gemini and OpenAI integration tested |
| **Error Recovery** | ✅ **Tested** | Query correction and retry mechanisms tested |

### Beta Testing Notes

- **Current Version**: Beta 1.0
- **Production Ready**: PostgreSQL only
- **Testing Environment**: PostgreSQL 13+ with various data types and schemas
- **Security Testing**: Comprehensive SQL injection prevention tested
- **Performance Testing**: Query optimization and monitoring validated

### Future Releases

- **v1.1**: MySQL and SQLite support
- **v1.2**: SQL Server and Oracle support  
- **v1.3**: MongoDB support and advanced features
- **v2.0**: Production-ready multi-database support

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database credentials
echo $POSTGRES_PASSWORD

# Test connection manually
psql -h localhost -U your_user -d your_database
```

#### LLM Setup Failed
```bash
# Verify API key
echo $GOOGLE_API_KEY

# Test API access
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     "https://generativelanguage.googleapis.com/v1/models"
```

#### Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```env
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_QUERY_LOGGING=true
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Add tests if applicable
6. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Include unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code documentation
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas
- **Security**: Report security vulnerabilities privately via GitHub Issues

## 🙏 Acknowledgments

- **LangChain** - For the excellent AI agent framework
- **SQLAlchemy** - For robust database connectivity
- **Google Gemini** - For powerful language model capabilities
- **OpenAI** - For alternative AI model support
- **Community** - For feedback, contributions, and support

---

<div align="center">

**Built with ❤️ for the data community**

[⭐ Star this repo](https://github.com/zer0009/enterprise-sql-agent) • [🐛 Report a bug](https://github.com/zer0009/enterprise-sql-agent/issues) • [💡 Request a feature](https://github.com/zer0009/enterprise-sql-agent/issues)

</div>