"""
知乎 x-zse-96 签名生成器 (Python port of JS reverse)

参考:
  - https://github.com/LumingMelody/JS_reverse
  - https://github.com/zhihulite/zhihu_zse96 (Android LAES, not used here)

算法: 自定义 32 轮分组密码 + CBC 模式 + 自定义 base64 编码
"""

import hashlib
import math
import random

# ---- 常量 (从 JS 直接移植) ----

ZK = [
    1170614578, 1024848638, 1413669199, -343334464, -766094290,
    -1373058082, -143119608, -297228157, 1933479194, -971186181,
    -406453910, 460404854, -547427574, -1891326262, -1679095901,
    2119585428, -2029270069, 2035090028, -1521520070, -5587175,
    -77751101, -2094365853, -1243052806, 1579901135, 1321810770,
    456816404, -1391643889, -229302305, 330002838, -788960546,
    363569021, -1947871109,
]

ZB = [
    20, 223, 245, 7, 248, 2, 194, 209, 87, 6, 227, 253, 240, 128,
    222, 91, 237, 9, 125, 157, 230, 93, 252, 205, 90, 79, 144, 199,
    159, 197, 186, 167, 39, 37, 156, 198, 38, 42, 43, 168, 217, 153,
    15, 103, 80, 189, 71, 191, 97, 84, 247, 95, 36, 69, 14, 35, 12,
    171, 28, 114, 178, 148, 86, 182, 32, 83, 158, 109, 22, 255, 94,
    238, 151, 85, 77, 124, 254, 18, 4, 26, 123, 176, 232, 193, 131,
    172, 143, 142, 150, 30, 10, 146, 162, 62, 224, 218, 196, 229, 1,
    192, 213, 27, 110, 56, 231, 180, 138, 107, 242, 187, 54, 120, 19,
    44, 117, 228, 215, 203, 53, 239, 251, 127, 81, 11, 133, 96, 204,
    132, 41, 115, 73, 55, 249, 147, 102, 48, 122, 145, 106, 118, 74,
    190, 29, 16, 174, 5, 177, 129, 63, 113, 99, 31, 161, 76, 246, 34,
    211, 13, 60, 68, 207, 160, 65, 111, 82, 165, 67, 169, 225, 57,
    112, 244, 155, 51, 236, 200, 233, 58, 61, 47, 100, 137, 185, 64,
    17, 70, 234, 163, 219, 108, 170, 166, 59, 149, 52, 105, 24, 212,
    78, 173, 45, 0, 116, 226, 119, 136, 206, 135, 175, 195, 25, 92,
    121, 208, 126, 139, 3, 75, 141, 21, 130, 98, 241, 40, 154, 66,
    184, 49, 181, 46, 243, 88, 101, 183, 8, 23, 72, 188, 104, 179,
    210, 134, 250, 201, 164, 89, 216, 202, 220, 50, 221, 152, 140, 33,
    235, 214,
]

# 固定 XOR 密钥
FIX_ARR = [48, 53, 57, 48, 53, 51, 102, 55, 100, 49, 53, 101, 48, 49, 100, 55]

# 自定义 base64 salt
SALT = '6fpLRqJO8M/c3jnYxFkUVC4ZIG12SiH=5v0mXDazWBTsuw7QetbKdoPyAl+hN9rgE'


def _to_uint32(x):
    """转换为无符号 32 位整数"""
    return x & 0xFFFFFFFF


def _i(e, t, n):
    """大端写入 4 字节"""
    t[n] = (e >> 24) & 0xFF
    t[n + 1] = (e >> 16) & 0xFF
    t[n + 2] = (e >> 8) & 0xFF
    t[n + 3] = e & 0xFF


def _b(e, t):
    """大端读取 4 字节"""
    return ((e[t] << 24) | (e[t + 1] << 16) | (e[t + 2] << 8) | e[t + 3]) & 0xFFFFFFFF


def _q(e, t):
    """循环左移"""
    return _to_uint32((e << t) | (e >> (32 - t)))


def _g(e):
    """G 函数: S-box 查表 + 循环移位异或"""
    t = [0] * 4
    n = [0] * 4
    _i(e, t, 0)
    n[0] = ZB[t[0] & 0xFF]
    n[1] = ZB[t[1] & 0xFF]
    n[2] = ZB[t[2] & 0xFF]
    n[3] = ZB[t[3] & 0xFF]
    r = _b(n, 0)
    return r ^ _q(r, 2) ^ _q(r, 10) ^ _q(r, 18) ^ _q(r, 24)


def __g_r(e):
    """
    32 轮分组加密, 输入 16 字节, 输出 16 字节
    对应 JS 的 __g.r
    """
    t = [0] * 16
    n = [0] * 36
    n[0] = _b(e, 0)
    n[1] = _b(e, 4)
    n[2] = _b(e, 8)
    n[3] = _b(e, 12)
    for r in range(32):
        o = _g(n[r + 1] ^ n[r + 2] ^ n[r + 3] ^ ZK[r])
        n[r + 4] = _to_uint32(n[r] ^ o)
    _i(n[35], t, 0)
    _i(n[34], t, 4)
    _i(n[33], t, 8)
    _i(n[32], t, 12)
    return t


