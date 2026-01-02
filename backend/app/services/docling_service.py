"""Service for extracting data from documents using Docling."""

import logging
import tempfile
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from app.schemas.extraction import ExtractedReference

logger = logging.getLogger(__name__)


class DoclingService:
    """Service for document processing using Docling."""

    def __init__(self):
        """Initialize Docling document converter."""
        # Configure PDF processing pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # Disable OCR for faster processing (enable if needed)
        pipeline_options.do_table_structure = True  # Extract tables

        # Initialize converter with PDF format options
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def process_pdf(self, pdf_content: bytes | BinaryIO, filename: str = "document.pdf") -> dict:
        """
        Process PDF and extract structured content.

        Args:
            pdf_content: PDF file content (bytes or file-like object)
            filename: Optional filename for logging

        Returns:
            Dict with extracted content including text, tables, and metadata
        """
        logger.info(f"Processing PDF: {filename}")

        # Docling requires a file path, so we need to save to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            # Write content to temp file
            if isinstance(pdf_content, bytes):
                tmp_file.write(pdf_content)
            else:
                tmp_file.write(pdf_content.read())

            tmp_path = Path(tmp_file.name)

        try:
            # Process the document using the file path
            result = self.converter.convert(tmp_path)

            # Extract document content
            doc_content = {
                "title": self._extract_title(result),
                "authors": self._extract_authors(result),
                "abstract": self._extract_abstract(result),
                "text": result.document.export_to_text(),
                "markdown": result.document.export_to_markdown(),
                "sections": self._extract_sections(result),
                "tables": self._extract_tables(result),
                "references": self._extract_references(result),
                "metadata": self._extract_metadata(result),
            }

            logger.info(
                f"Extracted {len(doc_content['sections'])} sections, "
                f"{len(doc_content['tables'])} tables, "
                f"{len(doc_content['references'])} references"
            )

            return doc_content
        finally:
            # Clean up temporary file
            try:
                tmp_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {tmp_path}: {e}")

    def _extract_title(self, result) -> str | None:
        """Extract document title from metadata."""
        try:
            # Try to get title from metadata
            if hasattr(result.document, 'metadata') and result.document.metadata:
                if hasattr(result.document.metadata, 'title'):
                    return result.document.metadata.title

            # Fallback: use first heading if available
            for item in result.document.body.children:
                if hasattr(item, 'text') and hasattr(item, 'label'):
                    if 'title' in item.label.lower() or 'heading' in item.label.lower():
                        return item.text

            return None
        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")
            return None

    def _extract_authors(self, result) -> list[str]:
        """Extract authors from document metadata."""
        try:
            authors = []
            if hasattr(result.document, 'metadata') and result.document.metadata:
                if hasattr(result.document.metadata, 'authors'):
                    authors = result.document.metadata.authors or []
            return authors
        except Exception as e:
            logger.warning(f"Failed to extract authors: {e}")
            return []

    def _extract_abstract(self, result) -> str | None:
        """Extract abstract from document."""
        try:
            # Look for abstract section
            for item in result.document.body.children:
                if hasattr(item, 'text') and hasattr(item, 'label'):
                    if 'abstract' in item.label.lower():
                        return item.text
            return None
        except Exception as e:
            logger.warning(f"Failed to extract abstract: {e}")
            return None

    def _extract_sections(self, result) -> list[dict]:
        """Extract document sections with headings."""
        sections = []
        current_section = {"heading": "Introduction", "text": ""}

        try:
            for item in result.document.body.children:
                if not hasattr(item, 'text'):
                    continue

                # Check if this is a heading
                if hasattr(item, 'label') and 'heading' in item.label.lower():
                    # Save previous section if it has content
                    if current_section["text"].strip():
                        sections.append(current_section)

                    # Start new section
                    current_section = {
                        "heading": item.text.strip(),
                        "text": ""
                    }
                else:
                    # Add to current section
                    current_section["text"] += item.text + "\n\n"

            # Add last section
            if current_section["text"].strip():
                sections.append(current_section)

        except Exception as e:
            logger.warning(f"Failed to extract sections: {e}")

        return sections

    def _extract_tables(self, result) -> list[dict]:
        """Extract tables from document."""
        tables = []

        try:
            for item in result.document.body.children:
                if hasattr(item, 'label') and 'table' in item.label.lower():
                    table_data = {
                        "caption": getattr(item, 'caption', None),
                        "data": self._parse_table(item),
                    }
                    tables.append(table_data)
        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")

        return tables

    def _parse_table(self, table_item) -> list[list[str]]:
        """Parse table structure into rows and columns."""
        try:
            # Docling provides table data in various formats
            # This is a simplified parser - adjust based on actual structure
            if hasattr(table_item, 'data'):
                return table_item.data
            return []
        except Exception as e:
            logger.warning(f"Failed to parse table: {e}")
            return []

    def _extract_references(self, result) -> list[ExtractedReference]:
        """Extract bibliographic references from document."""
        references = []

        try:
            # Look for references section
            in_references = False
            reference_text = ""

            for item in result.document.body.children:
                if not hasattr(item, 'text'):
                    continue

                # Check if we've entered the references section
                if hasattr(item, 'label') and 'heading' in item.label.lower():
                    heading = item.text.lower()
                    if 'reference' in heading or 'bibliography' in heading:
                        in_references = True
                        continue
                    elif in_references:
                        # We've left the references section
                        break

                # Collect reference text
                if in_references:
                    reference_text += item.text + "\n"

            # Parse individual references
            if reference_text:
                references = self._parse_references(reference_text)

        except Exception as e:
            logger.warning(f"Failed to extract references: {e}")

        return references

    def _parse_references(self, reference_text: str) -> list[ExtractedReference]:
        """
        Parse reference text into structured references.

        This is a simplified parser. For production, consider using:
        - A dedicated citation parser
        - LLM for parsing
        - Citation parsing libraries
        """
        references = []

        # Split by common reference separators
        lines = reference_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 20:  # Skip empty or very short lines
                continue

            # Very basic parsing - extract what we can
            # In production, use a proper citation parser or LLM
            ref = self._parse_single_reference(line)
            if ref:
                references.append(ref)

        return references

    def _parse_single_reference(self, ref_text: str) -> ExtractedReference | None:
        """
        Parse a single reference line into structured data.

        This is extremely simplified. For production use:
        - LLM-based parsing
        - Specialized citation parsing libraries
        - External services
        """
        try:
            # Remove common prefixes like [1], 1., etc.
            import re
            ref_text = re.sub(r'^\[?\d+\]?\.?\s*', '', ref_text)

            # Try to extract year
            year_match = re.search(r'\((\d{4})\)', ref_text)
            year = int(year_match.group(1)) if year_match else None

            # Very basic extraction - just use the full text as title
            # and mark it for manual review
            return ExtractedReference(
                title=ref_text[:200],  # Use first 200 chars as title
                authors="Unknown",  # Would need proper parsing
                year=year,
                source=None,
                doi=None,
                url=None
            )
        except Exception as e:
            logger.debug(f"Failed to parse reference: {e}")
            return None

    def _extract_metadata(self, result) -> dict:
        """Extract document metadata."""
        metadata = {}

        try:
            if hasattr(result.document, 'metadata'):
                meta = result.document.metadata
                metadata = {
                    "page_count": getattr(meta, 'page_count', None),
                    "language": getattr(meta, 'language', None),
                    "creation_date": getattr(meta, 'creation_date', None),
                }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

        return metadata


# Global service instance
_docling_service: DoclingService | None = None


def get_docling_service() -> DoclingService:
    """Get or create the global Docling service instance."""
    global _docling_service
    if _docling_service is None:
        _docling_service = DoclingService()
    return _docling_service
