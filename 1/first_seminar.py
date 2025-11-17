import numpy as np

class ColorTranslator:
    def __init__(self):

        pass

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


if __name__ == "__main__":

    translator = ColorTranslator()

    # Example:
    # Ask user for RGB input values
    R_in = int(input("Enter Red component (0-255): "))
    G_in = int(input("Enter Green component (0-255): "))
    B_in = int(input("Enter Blue component (0-255): "))
    
    print(f"\nRGB to YUV")
    print(f"Input RGB: ({R_in}, {G_in}, {B_in})")

    # Conversion
    Y, U, V = translator.rgb_to_yuv(R_in, G_in, B_in)
    print(f"Resulting YUV: ({Y}, {U}, {V})\n")

    # Inverse example:
    # Ask user for YUV input values
    Y_in = int(input("Enter Y component (0-255): "))
    U_in = int(input("Enter U component (0-255): "))
    V_in = int(input("Enter V component (0-255): "))

    Y_in, U_in, V_in = Y, U, V
    print(f"\nYUV to RGB")
    print(f"Input YUV: ({Y_in}, {U_in}, {V_in})")

    # Inverse Conversion
    R_out, G_out, B_out = translator.yuv_to_rgb(Y_in, U_in, V_in)
    print(f"Resulting RGB: ({R_out}, {G_out}, {B_out})\n")

    # Comparison:
    print(f"\nOriginal RGB: ({R_in}, {G_in}, {B_in})")
    print(f"Final RGB:    ({R_out}, {G_out}, {B_out})")