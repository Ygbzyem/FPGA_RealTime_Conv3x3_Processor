"""
=============================================================================
compare_my_image.py
-----------------------------------------------------------------------------
Script CHAY TRUC TIEP. Copy 1 trong 6 khoi config (tu file
config_blocks_6runs.py) DAN DE vao vung "SUA CAC DUONG DAN" ben duoi,
roi chay:

    python3 compare_my_image.py

Lam du 6 lan (moi lan dan 1 khoi khac vao) - du lieu se CONG DON vao
verification_logs/, khong ghi de.
=============================================================================
"""

from golden_model import verify_from_input_hex, print_log_summary

# =============================================================================
# >>> SUA CAC DUONG DAN + NHAN O DAY <<<
# Dan de 1 trong 6 khoi tu config_blocks_6runs.py vao thay the 6 dong duoi day
# =============================================================================

# ---------- KHOI 1: 64x64 - ADDER TREE ----------
INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/64x64/adder_tree/input_data_64.hex"
RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/64x64/adder_tree/output_sharp_64.hex"
RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/64x64/adder_tree/output_blur_64.hex"
IMG_SIZE       = 64
RUN_LABEL      = "64x64_adder"
ARCHITECTURE   = "Adder Tree"

 
# ---------- KHOI 2: 64x64 - SYSTOLIC ARRAY ----------
#INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/64x64/systolic_array/input_data_64.hex"
#RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/64x64/systolic_array/output_sharp_64.hex"
#RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/64x64/systolic_array/output_blur_64.hex"
#IMG_SIZE       = 64
#RUN_LABEL      = "64x64_systolic"
#ARCHITECTURE   = "Systolic Array"
 
 
# ---------- KHOI 3: 128x128 - ADDER TREE ----------
#INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/128x128/adder_tree/input_data_128.hex"
#RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/128x128/adder_tree/output_sharp_128.hex"
#RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/128x128/adder_tree/output_blur_128.hex"
#IMG_SIZE       = 128
#RUN_LABEL      = "128x128_adder"
#ARCHITECTURE   = "Adder Tree"
 
 
# ---------- KHOI 4: 128x128 - SYSTOLIC ARRAY ----------
#INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/128x128/systolic_array/input_data_128.hex"
#RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/128x128/systolic_array/output_sharp_128.hex"
#RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/128x128/systolic_array/output_blur_128.hex"
#IMG_SIZE       = 128
#RUN_LABEL      = "128x128_systolic"
#ARCHITECTURE   = "Systolic Array"
 
 
# ---------- KHOI 5: 256x256 - ADDER TREE ----------
#INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/256x256/adder_tree/input_data_256.hex"
#RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/256x256/adder_tree/output_sharp_256.hex"
#RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/256x256/adder_tree/output_blur_256.hex"
#IMG_SIZE       = 256
#RUN_LABEL      = "256x256_adder"
#ARCHITECTURE   = "Adder Tree"
 
 
# ---------- KHOI 6: 256x256 - SYSTOLIC ARRAY ----------
#INPUT_HEX_PATH = "C:/Users/tungd/OneDrive/Desktop/results/256x256/systolic_array/input_data_256.hex"
#RTL_SHARP_HEX  = "C:/Users/tungd/OneDrive/Desktop/results/256x256/systolic_array/output_sharp_256.hex"
#RTL_BLUR_HEX   = "C:/Users/tungd/OneDrive/Desktop/results/256x256/systolic_array/output_blur_256.hex"
#IMG_SIZE       = 256
#RUN_LABEL      = "256x256_systolic"
#ARCHITECTURE   = "Systolic Array"

# =============================================================================
# NGUONG PASS/FAIL - KHONG CAN SUA
# =============================================================================
PASS_THRESHOLD = 95.0

# =============================================================================
# TU DONG CHAY - KHONG CAN SUA PHAN DUOI NAY
# =============================================================================

if __name__ == "__main__":
    print(f"Dang so sanh '{RUN_LABEL}' ({ARCHITECTURE}) voi ket qua RTL...\n")
    results = verify_from_input_hex(
        input_hex_path=INPUT_HEX_PATH,
        rtl_sharp_hex_path=RTL_SHARP_HEX,
        rtl_blur_hex_path=RTL_BLUR_HEX,
        size=IMG_SIZE,
        run_label=RUN_LABEL,
        architecture=ARCHITECTURE,
        pass_threshold=PASS_THRESHOLD,
    )

    print("\n=====================================================")
    if results.get('sharpen', {}).get('PASS') and results.get('blur', {}).get('PASS'):
        print("KET QUA: PASS - RTL khop bit-exact voi golden model")
    else:
        print("KET QUA: CO SAI LECH - xem chi tiet match_rate_pct o tren")
        print("Anh diff_sharp.png / diff_blur.png trong thu muc real_image_check/")
        print("se cho thay CHINH XAC pixel nao bi sai (cang sang = cang lech nhieu)")
    print("=====================================================\n")

    # In bang tong hop tat ca cac lan da chay tu truoc den gio
    print_log_summary()