# RSS Summarizer Updates - Summary

## Changes Implemented

### 1. **Summary Header with Category Counts**
- **Dashboard** now displays a professional summary header showing:
  - Total number of articles processed
  - Article count per category with color-coded boxes
  - Each category shows its count with the category's designated color

### 2. **External LLM Configuration**
- **New Database Table**: `system_config` to store LLM configuration
- **New Admin Page**: `/admin/llm` for configuring AI service
- **Configurable Settings**:
  - **LLM Provider**: AWS Bedrock, OpenAI, Anthropic, or Custom (OpenAI Compatible)
  - **API Key**: For authentication (optional for AWS Bedrock with IAM)
  - **Model ID**: Specify which model to use (e.g., `gpt-4o-mini`, `claude-3-5-sonnet-20241022`)
  - **API Base URL**: For custom OpenAI-compatible endpoints

### 3. **Database Updates**
- Added `SystemConfig` model to `database.py`
- Created migration script `migrate_config.py` to add the `system_config` table
- Migration script automatically inserts default configuration values

### 4. **Updated Files**

#### **app.py**
- Added `SystemConfig` import
- Added `func` import from SQLAlchemy for aggregation
- Updated `dashboard()` route to calculate category statistics
- Added `admin_llm()` route to display LLM configuration page
- Added `update_llm_config()` route to save LLM settings

#### **database.py**
- Added `SystemConfig` model class

#### **templates/dashboard.html**
- Added summary header card with total articles count
- Added individual category count boxes with color coding
- Maintained all existing article display functionality

#### **templates/admin_base.html**
- Added "LLM Config" link to desktop navigation
- Added "LLM Config" to mobile dropdown menu

#### **templates/admin_llm.html** (NEW)
- Form to configure LLM provider
- Input fields for API key, model ID, and API base URL
- Displays current configuration
- Helpful examples for different providers

## How to Use

### View Summary Statistics
1. Go to the main dashboard (`/`)
2. See the summary header showing total articles and counts per category

### Configure LLM Provider
1. Go to Admin Panel → LLM Config (`/admin/llm`)
2. Select your LLM provider from the dropdown
3. Enter your API key (if required)
4. Specify the model ID
5. Optionally set a custom API base URL
6. Click "Save Configuration"

### Supported LLM Providers
- **AWS Bedrock**: Uses IAM credentials, no API key needed
- **OpenAI**: Requires API key, models like `gpt-4o-mini`, `gpt-4o`
- **Anthropic**: Requires API key, models like `claude-3-5-sonnet-20241022`
- **Custom**: Any OpenAI-compatible endpoint

## Next Steps
To fully integrate the LLM configuration into the article processing:
1. Update `services.py` `AIService` class to read from `SystemConfig`
2. Implement provider-specific API calls based on the selected provider
3. Handle different response formats from different providers

## Migration
Run the migration script to add the system_config table:
```bash
python migrate_config.py
```

This will create the table and insert default configuration values.
