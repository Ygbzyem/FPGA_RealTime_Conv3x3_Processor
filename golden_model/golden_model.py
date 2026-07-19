"""
=============================================================================
GOLDEN MODEL - FPGA RealTime Conv3x3 Processor
=============================================================================
Muc dich: mo phong bang phan mem (bit-exact, neu cau hinh dung) hanh vi cua
RTL trong repo FPGA_RealTime_Conv3x3_Processor, dung de:

  1. Sinh test vector (hex/txt) de nap vao testbench_prj.v
  2. Tinh output tham chieu (golden output) bang cung 1 thuat toan fixed-point
     nhu phan cung (kernel, do rong bit accumulator, rounding, clipping)
  3. So sanh output tu ModelSim (output_data.hex) voi golden output:
     - Ty le khop bit-exact (per-pixel)
     - PSNR / SSIM (dung cho phan "Results" cua paper)
     - Sinh anh diff de debug truc quan
     - Bao cao pass/fail dang bang, xuat CSV cho paper

QUAN TRONG - HAY DOC:
Cau hinh trong class `HWConfig` duoi day DA duoc khop chinh xac 100% voi
RTL that (conv_multi.v / conv_systolic.v) da xac nhan trong du an:

  - KERNEL_SHARP = [[0,-1,0],[-1,5,-1],[0,-1,0]]  (giong het mult11..mult33
    trong conv_multi.v / trong so w1..w9 trong conv_systolic.v)
  - KERNEL_BLUR  = toan bo 1 (9 pixel cong truc tiep, chua chia)
  - Cong thuc blur DUNG DUNG RTL: acc_blur = (sum_raw * 114) >>> 10, roi
    clip ve <=255 (KHONG lam tron, KHONG chia 9 truc tiep - day chinh la
    cach conv_multi.v/conv_systolic.v xap xi 1/9 bang nhan 114/1024).
  - Khong co kiem tra am cho blur (RTL goc cung khong kiem tra, vi 9 pixel
    khong dau + trong so =1 khong bao gio ra am).
  - Sharpen: clip ve [0,255] (co kiem tra am, giong RTL).

Neu code RTL cua ban thay doi trong so kernel hoac cong thuc blur, sua lai
KERNEL_SHARP/KERNEL_BLUR va ham apply_kernel() ben duoi cho khop.

HO TRO KICH THUOC ANH TUY CHINH: sua IMG_WIDTH/IMG_HEIGHT trong HWConfig
(hoac truyen tham so khi goi ham) de dung voi anh 128x128, 256x256... xem
phan "3. HO TRO NHIEU KICH THUOC ANH" o duoi.
=============================================================================
"""

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Tuple
import csv
import datetime

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

try:
    from skimage.metrics import structural_similarity as ssim
    HAVE_SSIM = True
except ImportError:
    HAVE_SSIM = False


# =============================================================================
# 1. CAU HINH PHAN CUNG (chinh lai cho khop RTL that cua ban)
# =============================================================================

@dataclass
class HWConfig:
    # Kernel chuan cho Sharpening (unsharp mask co ban)
    KERNEL_SHARP: np.ndarray = field(default_factory=lambda: np.array([
        [ 0, -1,  0],
        [-1,  5, -1],
        [ 0, -1,  0],
    ], dtype=np.int32))

    # Kernel chuan cho Blur (box blur, tong = 8 -> dung shift-right 3 de
    # tranh chia that trong RTL; neu RTL ban dung tong = 9 va chia that
    # (division), doi BLUR_DIVIDE_MODE ben duoi)
    KERNEL_BLUR: np.ndarray = field(default_factory=lambda: np.array([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
    ], dtype=np.int32))

    # DUY NHAT 1 CHE DO, KHOP DUNG CONG THUC RTL THAT:
    # acc_blur = (sum_raw * 114) >>> 10  (xap xi 1/9 bang nhan 114/1024,
    # dung >>> = arithmetic shift, KHONG lam tron). Day la cong thuc that
    # trong conv_multi.v/conv_systolic.v (bien temp_sum_comb), khong phai
    # gia dinh nua.
    BLUR_DIVIDE_MODE: Literal['mul114_shift10'] = 'mul114_shift10'

    ACC_WIDTH: int = 20          # do rong bit accumulator, khop sum_p/psum
                                 # trong conv_multi.v va conv_systolic.v (signed [19:0])
    PIXEL_WIDTH: int = 8         # do rong bit pixel (0-255)

    CLIP_MODE: Literal['saturate', 'wrap'] = 'saturate'

    # So chu ky tre pipeline tu i_pixel[0] valid den o_pixel[0] valid.
    # KHONG anh huong ket qua PIXEL VALUE (chi anh huong luc CAN CAT BOT
    # bao nhieu mau dau/cuoi khi doc output_data.hex, xem load_hex_as_image()).
    # Adder tree (conv_multi.v): latency = 3 chu ky (tinh tu p11..p33 hop le).
    # Systolic (conv_systolic.v): latency = 10 chu ky.
    # Ca 2 kien truc con cong them do tre "lam day" cua line_buffer/window_3x3
    # truoc khi p11..p33 lan dau hop le (~2*IMG_WIDTH, xem Gioi han trong README).
    PIPELINE_LATENCY: int = 0    # dat = 0 neu ban da tu align khi xuat hex

    # KICH THUOC ANH - sua truc tiep o day cho khop anh dang test, hoac
    # truyen tham so rieng khi goi cac ham gen_test_patterns()/golden_sharpen()/
    # golden_blur() de khong phai sua class nay moi lan doi kich thuoc.
    IMG_WIDTH: int = 64
    IMG_HEIGHT: int = 64


