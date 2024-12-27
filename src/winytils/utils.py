import ctypes
import time
import traceback
from ctypes import wintypes

import win32con
import win32gui

try:
    from PIL import Image
except:
    print("Pillow lib is not installed")


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", ctypes.c_bool),  # Specifies whether this structure defines an icon or a cursor
        ("xHotspot", ctypes.c_ulong),  # The x-coordinate of a cursor's hot spot
        ("yHotspot", ctypes.c_ulong),  # The y-coordinate of a cursor's hot spot
        ("hbmMask", ctypes.c_void_p),  # Handle to the icon/cursor mask bitmap
        ("hbmColor", ctypes.c_void_p),  # Handle to the icon/cursor color bitmap
    ]


def _get_icon_info(h_icon):
    icon_info = ICONINFO()
    ctypes.windll.user32.GetIconInfo(h_icon, ctypes.byref(icon_info))
    return icon_info


def _get_bitmap_bits(hbm, width, height):
    """
    Retrieve raw bitmap data using ctypes and the GetBitmapBits API.
    """
    buffer_len = width * height * 4  # 4 bytes per pixel (RGBA)
    buffer = ctypes.create_string_buffer(buffer_len)

    hbm = wintypes.HBITMAP(hbm)

    # Call GetBitmapBits from the GDI API
    success = ctypes.windll.gdi32.GetBitmapBits(hbm, buffer_len, buffer)
    if not success:
        raise RuntimeError("Failed to retrieve bitmap bits.")

    return buffer.raw


def _get_window_icon(hwnd) -> "Image":
    h_icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0)
    if not h_icon:
        h_icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0)
    if not h_icon:
        # In most cases this thing works. .Returnes 40x40 image
        h_icon = ctypes.windll.user32.GetClassLongPtrW(hwnd, win32con.GCL_HICON)
    if not h_icon:
        raise ValueError("No icon found for this window.")

    # Get ICONINFO structure
    icon_info = _get_icon_info(h_icon)

    # Extract color and mask bitmaps
    hbm_color = icon_info.hbmColor
    hbm_mask = icon_info.hbmMask

    # Get dimensions from the color bitmap
    bmp_info = win32gui.GetObject(hbm_color)
    width, height = bmp_info.bmWidth, bmp_info.bmHeight

    # Create a device context for drawing
    hdc = win32gui.GetDC(0)
    hdc_mem = win32gui.CreateCompatibleDC(hdc)
    win32gui.SelectObject(hdc_mem, hbm_color)

    # Extract raw pixel data
    bmp_bits = _get_bitmap_bits(hbm_color, width, height)
    img = Image.frombuffer("RGBA", (width, height), bmp_bits, "raw", "BGRA", 0, 1)

    # Release resources
    win32gui.DeleteObject(hbm_color)
    win32gui.DeleteObject(hbm_mask)
    win32gui.DeleteDC(hdc_mem)
    win32gui.ReleaseDC(0, hdc)

    return img.resize((40, 40))


# import win32gui
# import win32ui
# import win32con
# import time
# from PIL import Image
# import os
# import ctypes


# def get_window_icon(hwnd):
#     # NEVER SEEN THIS ICON BEEN FOUND
#     h_icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0)
#     if not h_icon:
#         # NEVER SEEN THIS ICON BEEN FOUND
#         h_icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0)
#     if not h_icon:
#         # ALWAYS FOUND THIS OR NONE
#         h_icon = ctypes.windll.user32.GetClassLongPtrW(hwnd, win32con.GCL_HICON)
#     if not h_icon:
#         raise ValueError("No icon found for this window.")

#     hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
#     hdc_mem = hdc.CreateCompatibleDC()
#     bmp = win32ui.CreateBitmap()
#     bmp.CreateCompatibleBitmap(hdc, 256, 256)  # Allocate enough space for a large icon
#     hdc_mem.SelectObject(bmp)

#     # Draw the icon into the bitmap
#     win32gui.DrawIconEx(hdc_mem.GetHandleOutput(), 0, 0, h_icon, 256, 256, 0, None, win32con.DI_NORMAL)

#     # Save the bitmap as an image file
#     bmp_info = bmp.GetInfo()
#     bmp_data = bmp.GetBitmapBits(True)
#     win32gui.DeleteObject(bmp.GetHandle())
#     hdc_mem.DeleteDC()
#     hdc.DeleteDC()
#     image = Image.frombuffer("RGB", (bmp_info["bmWidth"], bmp_info["bmHeight"]), bmp_data, "raw", "BGRX", 0, 1)
#     return image


# def main():

#     from winytils.windows import Windows

#     # Find the target window
#     # hwnd = win32gui.GetForegroundWindow()
#     window = Windows.foregrond()
#     if not window:
#         print("Window not found!")
#         return

#     if window.is_uwp():
#         child = window.uwp_child
#         if child:
#             window = child

#     try:
#         img = get_window_icon(window.hwnd)
#         img.save("i.png")
#     except Exception as e:
#         print(f"Error: {e}")


# if __name__ == "__main__":
#     time.sleep(3)
#     main()
