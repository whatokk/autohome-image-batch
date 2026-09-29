# -*- coding: utf-8 -*-
"""
一键交付脚本：把批量出图的成品按「序号_场景」重命名、生成总览图、打 zip。

用法:
  # 用内置默认场景名
  python deliver.py --src output-v27 --out "V27_车主随手拍_交付" --prefix V27

  # 用自定义场景名（从 JSON 读，键为序号，值为场景描述）
  python deliver.py --src output-v23 --out "V23_车主随手拍_交付" --prefix V23 --scenes scenes-v23.json

  # 也可以完全不带场景名，直接按序号复制
  python deliver.py --src output --out "成品" --prefix MY

说明:
  · 中文目录名一律用 Python zipfile 打包。PowerShell 的 Compress-Archive 有编码风险。
  · 总览图固定 5 列 × 2 行，最多拼 10 张。
"""
import argparse
import glob
import json
import os
import shutil
import zipfile

from PIL import Image

# 内置默认场景名（10 组，对应左前45度到近距斜角的常见车辆拍摄位）
# 换成自己的场景，用 --scenes 传 JSON 覆盖即可。
SCENES = {
    1: '左前45度_小区地面停车位_晴天',
    2: '右前45度_商场外停车区',
    3: '正前方_路边车位_阴天',
    4: '左侧面_小区楼下_傍晚',
    5: '右侧面_办公楼附近停车位',
    6: '左后45度_露天停车场',
    7: '右后45度_地下停车场B1',
    8: '正后方_普通街边车位_傍晚',
    9: '稍俯拍_公园旁停车区',
    10: '近距斜角_小区路边',
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--prefix', required=True)
    ap.add_argument('--zip', default=None)
    ap.add_argument('--scenes', default=None,
                    help='场景名 JSON 文件，形如 {"1":"左前45度_小区停车位","2":"..."}。'
                         '不传则用内置默认场景名。')
    a = ap.parse_args()

    scenes = dict(SCENES)
    if a.scenes:
        with open(a.scenes, encoding='utf-8') as f:
            scenes = {int(k): v for k, v in json.load(f).items()}

    src = sorted(glob.glob(os.path.join(a.src, '[0-9][0-9][0-9]_*.png')))
    if not src:
        print('[!] %s 下没有成品' % a.src)
        return
    if os.path.exists(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)

    for f in src:
        seq = int(os.path.basename(f)[:3])
        scene = scenes.get(seq, 'seq%03d' % seq)
        name = '%s%03d_%s.png' % (a.prefix + '_', seq, scene)
        shutil.copy2(f, os.path.join(a.out, name))

    files = sorted(glob.glob(os.path.join(a.out, '*.png')))
    cols, rows = 5, 2
    tw, th = 420, 640
    sheet = Image.new('RGB', (cols * tw, rows * th), (245, 245, 247))
    for i, f in enumerate(files[:10]):
        im = Image.open(f).convert('RGB')
        im.thumbnail((tw - 14, th - 14))
        sheet.paste(im, ((i % cols) * tw + (tw - im.width) // 2,
                         (i // cols) * th + (th - im.height) // 2))
    sheet.save(os.path.join(a.out, '_总览.jpg'), quality=86)

    zpath = a.zip or (a.out.rstrip('/\\') + '.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as zf:
        for n in sorted(os.listdir(a.out)):
            zf.write(os.path.join(a.out, n), n)

    print('交付目录: %s' % a.out)
    for f in files:
        print('   %s  %dKB' % (os.path.basename(f), os.path.getsize(f) // 1024))
    print('压缩包: %s  %.1fMB' % (zpath, os.path.getsize(zpath) / 1024 / 1024))


if __name__ == '__main__':
    main()