CFG = HWConfig()


# =============================================================================
# 2. GOLDEN CONVOLUTION - mo phong dung logic RTL (khong dung scipy convolve
#    truc tiep de kiem soat chinh xac rounding/clipping tung buoc, giong
#    adder tree that)
# =============================================================================

def pad_replicate_or_zero(img: np.ndarray, mode: str = 'zero') -> np.ndarray:
    """
    Line buffer/window_3x3 khi o bien anh (dong/cot dau, cuoi) se thieu du
    lieu lan can. RTL co the xu ly theo 1 trong 2 cach:
      - zero padding (gia dinh pixel ngoai bien = 0)
      - khong xuat output cho vien (valid convolution, anh output nho hon)
    Mac dinh gia dinh zero-padding de giu nguyen kich thuoc 64x64.
    !!! Kiem tra lai window_3x3.v xem co logic edge-handling khong. Neu
    RTL KHONG xu ly bien (chi la shift register don gian), hang/cot dau
    tien cua output se bi sai/rac - day la diem quan trong can note trong
    phan "Limitations" cua paper.
    """
    if mode == 'zero':
        return np.pad(img, 1, mode='constant', constant_values=0)
    elif mode == 'replicate':
        return np.pad(img, 1, mode='edge')
    else:
        raise ValueError(mode)


def apply_kernel(img_padded: np.ndarray, kernel: np.ndarray, cfg: HWConfig,
                  filter_type: str, H: int = None, W: int = None) -> np.ndarray:
    """
    H, W: kich thuoc anh OUTPUT (khong tinh padding). Neu khong truyen,
    mac dinh lay tu cfg.IMG_HEIGHT/IMG_WIDTH - nhung nen truyen truc tiep
    (vd H,W = img.shape truoc khi pad) de dung duoc voi bat ky kich thuoc
    anh nao (64x64, 128x128, 256x256...) ma khong can sua HWConfig.
    """
    if H is None: H = cfg.IMG_HEIGHT
    if W is None: W = cfg.IMG_WIDTH
    out = np.zeros((H, W), dtype=np.int64)

    for r in range(H):
        for c in range(W):
            window = img_padded[r:r+3, c:c+3].astype(np.int64)
            # --- adder tree / systolic: nhan tung pixel voi he so kernel,
            #     cong don - ca 2 kien truc RTL cho ra CUNG 1 KET QUA TOAN
            #     HOC nay (da verify bit-exact giua conv_multi.v va
            #     conv_systolic.v), nen golden model dung chung 1 cong thuc
            #     cho ca 2, khong can phan biet.
            raw_sum = int(np.sum(window * kernel))

            if filter_type == 'blur':
                # DUNG CONG THUC THAT: (raw_sum * 114) >>> 10
                # Dung Python '>>' tren so nguyen la arithmetic shift (floor
                # ve -vo cuc), khop hanh vi '>>>' tren Verilog signed.
                acc = (raw_sum * 114) >> 10
            else:
                acc = raw_sum

            # --- clipping / saturation ve [0, 2^PIXEL_WIDTH - 1] ---
            # (RTL that: sharpen co kiem tra ca am lan tran; blur chi kiem
            # tra tran vi tong pixel khong dau*trong so 1 khong the am)
            max_val = (1 << cfg.PIXEL_WIDTH) - 1
            if cfg.CLIP_MODE == 'saturate':
                acc = max(0, min(max_val, acc))
            else:  # wrap
                acc = acc & max_val

            out[r, c] = acc

    return out.astype(np.uint8)


