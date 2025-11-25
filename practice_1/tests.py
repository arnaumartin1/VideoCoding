import pytest
from httpx import AsyncClient
import numpy as np

from services import rgb_to_yuv_service, yuv_to_rgb_service, run_length_encoding
from main import app 

# Unit tests for the services functions

def test_rgb_to_yuv_service():
    R, G, B = 123, 45, 67
    
    # 1. RGB -> YUV
    yuv = rgb_to_yuv_service(R, G, B)
    Y, U, V = yuv['Y'], yuv['U'], yuv['V']
    
    # 2. YUV -> RGB
    rgb2 = yuv_to_rgb_service(Y, U, V)
    R2, G2, B2 = rgb2['R'], rgb2['G'], rgb2['B']
    
    # Assert that the original and converted RGB values are approximately equal
    assert np.isclose(R, R2, atol=2) 
    assert np.isclose(G, G2, atol=2)
    assert np.isclose(B, B2, atol=2)

def test_run_length_encoding():
    data = bytes([255, 255, 255, 0, 0, 128, 128])
    rle = run_length_encoding(data)

    # Assert the RLE output is as expected
    assert rle == [(3, 255), (2, 0), (2, 128)]

@pytest.mark.asyncio
async def test_api_rgb_to_yuv_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/convert/rgb_to_yuv/", json={"R": 255, "G": 0, "B": 0})
    
    assert response.status_code == 200
    # Verify the returned YUV values for pure red
    assert response.json() == {'Y': 68, 'U': 85, 'V': 255}