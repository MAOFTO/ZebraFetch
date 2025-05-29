import io
import base64
from typing import List, Dict, Any, Optional
import pypdfium2 as pdfium
import zxingcpp
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Scanner:
    """Service for scanning PDFs and extracting barcodes."""
    
    def __init__(self, dpi: int = 300):
        """Initialize scanner with specified DPI."""
        self.dpi = dpi
    
    def scan_pdf(
        self,
        pdf_bytes: bytes,
        page_range: Optional[List[int]] = None,
        symbologies: Optional[List[str]] = None,
        embed_page: bool = False,
        embed_snippet: bool = False
    ) -> List[Dict[str, Any]]:
        """Scan PDF and extract barcodes."""
        logger.debug(f"Starting PDF scan with symbologies: {symbologies}")
        doc = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
        results = []
        
        # Determine page range
        if not page_range:
            page_range = range(len(doc))
        
        # Process each page
        for page_idx in page_range:
            if page_idx >= len(doc):
                continue
                
            logger.debug(f"Processing page {page_idx + 1}")
            page = doc.get_page(page_idx)
            pil_image = page.render(scale=self.dpi/72).to_pil()
            
            # Find barcodes
            barcodes = zxingcpp.read_barcodes(pil_image)
            logger.debug(f"Found {len(barcodes)} barcodes on page {page_idx + 1}")
            
            if not barcodes:
                continue
            
            # Process each barcode
            for barcode in barcodes:
                barcode_format = str(barcode.format)
                logger.debug(f"Found barcode of type: {barcode_format}")
                
                # Calculate position and dimensions from corner points
                x = barcode.position.top_left.x
                y = barcode.position.top_left.y
                width = barcode.position.top_right.x - barcode.position.top_left.x
                height = barcode.position.bottom_left.y - barcode.position.top_left.y

                result = {
                    "page": page_idx + 1,  # 1-based page numbers
                    "type": barcode_format,
                    "value": barcode.text,
                    "position": {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height
                    }
                }
                
                # Filter by symbology if specified
                if symbologies:
                    logger.debug(f"Checking if {barcode_format} is in {symbologies}")
                    if barcode_format not in symbologies:
                        logger.debug(f"Skipping barcode - format {barcode_format} not in requested symbologies")
                        continue
                    logger.debug(f"Keeping barcode - format {barcode_format} matches requested symbologies")
                
                # Embed page image if requested
                if embed_page:
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    result["page_image"] = base64.b64encode(
                        img_byte_arr.getvalue()
                    ).decode()
                
                # Embed barcode snippet if requested
                if embed_snippet:
                    snippet = pil_image.crop((x, y, x + width, y + height))
                    img_byte_arr = io.BytesIO()
                    snippet.save(img_byte_arr, format='PNG')
                    result["snippet"] = base64.b64encode(
                        img_byte_arr.getvalue()
                    ).decode()
                
                results.append(result)
        
        logger.debug(f"Scan complete. Found {len(results)} matching barcodes")
        return results 