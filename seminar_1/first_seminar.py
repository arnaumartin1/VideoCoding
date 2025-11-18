import numpy as np
import subprocess
from PIL import Image
from scipy.fftpack import dct, idct
import os
import unittest




class ColorTranslator:
    def __init__(self):

        pass

    # Exercise 2

    def rgb_to_yuv(self, R: int, G: int, B: int) -> tuple:

        Y = 0.257 * R + 0.504 * G + 0.098 * B + 16
        U = -0.148 * R - 0.291 * G + 0.439 * B + 128
        V = 0.439 * R - 0.368 * G - 0.071 * B + 128

        # The values should be clipped to the range [0, 255]
        Y = np.clip(round(Y), 0, 255)
        U = np.clip(round(U), 0, 255)
        V = np.clip(round(V), 0, 255)

        return (int(Y), int(U), int(V))

    def yuv_to_rgb(self, Y: int, U: int, V: int) -> tuple:
    
        B = 1.164 * (Y - 16) + 2.018 * (U - 128)
        G = 1.164 * (Y - 16) - 0.813 * (V - 128) - 0.391 * (U - 128)
        R = 1.164 * (Y - 16) + 1.596 * (V - 128)

        return (int(R), int(G), int(B))
    
    

    # Exercise 3

    def ResizeImages(self, imagePath, outputPath, targetWidth, targetHeight):

        if targetWidth >= 0 or targetHeight >= 0: # Si son enters positius

            # Command per a consola de ffmpeg amb els paths i dimensions
            consoleString = f"ffmpeg -y -i \"{imagePath}\" -vf scale={targetWidth}:{targetHeight} \"{outputPath}\" -loglevel error"
            subprocess.run(consoleString, shell=True, check=True) # Executa la comanda
        else:             
            print("Target width and height must be positive integers.")


    # Exercise 4

    def Serpentine(self,imagePath) -> int:
        image = Image.open(imagePath)
        data = np.array(image) 
        height, width, _ = data.shape

        # Creem un array per guardar els píxels en ordre diagonal zig-zag
        serpentine = []

        for d in range(width + height - 1):  # recorrem cada diagonal
            for y in range(max(0, d - width + 1), min(height, d + 1)):
                x = d - y
                if d % 2 == 0: # diagonal parell: de dalt a baix
                    serpentine.append(data[y, x])
                else: # diagonal imparell: de baix a dalt
                    serpentine.append(data[height - 1 - y, width - 1 - x])  

        # Convertim a bytes
        byte_data = np.array(serpentine, dtype=np.uint8).tobytes()
        return len(byte_data)
    
    # Exercise 5a

    def BlackWhiteCompression(self, imagePath, outputPath):

        consoleString = f"ffmpeg -y -i \"{imagePath}\" -vf format=gray  -pix_fmt gray -q:v 31 \"{outputPath}\" -loglevel error"
        subprocess.run(consoleString, shell=True, check=True)

        print("\nBlack and white compression completed.")
        print("The filter '-vf format=gray' converts the image to grayscale by removing color information.")
        print("The parameter '-q:v 31' sets the worst possible quality for the output.")
        print("This leads to a smaller file size and a significant loss of detail.")


    # Exercise 5b

    def run_length_encoding(self, bytes: bytes) -> list:
        
        i = 0
        encoded_bytes = []

        while i < len(bytes):
            value = bytes[i]
            count = 1
            while i + count < len(bytes) and bytes[i] == bytes[i + count]:
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
    
    def Decode(self,dctData):
        idctData = idct(idct(dctData.T, norm='ortho').T, norm='ortho') # 2D IDCT
        idctData = np.clip(idctData, 0, 255)
        
        # decoded image
        decodedImg = Image.fromarray(np.uint8(idctData))
        decodedImg.save("/Users/arnaumartin/VideoCoding/seminar_1/decoded_image.jpg") # Ens guardem la imatge decodificada
        return idctData

    
# Exercise 7

# Exercise 8: Unit tests

class TestColorTranslator(unittest.TestCase):
    def setUp(self):
        self.translator = ColorTranslator()
        # Path de la imatge GOAT
        self.test_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT.jpg"
        self.output_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT_test_output.jpg"
        self.bw_output_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT_bw_test.jpg"

    def tearDown(self):
        # Neteja fitxers generats
        for path in [self.output_path, self.bw_output_path]:
            if os.path.exists(path):
                os.remove(path)

    # Exercise 2
    def test_rgb_to_yuv_and_back(self):
        R, G, B = 123, 45, 67
        Y, U, V = self.translator.rgb_to_yuv(R, G, B)
        R2, G2, B2 = self.translator.yuv_to_rgb(Y, U, V)
        self.assertAlmostEqual(R, R2, delta=2)
        self.assertAlmostEqual(G, G2, delta=2)
        self.assertAlmostEqual(B, B2, delta=2)

    # Exercise 3
    def test_resize_images(self):
        self.translator.ResizeImages(self.test_image_path, self.output_path, 50, 50)
        self.assertTrue(os.path.exists(self.output_path))
        img = Image.open(self.output_path)
        self.assertEqual(img.size, (50, 50))

    # Exercise 4
    def test_serpentine(self):
        byte_len = self.translator.Serpentine(self.test_image_path)
        img = Image.open(self.test_image_path)
        width, height = img.size
        self.assertEqual(byte_len, width * height * 3)  

    # Exercise 5a
    def test_blackwhite_compression(self):
        self.translator.BlackWhiteCompression(self.test_image_path, self.bw_output_path)
        self.assertTrue(os.path.exists(self.bw_output_path))
        img = Image.open(self.bw_output_path).convert("L")
        self.assertEqual(img.mode, "L")

    # Exercise 5b
    def test_run_length_encoding(self):
        data = bytes([255, 255, 255, 0, 0, 128, 128])
        rle = self.translator.run_length_encoding(data)
        self.assertEqual(rle, [(3, 255), (2, 0), (2, 128)])


