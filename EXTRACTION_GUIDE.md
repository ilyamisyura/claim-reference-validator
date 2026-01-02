# Text Extraction Guide

This guide explains how to use the new text extraction feature to automatically extract claims and references from user-provided text using LM Studio.

## Overview

The extraction system uses a local LLM (via LM Studio) to analyze text and extract:
- **Claims**: Factual statements, assertions, or findings
- **References**: Bibliographic citations supporting the claims
- **Links**: Automatic linking between claims and their supporting references

All extracted data follows your database schema with automatic reference deduplication.

## Setup

### 1. Install and Run LM Studio

1. Download LM Studio from https://lmstudio.ai
2. Load a model (recommended: a capable instruction-following model like Llama 3, Mistral, or similar)
3. Start the local server:
   - In LM Studio, go to "Local Server" tab
   - Click "Start Server"
   - Default URL: `http://localhost:1234`

### 2. Configure Environment Variables

Create or update `backend/.env`:

```env
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model  # Use the model name shown in LM Studio
```

### 3. Run Database Migrations

```bash
cd backend
uv run alembic upgrade head
```

### 4. Start the Backend

```bash
cd backend
uv run python -m app.main
```

## API Usage

### Endpoint: POST /api/v1/extraction/extract-text

Extract claims and references from text.

**Request Body:**
```json
{
  "text": "Your text with claims and references goes here...",
  "project_id": 1
}
```

**Response:**
```json
{
  "project_id": 1,
  "extraction_result": {
    "claims": [
      {
        "text": "The extracted claim text",
        "claim_type": "factual",
        "page_number": null,
        "paragraph_index": null,
        "reference_indices": [0, 1]
      }
    ],
    "references": [
      {
        "title": "Reference Title",
        "authors": "Smith, J., Doe, A.",
        "year": 2023,
        "source": "Journal Name",
        "doi": "10.1234/example",
        "url": "https://example.com"
      }
    ]
  },
  "claims_created": 1,
  "references_created": 1,
  "references_deduplicated": 0
}
```

## Example Usage

### Using curl

```bash
curl -X POST http://localhost:8000/api/v1/extraction/extract-text \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "text": "Recent studies have shown that machine learning improves accuracy (Smith et al., 2023). The authors demonstrated a 15% improvement in classification tasks using transformer models (Doe and Johnson, 2024)."
  }'
```

### Using Python

```python
import httpx

async def extract_text():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/extraction/extract-text",
            json={
                "project_id": 1,
                "text": """
                Recent studies have shown that machine learning improves accuracy
                (Smith et al., 2023). The authors demonstrated a 15% improvement
                in classification tasks using transformer models.

                References:
                Smith, J., Brown, A., & Lee, C. (2023). Machine Learning Advances.
                Journal of AI Research, 45(2), 123-145.
                """
            }
        )
        return response.json()
```

## How It Works

1. **Text Analysis**: The LLM analyzes the provided text to identify claims and references
2. **Structured Extraction**: Claims and references are extracted in a structured JSON format
3. **Deduplication**: References are automatically deduplicated using:
   - DOI (if available)
   - Title + first author (normalized)
4. **Database Storage**:
   - Claims are created and linked to the project
   - References are created or reused if duplicates exist
   - Claim-reference links are established automatically
5. **Response**: Returns statistics and the full extraction result

## Claim Types

The system categorizes claims into types:
- `factual`: Verifiable factual statement
- `statistical`: Contains numerical data or statistics
- `methodological`: Describes a method or approach
- `opinion`: An opinion or interpretation
- `conclusion`: A conclusion or finding

## Reference Deduplication

References are automatically deduplicated using:

1. **DOI Priority**: If both references have a DOI, they're compared
2. **Title + Author Fallback**: Normalized title and first author are hashed
3. **Reuse**: Existing references are reused instead of creating duplicates

This ensures a clean reference database across all projects.

## Troubleshooting

### "LM Studio service not available"

- Ensure LM Studio is running with the server started
- Check that `LM_STUDIO_URL` in `.env` matches your LM Studio server URL
- Verify the model is loaded in LM Studio

### Poor Extraction Quality

- Try a different model (larger models generally perform better)
- Adjust the text format (clearer formatting helps)
- Ensure references are properly formatted in the input text

### Slow Extraction

- Extraction speed depends on:
  - Model size (smaller models are faster)
  - Text length
  - Your hardware (GPU vs CPU)
- Consider using a smaller model for faster processing
- LM Studio shows generation speed in the UI

## Next Steps

After extracting claims and references, you can:

1. **View Claims**: `GET /api/v1/claims?project_id={id}`
2. **View References**: `GET /api/v1/references`
3. **Update Claims**: `PUT /api/v1/claims/{claim_id}`
4. **Link/Unlink References**:
   - `POST /api/v1/claims/{claim_id}/references/{reference_id}`
   - `DELETE /api/v1/claims/{claim_id}/references/{reference_id}`

## Future Enhancements

Planned features:
- PDF extraction (upload PDFs and extract automatically)
- Web URL extraction (fetch and extract from online papers)
- Bulk processing
- Confidence scores for extracted claims
- Vector similarity for fuzzy reference matching