def __g_x(e, iv):
    """
    CBC 模式加密, 输入 e (字节列表, 长度为 16 的倍数), iv (16 字节)
    对应 JS 的 __g.x
    """
    result = []
    t = iv[:]
    for i in range(len(e) // 16):
        block = e[16 * i:16 * (i + 1)]
        # XOR with t (IV or previous ciphertext)
        xored = [block[j] ^ t[j] for j in range(16)]
        t = __g_r(xored)
        result.extend(t)
    return result


def pre_process(md5_hex):
    """
    preProcess: MD5 hex -> charCode array -> padding -> XOR -> encrypt
    输出 48 字节
    """
    # MD5 hex string to char codes
    md5_codes = [ord(c) for c in md5_hex]

    # Prepend [0, random(0-127)]
    md5_codes.insert(0, 0)
    md5_codes.insert(0, random.randint(0, 127))

    # Append 15 bytes of 14
    md5_codes.extend([14] * 15)

    # 现在一定是 48 字节 (2 + 32 + 15 = 49, wait let me recount)
    # md5_hex is 32 chars, +2 prepended = 34, +15 appended = 49? No...
    # Let me re-check the JS:
    # md5Str = 32 chars -> md5CharCodeAtArr = 32 elements
    # unshift(0) -> 33
    # unshift(random*127) -> 34
    # push(14) x15 -> 49
    # Then slice(0, 16) for front, slice(16, 48) for back (32 elements)
    # Wait, slice(16, 48) of a 49-element array gives indices 16..47 = 32 elements
    # So front = 16, back = 32 (indices 16-47), total processed = 16 + 32 = 48
    # But we have 49 elements... let me re-read the JS more carefully.
    #
    # Oh wait, slice(16, 48): JavaScript slice end is exclusive.
    # If array has 49 elements (index 0-48), slice(16, 48) gives indices 16-47 = 32 elements.
    # And slice(0, 16) gives indices 0-15 = 16 elements.
    # 16 + 32 = 48. Element at index 48 (the last 14) is dropped!
    # So the last padding byte is thrown away. Total = 48.
    #
    # Actually wait - md5_hex is 32 chars, so char codes = 32 elements
    # After 2 unshifts: 34
    # After 15 pushes: 49
    # slice(0,16) = first 16 (indices 0-15)
    # slice(16,48) = indices 16-47 (32 elements)
    # Element 48 is dropped.
    # That's 16+32 = 48 total.
    #
    # Let me verify: 32 + 2 = 34, + 15 = 49. slice(16,48) from 49 elements = 48-16 = 32. Yes.

    front_arr = md5_codes[:16]
    back_arr = md5_codes[16:48]  # drop last element

    # XOR front with FIX_ARR ^ 42
    new_front = [front_arr[i] ^ FIX_ARR[i] ^ 42 for i in range(16)]

    # Encrypt front
    enc_front = __g_r(new_front)

    # CBC encrypt back
    enc_back = __g_x(back_arr, enc_front)

    return enc_front + enc_back


def _encode_24bit(val):
    """
    自定义 base64: 将 24 位值编码为 4 字符
    """
    result = ''
    for x in [0, 6, 12, 18]:
        a = val >> x
        b = a & 63
        result += SALT[b]
    return result


def encrypt(md5_hex):
    """
    主加密流程
    输入: MD5 hex string (32 字符)
    输出: base64-like 编码字符串
    """
    processed = pre_process(md5_hex)

    current = 0
    result_str = ''
    for i in range(len(processed)):
        pop = processed[len(processed) - i - 1]
        i_mod_4 = i % 4
        i_mod_3 = i % 3

        a = 8 * i_mod_4
        b = 58 >> a  # 58 = 0b00111010
        c = b & 255
        d = pop ^ c
        e = d << (8 * i_mod_3)

        current |= e

        if i_mod_3 == 2:
            result_str += _encode_24bit(current)
            current = 0

    return result_str


def get_xzse96(d_c0, api_path):
    """
    生成 x-zse-96 签名
    
    参数:
        d_c0: d_c0 cookie 值 (完整值, 含 |= 部分)
        api_path: API 路径, e.g. '/api/v4/search_v3?...' 或 '/api/articles/drafts'
    
    返回:
        x-zse-96 header 值, e.g. '2.0_xxxxxxxxxx'
    """
    f = f'101_3_3.0+{api_path}+{d_c0}'
    md5_hex = hashlib.md5(f.encode()).hexdigest()
    encrypted = encrypt(md5_hex)
    return f'2.0_{encrypted}'


if __name__ == '__main__':
    # 测试
    test_d_c0 = "AFATiXgZ_BWPTtgq6Lp8yI2EWG9iT6W6BgI=|1670475363"
    test_path = "/api/v4/search_v3?gk_version=gz-gaokao&t=zvideo&q=%E9%80%86%E5%90%91&correction=1&offset=0&limit=20&filter_fields=&lc_idx=0&show_all_topics=0&search_source=Normal"
    
    sig = get_xzse96(test_d_c0, test_path)
    print(f"x-zse-96: {sig}")
    print(f"Length: {len(sig)}")
