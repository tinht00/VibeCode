import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from background_remover import BackgroundRemover
from main import app
from fastapi.testclient import TestClient
from PIL import Image
import io

client = TestClient(app)

@pytest.fixture
def mock_upload_file(tmp_path):
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_ai_removal_import_check():
    """Kiểm tra logic ưu tiên AI trong auto mode."""
    with patch("background_remover.HAS_REMBG", True):
        remover = BackgroundRemover()
        # Mock load
        remover.image = Image.new('RGB', (100, 100), color='white')
        
        with patch("background_remover.rembg_remove") as mock_remove:
            # Mock return value of rembg_remove (should return PIL Image)
            mock_remove.return_value = Image.new('RGBA', (100, 100), color=(0,0,0,0))
            
            remover.remove_background(method="auto")
            mock_remove.assert_called_once()


def test_batch_processing_endpoint(mock_upload_file):
    """Test endpoint xử lý hàng loạt trả về ZIP."""
    files = [
        ('files', ('test1.png', mock_upload_file, 'image/png')),
        ('files', ('test2.png', mock_upload_file, 'image/png'))
    ]
    
    # Mock BackgroundRemover methods to avoid heavy processing
    with patch("background_remover.BackgroundRemover.remove_background") as mock_remove:
         # Mock rembg/ai if needed, or just default method
         response = client.post(
             "/api/batch/remove-background",
             files=files,
             data={"method": "edge"} # Use simple method for speed
         )
         
         assert response.status_code == 200
         assert response.headers["content-type"] == "application/zip"
         assert "results.zip" in response.headers["content-disposition"]
         
         # Verify content
         import zipfile
         with zipfile.ZipFile(io.BytesIO(response.content)) as z:
             assert len(z.namelist()) == 2
             assert "test1_nobg.png" in z.namelist()

def test_batch_limit_error(mock_upload_file):
    """Test giới hạn số lượng file upload."""
    files = [('files', ('test.png', mock_upload_file, 'image/png'))] * 15
    response = client.post("/api/batch/remove-background", files=files)
    assert response.status_code == 400 # Custom Error Response
