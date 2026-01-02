"""Service for extracting claims and references from text using LLM."""

import json
import logging
from typing import Any

from app.schemas.extraction import ExtractionResult, ExtractedClaim, ExtractedReference
from app.services.lm_studio_client import LMStudioClient, LMStudioError

logger = logging.getLogger(__name__)


EXTRACTION_SYSTEM_PROMPT = """You are an expert at analyzing scientific and academic text to extract claims and their supporting references.

Your task is to:
1. Identify factual claims, statements, or assertions made in the text
2. Extract all bibliographic references mentioned in the text
3. Link each claim to the references that support it

For each claim, determine its type:
- factual: A verifiable factual statement
- statistical: Contains numerical data or statistics
- methodological: Describes a method or approach
- opinion: An opinion or interpretation
- conclusion: A conclusion or finding

Extract references in a structured format with as much information as available:
- Title
- Authors (as a formatted string)
- Year
- Source (journal, conference, book, etc.)
- DOI (if available)
- URL (if available)

Return ONLY a valid JSON object with this exact structure:
{
  "claims": [
    {
      "text": "claim text here",
      "claim_type": "factual",
      "reference_indices": [0, 1]
    }
  ],
  "references": [
    {
      "title": "Reference title",
      "authors": "Author1, Author2",
      "year": 2023,
      "source": "Journal Name",
      "doi": "10.1234/example",
      "url": "https://example.com"
    }
  ]
}

Be thorough but precise. Only extract clear claims and well-defined references."""


async def extract_claims_and_references(
    client: LMStudioClient,
    text: str,
) -> ExtractionResult:
    """
    Extract claims and references from text using LLM.

    Args:
        client: LM Studio client instance
        text: Text to analyze

    Returns:
        ExtractionResult with extracted claims and references

    Raises:
        LMStudioError: If extraction fails
    """
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract claims and references from the following text:\n\n{text}"}
    ]

    try:
        # Request JSON response format
        response = await client.chat_completion(
            messages=messages,
            temperature=0.1,  # Low temperature for more consistent extraction
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        # Parse the JSON response
        try:
            result_dict = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                result_dict = json.loads(response[json_start:json_end].strip())
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                result_dict = json.loads(response[json_start:json_end].strip())
            else:
                raise LMStudioError(f"Failed to parse JSON response: {e}") from e

        # Validate and parse into Pydantic models
        extraction_result = ExtractionResult(**result_dict)

        logger.info(
            f"Extracted {len(extraction_result.claims)} claims and "
            f"{len(extraction_result.references)} references"
        )

        return extraction_result

    except LMStudioError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}")
        raise LMStudioError(f"Extraction failed: {e}") from e


def validate_reference_indices(extraction_result: ExtractionResult) -> ExtractionResult:
    """
    Validate that all reference indices in claims are valid.

    Args:
        extraction_result: Extraction result to validate

    Returns:
        Validated extraction result with invalid indices removed
    """
    max_ref_index = len(extraction_result.references) - 1

    for claim in extraction_result.claims:
        # Filter out invalid reference indices
        valid_indices = [
            idx for idx in claim.reference_indices
            if 0 <= idx <= max_ref_index
        ]

        if len(valid_indices) != len(claim.reference_indices):
            logger.warning(
                f"Removed invalid reference indices from claim: {claim.text[:50]}..."
            )
            claim.reference_indices = valid_indices

    return extraction_result
