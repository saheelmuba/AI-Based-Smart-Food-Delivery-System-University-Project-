"""
Utility to prepare spoilage dataset directories.

Usage:
 - Place unlabeled images in `data_pool/`.
 - Run: python prepare_spoilage_dataset.py --scan data_pool --export-csv labels.csv
 - Manually label CSV (filename,label where label is GOOD or SPOILED)
 - Run: python prepare_spoilage_dataset.py --apply labels.csv --good-dir food_data/datasets/good_food_images --spoiled-dir food_data/datasets/spoilage_images

The script tries to auto-label files whose names contain keywords like 'spoiled' or 'good'.
"""
import argparse
from pathlib import Path
import csv

KEY_SPOILED = ['spoiled', 'mold', 'rotten', 'bad']
KEY_GOOD = ['fresh', 'good', 'ok']


def scan_pool(pool_dir: Path, out_csv: Path):
    files = sorted([p for p in pool_dir.glob('*') if p.is_file()])
    with out_csv.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['filename', 'label'])
        for p in files:
            label = ''
            name = p.name.lower()
            if any(k in name for k in KEY_SPOILED):
                label = 'SPOILED'
            elif any(k in name for k in KEY_GOOD):
                label = 'GOOD'
            writer.writerow([str(p), label])
    print(f'Wrote {out_csv} with {len(files)} entries')


def apply_labels(csv_path: Path, good_dir: Path, spoiled_dir: Path):
    good_dir.mkdir(parents=True, exist_ok=True)
    spoiled_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    with csv_path.open('r', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            src = Path(row['filename'])
            label = row.get('label','').strip().upper()
            if not src.exists():
                continue
            if label == 'GOOD':
                dst = good_dir / src.name
                src.rename(dst)
                moved += 1
            elif label == 'SPOILED':
                dst = spoiled_dir / src.name
                src.rename(dst)
                moved += 1
    print(f'Moved {moved} files according to {csv_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan', type=str, help='Directory with unlabeled images to scan')
    parser.add_argument('--export-csv', type=str, help='CSV output for labeling')
    parser.add_argument('--apply', type=str, help='CSV with labels to apply')
    parser.add_argument('--good-dir', type=str, default='food_data/datasets/good_food_images')
    parser.add_argument('--spoiled-dir', type=str, default='food_data/datasets/spoilage_images')
    args = parser.parse_args()

    if args.scan and args.export_csv:
        scan_pool(Path(args.scan), Path(args.export_csv))
    elif args.apply:
        apply_labels(Path(args.apply), Path(args.good_dir), Path(args.spoiled_dir))
    else:
        parser.print_help()