class TestDCT(unittest.TestCase):
    # Fem un setup semblant per a l'altra classe creada
    def setUp(self):
        self.converter = DCT()
        self.test_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT.jpg"
        self.decoded_path = "/Users/arnaumartin/VideoCoding/seminar_1/decoded_image_test.jpg"

    def tearDown(self):
        if os.path.exists(self.decoded_path):
            os.remove(self.decoded_path)

    def test_encode_decode(self):
        dct_data = self.converter.Encode(self.test_image_path)
        idct_data = self.converter.Decode(dct_data)
        self.assertTrue(np.all((idct_data >= 0) & (idct_data <= 255)))



# Main execution


if __name__ == "__main__":
    unittest.main()
    
    # # Eercise 1 Test
    # # Ask user for RGB input values
    # R_in = int(input("Enter Red component (0-255): "))
    # G_in = int(input("Enter Green component (0-255): "))
    # B_in = int(input("Enter Blue component (0-255): "))
    # Eercise 2 Test
    # Ask user for RGB input values
    # R_in = int(input("Enter Red component (0-255): "))
    # G_in = int(input("Enter Green component (0-255): "))
    # B_in = int(input("Enter Blue component (0-255): "))
    
    # print(f"\nRGB to YUV")
    # print(f"Input RGB: ({R_in}, {G_in}, {B_in})")

    # # Conversion
    # Y, U, V = translator.rgb_to_yuv(R_in, G_in, B_in)
    # print(f"Resulting YUV: ({Y}, {U}, {V})\n")

    # # Inverse example:
    # # Ask user for YUV input values
    # Y_in = int(input("Enter Y component (0-255): "))
    # U_in = int(input("Enter U component (0-255): "))
    # V_in = int(input("Enter V component (0-255): "))

    # Y_in, U_in, V_in = Y, U, V
    # print(f"\nYUV to RGB")
    # print(f"Input YUV: ({Y_in}, {U_in}, {V_in})")

    # # Inverse Conversion
    # R_out, G_out, B_out = translator.yuv_to_rgb(Y_in, U_in, V_in)
    # print(f"Resulting RGB: ({R_out}, {G_out}, {B_out})\n")

    # # Comparison:
    # print(f"\nOriginal RGB: ({R_in}, {G_in}, {B_in})")
    # print(f"Final RGB:    ({R_out}, {G_out}, {B_out})")


    # Exercise 2 Test

    # input_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT.jpg"
    # output_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT_resized.jpg"
    # target_width = int(input("Enter target width: "))
    # target_height = int(input("Enter target height: "))
    # translator.ResizeImages(input_image_path, output_image_path, target_width, target_height)

    # Exercise 3 Test
    # input_image_path = "/Users/Eric/Downloads/VideoCoding/seminar_1/GOAT.jpg"
    # output_image_path = "/Users/Eric/Downloads/VideoCoding/seminar_1/GOAT_resized.jpg"
    # target_width = int(input("Enter target width: "))
    # target_height = int(input("Enter target height: "))
    # translator.ResizeImages(input_image_path, output_image_path, target_width, target_height)


    # Exercise 4 Test
    # input_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT.jpg"
    # serpentine_data = translator.Serpentine(input_image_path)
    # print(f"Serpentine byte data length: {(serpentine_data)}")


    # # Exercise 5a Test
    # input_image_path = "/Users/Eric/Downloads/VideoCoding/seminar_1/GOAT.jpg"
    # bw_output_image_path = "/Users/Eric/Downloads/VideoCoding/seminar_1/GOAT_bw_compressed.jpg"
    # translator.BlackWhiteCompression(input_image_path, bw_output_image_path)


    # # Exercise 5b Test
    # input_data = [255, 255, 255, 0, 0, 0, 0, 128, 128, 128, 128, 128, 255]
    # print(f"Original Data ({len(input_data)} elements):")
    # print(input_data)
    
    # # Codification
    # rle_encoded = translator.run_length_encoding(input_data)
    # print("\nCodification by RLE:")
    # print(rle_encoded)

    # # Exercise 6 Test

    # input_image_path = "/Users/arnaumartin/VideoCoding/seminar_1/GOAT.jpg"

    # converter = DCT()
    # encoded = converter.Encode(input_image_path)
    # decoded = converter.Decode(encoded)

    # print("Original Data:\n", np.array(Image.open(input_image_path)))
    # print("DCT Encoded:\n", encoded)
    # print("Decoded Data:\n", decoded)




    

    