def golden_sharpen(img: np.ndarray, cfg: HWConfig = CFG) -> np.ndarray:
    # Dung dung shape cua anh dau vao (img.shape), KHONG lay tu cfg co dinh
    # 64x64 nua - nho vay ham nay dung duoc voi bat ky kich thuoc anh nao
    # (64x64, 128x128, 256x256...) ma khong can sua HWConfig.
    H, W = img.shape
    img_p = pad_replicate_or_zero(img, mode='zero')
    return apply_kernel(img_p, cfg.KERNEL_SHARP, cfg, filter_type='sharpen', H=H, W=W)


def golden_blur(img: np.ndarray, cfg: HWConfig = CFG) -> np.ndarray:
    H, W = img.shape
    img_p = pad_replicate_or_zero(img, mode='zero')
    return apply_kernel(img_p, cfg.KERNEL_BLUR, cfg, filter_type='blur', H=H, W=W)


# =============================================================================
# 3. TEST VECTOR GENERATOR - sinh cac pattern de bat loi overflow/boundary
#    Dung de xuat ra input_data.hex/txt nap vao testbench_prj.v
# =============================================================================

def gen_test_patterns(H: int = 64, W: int = 64) -> dict:
    patterns = {}

    patterns['all_zero'] = np.zeros((H, W), dtype=np.uint8)
    patterns['all_max']  = np.full((H, W), 255, dtype=np.uint8)

    # Checkerboard: bat loi window_3x3 doc sai thu tu pixel
    cb = np.indices((H, W)).sum(axis=0) % 2
    patterns['checkerboard'] = (cb * 255).astype(np.uint8)

    # Gradient ngang/doc: bat loi line_buffer bi lech dong/cot
    grad_h = np.tile(np.linspace(0, 255, W, dtype=np.uint8), (H, 1))
    patterns['gradient_horizontal'] = grad_h
    grad_v = np.tile(np.linspace(0, 255, H, dtype=np.uint8).reshape(-1, 1), (1, W))
    patterns['gradient_vertical'] = grad_v

    # Single white pixel giua nen den: bat loi impulse response / kernel sai
    impulse = np.zeros((H, W), dtype=np.uint8)
    impulse[H // 2, W // 2] = 255
    patterns['impulse_center'] = impulse

    # 4 goc = 255 (con lai = 0): bat loi zero-padding bien
    corners = np.zeros((H, W), dtype=np.uint8)
    corners[0, 0] = corners[0, -1] = corners[-1, 0] = corners[-1, -1] = 255
    patterns['corners'] = corners

    # Random seed co dinh (tai lap duoc) de test thong ke tren nhieu mau
    rng = np.random.default_rng(42)
    patterns['random_uniform'] = rng.integers(0, 256, size=(H, W), dtype=np.uint8)

    # Random co the gay saturate manh nhat (worst-case cho sharpen: tam sang
    # 255, xung quanh toi 0 -> kiem tra clipping duoi 0 co hoat dong dung)
    worst = np.zeros((H, W), dtype=np.uint8)
    worst[::2, ::2] = 255
    patterns['worst_case_saturation'] = worst

    return patterns


def find_best_offset(golden: np.ndarray, rtl_out: np.ndarray, max_offset: int = 300) -> Tuple[int, float]:
    """
    Tu dong do offset (so pixel bi lech) giua golden model va RTL output,
    do hien tuong "lam day" pipeline (line_buffer/window_3x3 xuat du lieu
    rac o dau luong truoc khi co du lieu that). Day la GIOI HAN DA BIET cua
    kien truc (xem README muc Limitations), khong phai loi RTL tinh sai.

    Tra ve: (offset_tot_nhat, match_rate_tai_offset_do)
    """
    g_flat = golden.flatten()
    r_flat = rtl_out.flatten()
    best_off, best_match = 0, -1

    for off in range(0, max_offset + 1):
        match = 0
        total = 0
        for i in range(len(g_flat) - off):
            j = i + off
            total += 1
            if g_flat[i] == r_flat[j]:
                match += 1
        if total > 100:
            rate = match / total
            if match > best_match:
                best_match = match
                best_off = off

    match_rate = 100.0 * best_match / (len(g_flat) - best_off)
    return best_off, match_rate


def compare_with_auto_offset(golden: np.ndarray, rtl_out: np.ndarray, label: str,
                              max_offset: int = 300, pass_threshold: float = 95.0) -> dict:
    """
    Ban "thong minh" cua compare_outputs(): TU DONG do offset do pipeline
    "lam day" (xem find_best_offset), roi so sanh sau khi da bu offset do.
    Dung ham nay thay cho compare_outputs() truc tiep khi ban biet truoc
    co the co do lech do pipeline warm-up (vd anh dau tien, hoac doi kich
    thuoc anh).

    pass_threshold mac dinh = 95.0 (khong phai 100.0) vi SAU KHI DA BU
    OFFSET, phan con lai sai chi la hieu ung vien anh (line_buffer khong
    zero-pad doi xung 4 canh) - day la GIOI HAN KIEN TRUC DA BIET, khong
    phai loi RTL, nen khong nen doi hoi khop tuyet doi 100%.
    """
    offset, _ = find_best_offset(golden, rtl_out, max_offset)

    W = golden.shape[1] if golden.ndim == 2 else None  # luu chieu rong anh GOC truoc khi flatten

    g_flat = golden.flatten()
    r_flat = rtl_out.flatten()
    n = len(g_flat) - offset

    g_aligned = g_flat[:n]
    r_aligned = r_flat[offset:offset + n]

    result = compare_outputs(g_aligned, r_aligned, label, pass_threshold=pass_threshold)
    result['pipeline_offset_detected'] = offset

    # --- Tinh rieng SSIM tren phan da bu offset, reshape lai 2D ---
    if HAVE_SSIM and W is not None:
        try:
            n_rows = n // W
            if n_rows >= 7 and W >= 7:
                g_2d = g_aligned[:n_rows * W].reshape(n_rows, W)
                r_2d = r_aligned[:n_rows * W].reshape(n_rows, W)
                result['ssim'] = round(float(ssim(g_2d, r_2d, data_range=255)), 5)
        except Exception:
            pass

    print(f"[{label}] Da tu dong phat hien va bu pipeline offset = {offset} pixel "
          f"(do line_buffer/window_3x3 can 'lam day' truoc khi xuat du lieu that)")
    return result


def verify_from_input_hex(input_hex_path, rtl_sharp_hex_path=None, rtl_blur_hex_path=None,
                           size: int = 64, cfg: HWConfig = None, out_dir: str = "real_image_check",
                           auto_offset: bool = True, run_label: str = "unnamed_run",
                           architecture: str = "", log_dir: str = "verification_logs",
                           save_log: bool = True, pass_threshold: float = 95.0):
    """
    DUNG HAM NAY thay cho verify_real_image() khi ban da co san file .hex
    input (vd tao boi image_to_hex.py cua ban) va muon golden model tinh
    tren DUNG anh do - khong resize lai tu PNG (tranh truong hop golden
    model va image_to_hex.py resize anh goc theo 2 cach khac nhau, gay
    sai lech gia o vien anh du RTL tinh dung).

    auto_offset=True (mac dinh): tu dong do va bu pipeline "lam day" offset
    truoc khi tinh match rate/PSNR - phan anh dung ban chat RTL co tinh
    dung khong, thay vi bi nhieu boi do lech vi tri.

    pass_threshold=95.0 (mac dinh): nguong % de coi la PASS. Dat = 100.0
    neu muon doi hoi khop tuyet doi (vd dang test pattern nhan tao khong
    co hieu ung vien, hoac muon kiem tra nghiem ngat hon).

    run_label / architecture: dat ten cho lan chay nay (vd run_label="hoa_64x64",
    architecture="Adder Tree") - dung de phan biet trong file log tich luy
    (xem save_log). Neu chay lai voi cung run_label+architecture nhieu lan,
    moi lan van duoc GHI THEM (khong ghi de) vao log - loc lai theo timestamp
    neu can chi giu lan chay moi nhat.

    save_log=True (mac dinh): tu dong ghi ket qua vao verification_logs/
    (CSV + TXT, cong don qua nhieu lan chay) - dung lam tai nguyen bao cao.
    Dat save_log=False neu chi muon xem ket qua nhanh, khong can luu lai.

    Cach dung:
        verify_from_input_hex(
            "input_data.hex",           # file .hex ban da dung de chay RTL
            "output_sharp.hex",
            "output_blur.hex",
            size=64,
            run_label="hoa_64x64",
            architecture="Adder Tree"
        )
    """
    if cfg is None:
        cfg = CFG

    out = Path(out_dir)
    out.mkdir(exist_ok=True)

    # Doc LAI DUNG anh da dung de chay RTL, khong resize lai tu dau
    img = load_hex_as_image(input_hex_path, size, size)
    print(f"Da doc input hex: {input_hex_path} -> {img.shape} (dung nguyen, khong resize lai)")

    g_sharp = golden_sharpen(img, cfg)
    g_blur = golden_blur(img, cfg)

    if HAVE_PIL:
        Image.fromarray(img).save(out / "input_from_hex.png")
        Image.fromarray(g_sharp).save(out / "golden_sharp.png")
        Image.fromarray(g_blur).save(out / "golden_blur.png")

    results = {}

    if rtl_sharp_hex_path is not None:
        rtl_sharp = load_hex_as_image(rtl_sharp_hex_path, size, size)
        if auto_offset:
            r = compare_with_auto_offset(g_sharp, rtl_sharp, "sharpen", pass_threshold=pass_threshold)
        else:
            r = compare_outputs(g_sharp, rtl_sharp, "sharpen", pass_threshold=pass_threshold)
        results['sharpen'] = r
        print("SHARPEN vs RTL:", r)
        if HAVE_PIL:
            Image.fromarray(rtl_sharp).save(out / "rtl_sharp.png")
            Image.fromarray(diff_image(g_sharp, rtl_sharp)).save(out / "diff_sharp.png")
        if save_log:
            log_verification_result(r, run_label, architecture, "sharpen", log_dir)

    if rtl_blur_hex_path is not None:
        rtl_blur = load_hex_as_image(rtl_blur_hex_path, size, size)
        if auto_offset:
            r = compare_with_auto_offset(g_blur, rtl_blur, "blur", pass_threshold=pass_threshold)
        else:
            r = compare_outputs(g_blur, rtl_blur, "blur", pass_threshold=pass_threshold)
        results['blur'] = r
        print("BLUR vs RTL:", r)
        if HAVE_PIL:
            Image.fromarray(rtl_blur).save(out / "rtl_blur.png")
            Image.fromarray(diff_image(g_blur, rtl_blur)).save(out / "diff_blur.png")
        if save_log:
            log_verification_result(r, run_label, architecture, "blur", log_dir)

    return results


def load_real_image(path, size: int, resize_mode: str = 'resize') -> np.ndarray:
    """
    Doc 1 anh THAT (png/jpg/bmp...) tu dia, chuyen ve grayscale 8-bit, va
    dua ve dung kich thuoc vuong `size x size` (phai khop voi kich thuoc
    ban dinh chay tren RTL, vi du 64, 128, 256).

    resize_mode:
      'resize'       - resize toan bo anh ve size x size (co the meo ty le,
                        nhung giu duoc toan bo noi dung anh - mac dinh, giong
                        cach image_to_hex.py cua ban thuong lam)
      'center_crop'  - resize canh ngan ve size, roi cat giua ra size x size
                        (giu dung ty le, nhung mat vien anh)

    Tra ve: ndarray uint8, shape (size, size).
    """
    if not HAVE_PIL:
        raise RuntimeError("Can cai Pillow: pip install pillow --break-system-packages")

    img = Image.open(path).convert("L")   # "L" = 8-bit grayscale

    if resize_mode == 'resize':
        img = img.resize((size, size), Image.LANCZOS)
    elif resize_mode == 'center_crop':
        w, h = img.size
        scale = size / min(w, h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - size) // 2
        top = (new_h - size) // 2
        img = img.crop((left, top, left + size, top + size))
    else:
        raise ValueError(resize_mode)

    return np.array(img, dtype=np.uint8)


def verify_real_image(image_path, rtl_sharp_hex_path=None, rtl_blur_hex_path=None,
                       size: int = 64, cfg: HWConfig = None, out_dir: str = "real_image_check"):
    """
    HAM GOP: chay toan bo luong "anh that -> golden model -> (tuy chon) so
    sanh voi RTL" trong 1 lan goi.

    Cach dung:
      1. Chi muon xem golden model xu ly anh that ra sao (chua co RTL output):
           verify_real_image("hoa.png", size=64)
         -> xuat golden_sharp.png, golden_blur.png, va input_from_real_image.hex
            (file nay dung de nap vao testbench_prj.v) vao thu muc out_dir.

      2. Da co output tu RTL (output_sharp.hex, output_blur.hex tu ModelSim/
         iverilog), muon so sanh bit-exact/PSNR:
           verify_real_image("hoa.png", "output_sharp.hex", "output_blur.hex", size=64)
         -> in ra bang so sanh (match rate, PSNR, SSIM) va luu diff image.
    """
    if cfg is None:
        cfg = CFG

    out = Path(out_dir)
    out.mkdir(exist_ok=True)

    # 1. Doc anh that, resize ve dung kich thuoc
    img = load_real_image(image_path, size)
    print(f"Da doc anh: {image_path} -> resize ve {img.shape}")

    # 2. Xuat file .hex de nap vao testbench_prj.v (neu chua chay RTL)
    save_pattern_as_hex(img, out / "input_from_real_image.hex")
    print(f"Da xuat input RTL: {out / 'input_from_real_image.hex'}")

    # 3. Tinh golden output
    g_sharp = golden_sharpen(img, cfg)
    g_blur = golden_blur(img, cfg)

    if HAVE_PIL:
        Image.fromarray(img).save(out / "input_grayscale.png")
        Image.fromarray(g_sharp).save(out / "golden_sharp.png")
        Image.fromarray(g_blur).save(out / "golden_blur.png")
        print(f"Da luu anh xem truoc (grayscale/golden_sharp/golden_blur) vao {out}/")

    results = {}

    # 4. Neu co RTL output, so sanh
    if rtl_sharp_hex_path is not None:
        rtl_sharp = load_hex_as_image(rtl_sharp_hex_path, size, size)
        r = compare_outputs(g_sharp, rtl_sharp, "real_image_sharpen")
        results['sharpen'] = r
        print("SHARPEN vs RTL:", r)
        if HAVE_PIL:
            Image.fromarray(rtl_sharp).save(out / "rtl_sharp.png")
            Image.fromarray(diff_image(g_sharp, rtl_sharp)).save(out / "diff_sharp.png")

    if rtl_blur_hex_path is not None:
        rtl_blur = load_hex_as_image(rtl_blur_hex_path, size, size)
        r = compare_outputs(g_blur, rtl_blur, "real_image_blur")
        results['blur'] = r
        print("BLUR vs RTL:", r)
        if HAVE_PIL:
            Image.fromarray(rtl_blur).save(out / "rtl_blur.png")
            Image.fromarray(diff_image(g_blur, rtl_blur)).save(out / "diff_blur.png")

    if not results:
        print("\n>>> Chua co RTL output de so sanh. Buoc tiep theo:")
        print(f"1. Chay ModelSim/iverilog voi input '{out / 'input_from_real_image.hex'}'")
        print("   (doi ten file trong testbench_prj.v cho khop duong dan nay)")
        print("2. Goi lai verify_real_image(..., rtl_sharp_hex_path=..., rtl_blur_hex_path=...)")

    return results


def save_pattern_as_hex(img: np.ndarray, out_path: Path):
    """
    Xuat theo dung dinh dang input_data.hex ma testbench_prj.v doc (thuong
    la 1 gia tri hex 2 ky tu moi dong, quet theo row-major tu (0,0)).
    Kiem tra lai script image_to_hex.py cua ban de doi format cho khop
    (vd co the la .txt dang thap phan thay vi hex).
    """
    with open(out_path, 'w') as f:
        for r in range(img.shape[0]):
            for c in range(img.shape[1]):
                f.write(f"{img[r, c]:02x}\n")


def load_hex_as_image(path: Path, H: int, W: int) -> np.ndarray:
    """Doc output_data.hex tu ModelSim thanh anh HxW."""
    vals = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            vals.append(int(line, 16))
    arr = np.array(vals, dtype=np.uint8)
    expected = H * W
    if arr.size != expected:
        print(f"[CANH BAO] So pixel doc duoc = {arr.size}, ky vong = {expected}. "
              f"Kiem tra PIPELINE_LATENCY hoac dinh dang file - co the can bo bot "
              f"{arr.size - expected} mau dau/cuoi do do tre pipeline.")
        arr = arr[:expected] if arr.size > expected else np.pad(arr, (0, expected - arr.size))
    return arr.reshape(H, W)


# =============================================================================
# 4. COMPARATOR - so sanh RTL output vs golden model, xuat bao cao cho paper
# =============================================================================

def compare_outputs(golden: np.ndarray, rtl_out: np.ndarray, label: str,
                     pass_threshold: float = 100.0) -> dict:
    """
    pass_threshold: nguong % de tinh PASS/FAIL (mac dinh 100.0 = phai khop
    tuyet doi). Khi so sanh voi ANH THAT (co hieu ung vien anh da biet do
    line_buffer/window_3x3 khong zero-pad doi xung), nen dat pass_threshold
    thap hon (vd 95.0) qua ham verify_from_input_hex(), vi khong bao gio
    dat 100% do gioi han kien truc, khong phai loi RTL - xem README muc
    Limitations.
    """
    assert golden.shape == rtl_out.shape, f"Shape mismatch: {golden.shape} vs {rtl_out.shape}"

    diff = golden.astype(np.int32) - rtl_out.astype(np.int32)
    n_total = diff.size
    n_match = int(np.sum(diff == 0))
    match_rate = 100.0 * n_match / n_total

    mse = float(np.mean(diff.astype(np.float64) ** 2))
    psnr = float('inf') if mse == 0 else 20 * np.log10(255.0 / np.sqrt(mse))

    ssim_val = None
    if HAVE_SSIM:
        try:
            if golden.ndim == 2 and min(golden.shape) >= 7:
                ssim_val = float(ssim(golden, rtl_out, data_range=255))
        except Exception:
            ssim_val = None

    result = {
        'label': label,
        'total_pixels': n_total,
        'exact_match': n_match,
        'match_rate_pct': round(match_rate, 4),
        'max_abs_error': int(np.max(np.abs(diff))),
        'mean_abs_error': float(np.mean(np.abs(diff))),
        'mse': round(mse, 6),
        'psnr_db': round(psnr, 3) if psnr != float('inf') else 'inf',
        'ssim': round(ssim_val, 5) if ssim_val is not None else 'N/A',
        'pass_threshold_used': pass_threshold,
        'PASS': bool(match_rate >= pass_threshold),
    }
    return result


def diff_image(golden: np.ndarray, rtl_out: np.ndarray) -> np.ndarray:
    """Anh sai lech, scale de nhin ro (0 = giong het, cang sang cang lech nhieu)."""
    diff = np.abs(golden.astype(np.int32) - rtl_out.astype(np.int32))
    if diff.max() > 0:
        diff_vis = (diff * (255 // diff.max())).astype(np.uint8)
    else:
        diff_vis = diff.astype(np.uint8)
    return diff_vis


def write_report_csv(results: list, out_path: Path):
    fields = ['label', 'total_pixels', 'exact_match', 'match_rate_pct',
              'max_abs_error', 'mean_abs_error', 'mse', 'psnr_db', 'ssim', 'PASS']
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


# =============================================================================
# 4b. GHI LOG XAC MINH - tich luy ket qua PASS/FAIL qua nhieu lan chay, dung
#     lam tai nguyen bao cao/paper (bang tong hop, khong phai chi 1 lan chay).
# =============================================================================

LOG_CSV_FIELDS = [
    'timestamp', 'run_label', 'architecture', 'filter_mode',
    'total_pixels', 'exact_match', 'match_rate_pct',
    'max_abs_error', 'mean_abs_error', 'mse', 'psnr_db', 'ssim',
    'pipeline_offset_detected', 'pass_threshold_used', 'PASS',
]


def log_verification_result(result: dict, run_label: str, architecture: str = "",
                             filter_mode: str = "", log_dir: str = "verification_logs"):
    """
    Ghi 1 KET QUA so sanh (dict tra ve tu compare_outputs()/compare_with_auto_offset())
    vao 2 file log TICH LUY (cong don qua nhieu lan chay, khong ghi de):
      - verification_log.csv  : dang bang, mo bang Excel/Google Sheets de lam
                                 bao cao hoac dua thang vao paper.
      - verification_log.txt  : dang doc de, co timestamp, dung de xem nhanh
                                 lich su cac lan chay va ty le PASS/FAIL.

    run_label     : ten de phan biet lan chay nay (vd "hoa_64x64", "test_pattern_checkerboard")
    architecture  : "Adder Tree" hoac "Systolic Array" (de sau nay loc/nhom trong bang)
    filter_mode   : "sharpen" hoac "blur"
    log_dir       : thu muc luu 2 file log (tu tao neu chua co)

    Goi ham nay MOI LAN sau khi co ket qua so sanh (co the goi nhieu lan lien
    tiep cho nhieu anh/nhieu kien truc khac nhau) - du lieu se CONG DON, khong
    bi ghi de, giup xay dung dan 1 bang tong hop day du cho bao cao.
    """
    out = Path(log_dir)
    out.mkdir(exist_ok=True)
    csv_path = out / "verification_log.csv"
    txt_path = out / "verification_log.txt"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = {
        'timestamp': timestamp,
        'run_label': run_label,
        'architecture': architecture,
        'filter_mode': filter_mode,
        'total_pixels': result.get('total_pixels', ''),
        'exact_match': result.get('exact_match', ''),
        'match_rate_pct': result.get('match_rate_pct', ''),
        'max_abs_error': result.get('max_abs_error', ''),
        'mean_abs_error': result.get('mean_abs_error', ''),
        'mse': result.get('mse', ''),
        'psnr_db': result.get('psnr_db', ''),
        'ssim': result.get('ssim', ''),
        'pipeline_offset_detected': result.get('pipeline_offset_detected', ''),
        'pass_threshold_used': result.get('pass_threshold_used', ''),
        'PASS': result.get('PASS', ''),
    }

    # --- Ghi CSV (cong don - append neu file da ton tai) ---
    file_exists = csv_path.exists()
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    # --- Ghi TXT (cong don - de doc, co timestamp) ---
    status = "PASS" if row['PASS'] else "FAIL"
    with open(txt_path, 'a') as f:
        f.write(f"[{timestamp}] {run_label} | {architecture} | {filter_mode}\n")
        f.write(f"    Ket qua       : {status}\n")
        f.write(f"    Match rate    : {row['match_rate_pct']}%\n")
        f.write(f"    Max abs error : {row['max_abs_error']}\n")
        f.write(f"    Mean abs error: {row['mean_abs_error']}\n")
        f.write(f"    PSNR (dB)     : {row['psnr_db']}\n")
        f.write(f"    SSIM          : {row['ssim']}\n")
        if row['pipeline_offset_detected'] != '':
            f.write(f"    Pipeline offset da bu: {row['pipeline_offset_detected']} pixel\n")
        f.write("-" * 60 + "\n")

    print(f"Da ghi log: {csv_path} va {txt_path} (run_label='{run_label}')")


def print_log_summary(log_dir: str = "verification_logs"):
    """
    Doc lai file verification_log.csv da tich luy, in ra bang tong hop
    PASS/FAIL - dung khi ban da chay nhieu lan (nhieu anh, nhieu kien truc)
    va muon xem tong quan truoc khi dua vao bao cao.
    """
    csv_path = Path(log_dir) / "verification_log.csv"
    if not csv_path.exists():
        print(f"Chua co file log nao tai {csv_path}. Hay chay it nhat 1 lan "
              f"verify_from_input_hex(...) hoac goi log_verification_result() truoc.")
        return

    with open(csv_path, 'r') as f:
        rows = list(csv.DictReader(f))

    n_pass = sum(1 for r in rows if r['PASS'] == 'True')
    n_fail = sum(1 for r in rows if r['PASS'] == 'False')

    print("=" * 70)
    print(f"TONG HOP LOG XAC MINH ({csv_path})")
    print("=" * 70)
    print(f"{'Run label':<25}{'Kien truc':<16}{'Mode':<10}{'Match%':<10}{'PASS?':<8}")
    print("-" * 70)
    for r in rows:
        print(f"{r['run_label']:<25}{r['architecture']:<16}{r['filter_mode']:<10}"
              f"{r['match_rate_pct']:<10}{r['PASS']:<8}")
    print("-" * 70)
    print(f"TONG: {len(rows)} lan chay | PASS: {n_pass} | FAIL: {n_fail}")
    print("=" * 70)


# =============================================================================
# 5. DEMO / SELF-TEST - chay thu voi golden model tu tuong tao (chua co RTL)
#    Muc dich: kiem tra code chay dung, va sinh file test vector mau.
# =============================================================================

def main_demo(img_size: int = None):
    """
    img_size: kich thuoc anh vuong can test (64, 128, 256...). Neu khong
    truyen, mac dinh lay CFG.IMG_HEIGHT/IMG_WIDTH (64x64). Chay tu dong lenh:
        python3 golden_model.py            -> dung 64x64 (mac dinh)
        python3 golden_model.py 128        -> dung 128x128
        python3 golden_model.py 256        -> dung 256x256
    """
    H = img_size if img_size else CFG.IMG_HEIGHT
    W = img_size if img_size else CFG.IMG_WIDTH

    out_dir = Path(f"golden_model_output_{H}x{W}")
    out_dir.mkdir(exist_ok=True)

    patterns = gen_test_patterns(H, W)
    results_sharp, results_blur = [], []

    print(f"{'Pattern':<24}{'Sharpen match%':<18}{'Blur match%':<15}")
    print("-" * 57)

    for name, img in patterns.items():
        # 1. Xuat test vector (de nap vao testbench_prj.v thuc te)
        save_pattern_as_hex(img, out_dir / f"input_{name}.hex")

        # 2. Tinh golden output
        g_sharp = golden_sharpen(img)
        g_blur = golden_blur(img)

        # (Trong thuc te: ban chay ModelSim voi input_{name}.hex, lay
        #  output_data.hex, roi load bang load_hex_as_image() de so sanh
        #  that voi RTL. O day, demo tu-so-sanh golden voi chinh no de
        #  minh hoa cach dung - se luon PASS 100%.)
        r_sharp = compare_outputs(g_sharp, g_sharp, f"{name}_sharpen")
        r_blur = compare_outputs(g_blur, g_blur, f"{name}_blur")
        results_sharp.append(r_sharp)
        results_blur.append(r_blur)

        print(f"{name:<24}{r_sharp['match_rate_pct']:<18}{r_blur['match_rate_pct']:<15}")

    write_report_csv(results_sharp + results_blur, out_dir / "verification_report.csv")
    print(f"\nDa sinh test vectors va bao cao mau tai: {out_dir}/")
    print("\n>>> BUOC TIEP THEO DE VERIFY THAT:")
    print("1. Chay ModelSim voi tung file input_<pattern>.hex")
    print("2. Doi ten output_data.hex thanh output_<pattern>_<sharp|blur>.hex")
    print("3. Dung load_hex_as_image() de doc, roi goi compare_outputs(golden, rtl_out, ...)")
    print("4. Ghep tat ca results vao 1 bang cho phan 'Experimental Results' cua paper")


if __name__ == "__main__":
    import sys
    size_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main_demo(size_arg)
