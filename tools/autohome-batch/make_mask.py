#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成车窗遮罩(用于 /images/edits 的 mask 参数)

用途: 内饰图"不改原图、只换窗外场景" —— 把车窗玻璃区域设为可编辑(alpha=0),
      其余全部区域设为保留(alpha=255), 模型就只会重画玻璃里的景色。

用法:
  1. 编辑 polygons.json, 为每张图列出玻璃区域多边形(归一化坐标 0~1)
     支持 add(可编辑) 与 sub(从可编辑区里挖掉, 如后视镜/车内立柱)
  2. python make_mask.py
  3. 产出: masks/<name>.png (遮罩) 与 mask_preview/<name>.jpg (叠加预览, 用于人工核对边界)
"""
import json
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(ROOT, "polygons.json")
MASK_DIR = os.path.join(ROOT, "masks")
PREVIEW_DIR = os.path.join(ROOT, "mask_preview")


def build_mask(size, add_polys, sub_polys, feather=0, invert_for_openai=True):
    """返回 L 模式遮罩: 255=可编辑区域, 0=保留区域"""
    w, h = size
    # 先全部涂黑(保留), 再把可编辑区涂白
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for poly in add_polys:
        d.polygon([(x * w, y * h) for x, y in poly], fill=255)
    for poly in sub_polys:
        d.polygon([(x * w, y * h) for x, y in poly], fill=0)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def to_openai_mask(editable):
    """OpenAI /images/edits 语义: 透明(alpha=0)处才会被编辑 -> 把可编辑区做成透明"""
    w, h = editable.size
    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    # 可编辑区 alpha=0
    rgba.putalpha(editable.point(lambda v: 255 - v))
    return rgba


def main():
    with open(CFG, encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(MASK_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    for item in cfg["items"]:
        src = os.path.join(ROOT, item["image"])
        im = Image.open(src).convert("RGB")
        w, h = im.size
        editable = build_mask((w, h), item.get("add", []), item.get("sub", []), item.get("feather", 0))

        # 1) 给接口用的 RGBA 遮罩
        out_mask = os.path.join(MASK_DIR, item["name"] + ".png")
        to_openai_mask(editable).save(out_mask)

        # 2) 人工核对用的叠加预览
        prev = im.copy()
        tint = Image.new("RGB", (w, h), (255, 0, 0))
        prev = Image.composite(tint, prev, editable.point(lambda v: int(v * 0.45)))
        # 画边界线
        edge = editable.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
        prev = Image.composite(Image.new("RGB", (w, h), (0, 255, 0)), prev, edge)
        prev.thumbnail((760, 1014))
        out_prev = os.path.join(PREVIEW_DIR, item["name"] + ".jpg")
        prev.save(out_prev, quality=88)

        px = sum(1 for v in editable.getdata() if v > 127)
        print(f"{item['name']:<28} {w}x{h}  可编辑占比 {px / (w * h) * 100:5.1f}%  -> {out_mask}")

    print("预览目录:", PREVIEW_DIR)


if __name__ == "__main__":
    main()
