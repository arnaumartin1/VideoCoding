import numpy as np
import subprocess
from PIL import Image
from scipy.fftpack import dct, idct
import os
import unittest
import pywt





class ColorTranslator:
    def __init__(self):

        pass

    # Exercise 2

    def rgb_to_yuv(R: int, G: int, B: int) -> dict:

        Y = 0.257 * R + 0.504 * G + 0.098 * B + 16
        U = -0.148 * R - 0.291 * G + 0.439 * B + 128
        V = 0.439 * R - 0.368 * G - 0.071 * B + 128

        # The values should be clipped to the range [0, 255]
        Y = np.clip(round(Y), 0, 255)
        U = np.clip(round(U), 0, 255)
        V = np.clip(round(V), 0, 255)

        return {"Y": int(Y), "U": int(U), "V": int(V)}

    def yuv_to_rgb(Y: int, U: int, V: int) -> dict:
    
        B = 1.164 * (Y - 16) + 2.018 * (U - 128)
        G = 1.164 * (Y - 16) - 0.813 * (V - 128) - 0.391 * (U - 128)
        R = 1.164 * (Y - 16) + 1.596 * (V - 128)

        return {"R": int(R), "G": int(G), "B": int(B)}
    
    
    # Exercise 3

    def ResizeImages(self, imagePath, outputPath, targetWidth, targetHeight):

        if targetWidth >= 0 or targetHeight >= 0: # If they are positive integers

            # Command to be executed in the console to resize the image using ffmpeg
            consoleString = f"ffmpeg -y -i \"{imagePath}\" -vf scale={targetWidth}:{targetHeight} \"{outputPath}\" -loglevel error"
            subprocess.run(consoleString, shell=True, check=True) # Executa la comanda
        else:             
            print("Target width and height must be positive integers.")


    # Exercise 4

    def Serpentine(self,imagePath) -> int:
        image = Image.open(imagePath)
        data = np.array(image) 
        height, width, _ = data.shape

        # Create an array to store pixels in zig-zag diagonal order
        serpentine = []

        for d in range(width + height - 1):  # iterate over each diagonal
            for y in range(max(0, d - width + 1), min(height, d + 1)):
                x = d - y
                if d % 2 == 0: # even diagonal: top to bottom
                    serpentine.append(data[y, x])
                else: # odd diagonal: bottom to top
                    serpentine.append(data[height - 1 - y, width - 1 - x])  

        # Convert to bytes
        byte_data = np.array(serpentine, dtype=np.uint8).tobytes()
        return len(byte_data)
    

    # Exercise 5a

    def BlackWhiteCompression(self, imagePath, outputPath):

        consoleString = f"ffmpeg -y -i \"{imagePath}\" -vf format=gray  -pix_fmt gray -q:v 31 \"{outputPath}\" -loglevel error" # Command to compress in black and white and low quality
        subprocess.run(consoleString, shell=True, check=True)

        print("\nBlack and white compression completed.")
        print("The filter '-vf format=gray' converts the image to grayscale by removing color information.")
        print("The parameter '-q:v 31' sets the worst possible quality for the output.")
        print("This leads to a smaller file size and a significant loss of detail.\n")


    # Exercise 5b

    def run_length_encoding(self, bytes: bytes) -> list:
        
        i = 0
        encoded_bytes = []

        while i < len(bytes):
            value = bytes[i] # Current byte value
            count = 1
            while i + count < len(bytes) and bytes[i] == bytes[i + count]: # Count occurrences
                count += 1

            encoded_bytes.append((count, value))
            i += count
        return encoded_bytes
            
    
    # Exercise 6
    
class DCT:
    def __init__(self):
        pass

    def Encode(self, inputPath):
        image = Image.open(inputPath)
        data = np.array(image)

        dctData = dct(dct(data.T, norm='ortho').T, norm='ortho') # 2D DCT
        return dctData
    
    def Decode(self, dctData, save_path=None):
        idctData = idct(idct(dctData.T, norm='ortho').T, norm='ortho') # 2D IDCT
        idctData = np.clip(idctData, 0, 255)
        
        # Decoded image
        decodedImg = Image.fromarray(np.uint8(idctData))
        decodedImg.save("/Users/Eric/Downloads/VideoCoding/seminar_1/dct_decoded_image.jpg") # Save the decoded image
        return idctData

    
    # Exercise 7

class DWT:
    def __init__(self, wavelet='haar', level=1):
        # Choosing the wavelet type and decomposition level
        self.wavelet = wavelet
        self.level = level

    def Encode(self, inputPath):
        image = Image.open(inputPath).convert('RGB')  # Ensure image is in RGB mode
        data = np.array(image)

        # Separate channels
        channels = [data[:, :, i] for i in range(3)]
        encoded_coeffs = []
        for channel in channels:
            coeffs = pywt.wavedec2(channel, wavelet=self.wavelet, level=self.level) # 2D DWT
            encoded_coeffs.append(coeffs)

        return encoded_coeffs
    
    def Decode(self, coeffs, save_path=None):
        decoded_channels = []
        for channel_coeffs in coeffs:
            reconstructed = pywt.waverec2(channel_coeffs, wavelet=self.wavelet) # 2D IDWT
            reconstructed = np.clip(reconstructed, 0, 255) # Clipping values to valid range
            decoded_channels.append(reconstructed)

        idwtData = np.stack(decoded_channels, axis=-1)  # Reconstruct the image from channels
        
        # Decoded image
        decodedImg = Image.fromarray(np.uint8(idwtData))
        decodedImg.save("/Users/Eric/Downloads/VideoCoding/seminar_1/dwt_decoded_image.jpg") # Save the decoded image
        return idwtData