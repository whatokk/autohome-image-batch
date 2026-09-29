#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终合成: 原图 + 车窗内的户外场景
  1. 场景图按"铺满整幅画面"(cover-fit)缩放, 于是同一张图里各个车窗拿到的是
     场景里对应位置的片段 —— 左侧窗看到左侧景、右侧窗看到右侧景, 空间上自洽。
  2. 通过遮罩(腐蚀+羽化)贴回原图, 车窗以外像素 = 原图, 逐像素不变。
"""
import glob
import os

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(ROOT, "output-scenes")
OUT_DIR = os.path.join(ROOT, "output-cp001-interior-final")

# seq: (原图, 遮罩, 场景图, 成品名)
MAP = {
    1: ("ref/v27/v27_cabin_driver.jpg", "masks/driver.png", "001", "内01_主驾视角_小区地面停车位_晴天.png"),
    2: ("ref/v27/v27_cabin_passenger.jpg", "masks/passenger.png", "002", "内02_副驾视角_商场外停车区_下午暖光.png"),
    3: ("ref/v27/v27_cabin_rear.jpg", "masks/rear.png", "003", "内03_后排向前_城市马路边_阴天.png"),
    4: ("ref/v27/v27_cabin_flat.jpg", "masks/flat.png", "004", "内04_后备箱视角_小区楼下_傍晚.png"),
    5: ("ref/v27/v27_cabin_wheel.jpg", "masks/wheel.png", "005", "内05_方向盘特写_地下车库B1_冷白灯.png"),
    6: ("ref/v27/v27_cabin_driver.jpg", "masks/driver.png", "006", "内06_主驾视角_公园附近停车区_晴天树影.png"),
    7: ("ref/v27/v27_cabin_passenger.jpg", "masks/passenger.png", "007", "内07_副驾视角_露天停车场_晴天正午.png"),
    8: ("ref/v27/v27_cabin_rear.jpg", "masks/rear.png", "008", "内08_后排向前_写字楼楼下_白天.png"),
}

ERODE = 8
FEATHER = 6


def editable_mask(path, size):
    """从 OpenAI 格式 RGBA 遮罩取可编辑区(alpha=0 处), 返回 L 模式 255=可编辑"""
    rgba = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
    return rgba.getchannel("A").point(lambda v: 255 - v)


def cover_fit(img, size):
    """等比缩放并居中裁剪, 铺满目标尺寸(不拉伸、不留边)"""
    tw, th = size
    sw, sh = img.size
    s = max(tw / sw, th / sh)
    img = img.resize((max(1, int(round(sw * s))), max(1, int(round(sh * s)))), Image.LANCZOS)
    left = (img.width - tw) // 2
    top = (img.height - th) // 2
    return img.crop((left, top, left + tw, top + th))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for seq, (rel_base, rel_mask, scene_seq, out_name) in MAP.items():
        base = Image.open(os.path.join(ROOT, rel_base)).convert("RGB")
        w, h = base.size

        hits = sorted(glob.glob(os.path.join(SCENES_DIR, f"{scene_seq}_*.png")))
        if not hits:
            print(f"! 缺少场景图 {scene_seq}")
            continue
        scene = cover_fit(Image.open(hits[0]).convert("RGB"), (w, h))

        m = editable_mask(os.path.join(ROOT, rel_mask), (w, h))
        m = m.filter(ImageFilter.MinFilter(ERODE * 2 + 1)).filter(ImageFilter.GaussianBlur(FEATHER))

        out = Image.composite(scene, base, m)
        dst = os.path.join(OUT_DIR, out_name)
        out.save(dst, quality=95)

        # 校验遮罩外必须与原图逐像素一致
        diff, b, o = 0, base.load(), out.load()
        for y in range(0, h, 3):
            for x in range(0, w, 3):
                if m.getpixel((x, y)) == 0 and b[x, y] != o[x, y]:
                    diff += 1
        print(f"{out_name:<44} {w}x{h}  遮罩外改动 {diff}(抽样)  -> {dst}")
    print("输出目录:", OUT_DIR)


if __name__ == "__main__":
    main()
