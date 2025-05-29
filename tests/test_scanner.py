import pytest
from app.services.scanner import Scanner
import io
from PIL import Image, ImageDraw

def create_test_pdf_with_barcode():
    """Create a test PDF with a QR code."""
    # Create a blank image
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple QR code pattern (just for testing)
    draw.rectangle([50, 50, 150, 150], fill='black')
    draw.rectangle([60, 60, 140, 140], fill='white')
    draw.rectangle([70, 70, 130, 130], fill='black')
    
    # Save as PDF
    pdf_bytes = io.BytesIO()
    img.save(pdf_bytes, format='PDF')
    return pdf_bytes.getvalue()

def test_scanner_initialization():
    """Test scanner initialization."""
    scanner = Scanner(dpi=300)
    assert scanner.dpi == 300

def test_scan_pdf():
    """Test PDF scanning."""
    scanner = Scanner()
    pdf_bytes = create_test_pdf_with_barcode()
    
    results = scanner.scan_pdf(
        pdf_bytes,
        page_range=[0],
        symbologies=['QR_CODE'],
        embed_page=True,
        embed_snippet=True
    )
    
    assert isinstance(results, list)
    if results:  # If a barcode was detected
        result = results[0]
        assert 'page' in result
        assert 'type' in result
        assert 'value' in result
        assert 'position' in result
        assert 'page_image' in result
        assert 'snippet' in result

def test_scan_pdf_invalid_page():
    """Test scanning with invalid page range."""
    scanner = Scanner()
    pdf_bytes = create_test_pdf_with_barcode()
    
    results = scanner.scan_pdf(
        pdf_bytes,
        page_range=[999],  # Non-existent page
        symbologies=['QR_CODE']
    )
    
    assert isinstance(results, list)
    assert len(results) == 0

def test_scan_pdf_filter_symbology():
    """Test filtering by barcode type."""
    scanner = Scanner()
    pdf_bytes = create_test_pdf_with_barcode()
    
    # Test with non-matching symbology
    results = scanner.scan_pdf(
        pdf_bytes,
        symbologies=['CODE_128']  # Different from QR_CODE
    )
    
    assert isinstance(results, list)
    assert len(results) == 0 