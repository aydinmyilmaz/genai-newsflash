# Article Processing and Storage System

## Introduction

This system is a robust article processing pipeline that fetches, analyzes, summarizes, and stores web articles with a focus on specific topics. It's particularly useful for content curation, research aggregation, and maintaining personalized article collections.

### Key Features

- **Dual Scraping Strategy**: Implements both newspaper3k and SmartScraperGraph for reliable article extraction
- **Topic Validation**: Uses GPT-4 to ensure articles match specified topics
- **AI-Powered Summarization**: Generates concise summaries using OpenAI's language models
- **Persistent Storage**: MongoDB integration for efficient article and user data management
- **User Management**: Links articles to user profiles for personalized content collections
- **Error Handling**: Comprehensive logging and fallback mechanisms throughout the pipeline

## System Architecture

### Core Components

1. **ContentProcessor**
   - Handles article fetching, validation, and summarization
   - Implements dual scraping strategy with fallback mechanism
   - Integrates with OpenAI for content analysis and summarization
   - Validates article relevance against specified topics

2. **MongoDBManager**
   - Manages database connections and operations
   - Handles article storage and retrieval
   - Maintains user-article associations
   - Implements data indexing for efficient queries

### Dependencies

- `newspaper3k`: Primary article extraction
- `scrapegraphai`: Secondary article extraction (fallback)
- `langchain_openai`: AI-powered content processing
- `pymongo`: MongoDB interactions
- `nltk`: Natural language processing
- Various utility libraries (datetime, logging, etc.)

## Data Model

### Article Structure
```json
{
    "metadata": {
        "url": "string",
        "title": "string",
        "content": "string",
        "authors": ["string"],
        "published_date": "ISO-8601 date",
        "keywords": ["string"],
        "processing_date": "ISO-8601 date"
    },
    "summary": {
        "text": "string",
        "model_used": "string"
    }
}
```

### User Structure
```json
{
    "email": "string",
    "articles": ["article_id"]
}
```

## Setup Requirements

1. MongoDB instance running (default: localhost:27017)
2. OpenAI API key in environment variables
3. Summary prompt template file (`summary_prompt.txt`)
4. Input links file (`links.txt`)

## Usage

1. Configure environment variables:
   ```bash
   export OPENAI_API_KEY='your-api-key'
   ```

2. Prepare input files:
   - Create `summary_prompt.txt` with your summarization prompt
   - Add article URLs to `links.txt`

3. Run the script:
   ```bash
   python script_name.py
   ```

## Error Handling

The system implements comprehensive error handling:
- Connection failures fallback mechanisms
- Content extraction redundancy
- Detailed logging at all stages
- Transaction safety for database operations

## Logging

Detailed logging is implemented throughout the system:
- Connection events
- Processing status
- Error tracking
- Performance metrics

## Best Practices

1. **Regular Monitoring**: Check logs for processing errors
2. **Database Maintenance**: Regular backups and index optimization
3. **API Key Security**: Secure handling of OpenAI API keys
4. **Content Validation**: Regular checks of topic validation accuracy
5. **Performance Tuning**: Monitor and adjust batch sizes and timeouts

## Future Enhancements

Potential areas for improvement:
- Parallel processing for better throughput
- Additional content source adapters
- Enhanced summarization algorithms
- Advanced user management features
- API interface for external integration