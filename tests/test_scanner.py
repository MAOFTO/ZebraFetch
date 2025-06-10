"""Test the scanner service."""

from app.services.scanner import Scanner
import io
from PIL import Image, ImageDraw
import pytest


def create_test_pdf_with_barcode() -> bytes:
    """Create a test PDF with a QR code."""
    # Create a blank image
    img = Image.new("RGB", (200, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Draw a simple QR code pattern (just for testing)
    draw.rectangle([50, 50, 150, 150], fill="black")
    draw.rectangle([60, 60, 140, 140], fill="white")
    draw.rectangle([70, 70, 130, 130], fill="black")

    # Save as PDF
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format="PDF")
    return pdf_bytes.getvalue()


@pytest.fixture
def scanner() -> Scanner:
    """Create a scanner instance with default DPI."""
    return Scanner(dpi=300)  # Use explicit DPI value


def test_scanner_initialization(scanner: Scanner) -> None:
    """Test scanner initialization."""
    assert scanner is not None
    assert scanner.dpi == 300


def test_scan_pdf_with_barcodes(scanner: Scanner) -> None:
    """Test PDF scanning with barcodes."""
    pdf_bytes = create_test_pdf_with_barcode()
    results = scanner.scan_pdf(pdf_bytes)
    assert results is not None
    assert isinstance(results, list)


def test_scan_pdf_without_barcodes(scanner: Scanner) -> None:
    """Test PDF scanning without barcodes."""
    # Create a blank PDF (no barcode)
    img = Image.new("RGB", (200, 200), color="white")
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format="PDF")
    results = scanner.scan_pdf(pdf_bytes.getvalue())
    assert results is not None
    assert isinstance(results, list)
    assert len(results) == 0


def test_scan_invalid_file(scanner: Scanner) -> None:
    """Test scanning with invalid file (should raise)."""
    with pytest.raises(Exception):
        scanner.scan_pdf(b"not a pdf")


def test_scan_pdf() -> None:
    """Test PDF scanning."""
    scanner = Scanner(dpi=300)  # Use explicit DPI value
    pdf_bytes = create_test_pdf_with_barcode()
    results = scanner.scan_pdf(
        pdf_bytes,
        page_range=[0],
        symbologies=["QR_CODE"],
        embed_page=True,
        embed_snippet=True,
    )
    assert isinstance(results, list)
    if results:  # If a barcode was detected
        result = results[0]
        assert "page" in result
        assert "type" in result
        assert "value" in result
        assert "position" in result
        assert "page_image" in result
        assert "snippet" in result


def test_scan_pdf_invalid_page() -> None:
    """Test scanning with invalid page range."""
    scanner = Scanner(dpi=300)  # Use explicit DPI value
    pdf_bytes = create_test_pdf_with_barcode()
    results = scanner.scan_pdf(
        pdf_bytes, page_range=[999], symbologies=["QR_CODE"]  # Non-existent page
    )
    assert isinstance(results, list)
    assert len(results) == 0


def test_scan_pdf_filter_symbology() -> None:
    """Test filtering by barcode type."""
    scanner = Scanner(dpi=300)  # Use explicit DPI value
    pdf_bytes = create_test_pdf_with_barcode()
    # Test with non-matching symbology
    results = scanner.scan_pdf(
        pdf_bytes, symbologies=["CODE_128"]  # Different from QR_CODE
    )
    assert isinstance(results, list)
    assert len(results) == 0
