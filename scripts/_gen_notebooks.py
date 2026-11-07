import json, os, sys

base = os.path.join(os.path.dirname(__file__), "..", "notebooks")
os.makedirs(base, exist_ok=True)

def nb(cells):
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11.0"}}, "nbformat": 4, "nbformat_minor": 5}

_id = [0]
def md(src):
    _id[0] += 1
    return {"cell_type": "markdown", "metadata": {}, "source": src.split("\n"), "id": f"m{_id[0]}"}

def code(src):
    _id[0] += 1
    return {"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": src.split("\n"), "id": f"c{_id[0]}"}

nbs = {}

nbs["01_dataset_exploration.ipynb"] = nb([
    md("# NEXUS AI - 01 Dataset Exploration\nExplore RDD2022 road damage dataset structure, class distribution, and image quality."),
    code("""import os, sys
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path.cwd().parent))

DATASET = Path('../datasets/road_damage')
print('Dataset exists:', DATASET.exists())
print('Images in train:', len(list((DATASET/'images/train').glob('*.jpg'))))
print('Labels in train:', len(list((DATASET/'labels/train').glob('*.txt'))))"""),
    code("""from collections import Counter
class_counts = Counter()
for lbl in (DATASET/'labels/train').glob('*.txt'):
    for line in lbl.read_text().splitlines():
        parts = line.strip().split()
        if parts: class_counts[int(float(parts[0]))] += 1
CLASSES = ['medium_damaged','severely_damaged','unpaved','longitudinal_transverse_crack','alligator_crack']
names = [CLASSES[i] for i in sorted(class_counts)]
plt.bar(names, class_counts.values(), color='steelblue')
plt.title('RDD2022 Class Distribution'); plt.xticks(rotation=20); plt.tight_layout(); plt.show()"""),
    code("""imgs = list((DATASET/'images/train').glob('*.jpg'))[:4]
fig, axes = plt.subplots(1, 4, figsize=(16,4))
for ax, img_path in zip(axes, imgs):
    img = Image.open(img_path); ax.imshow(img)
    ax.set_title(str(img.size), fontsize=9); ax.axis('off')
plt.suptitle('Sample Images'); plt.tight_layout(); plt.show()"""),
])

nbs["02_image_preprocessing.ipynb"] = nb([
    md("# NEXUS AI - 02 Image Preprocessing\nCLAHE, denoising, sharpening, and augmentation pipeline."),
    code("""import cv2, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
import sys; sys.path.insert(0, str(Path.cwd().parent))
from ai_engine.detection.preprocessing import preprocess_image, PreprocessConfig

cfg = PreprocessConfig()
samples = list(Path('../datasets/road_damage/images/train').glob('*.jpg'))
print('Config:', cfg); print('Samples found:', len(samples))"""),
    code("""if samples:
    img = cv2.imread(str(samples[0]))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    processed = preprocess_image(str(samples[0]), cfg)
    processed_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
    fig, axes = plt.subplots(1, 2, figsize=(12,5))
    axes[0].imshow(img_rgb); axes[0].set_title('Original')
    axes[1].imshow(processed_rgb); axes[1].set_title('Preprocessed (CLAHE+Sharpen)')
    for ax in axes: ax.axis('off')
    plt.tight_layout(); plt.show()"""),
    code("""if samples:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges_raw = cv2.Canny(gray, 50, 150)
    gray_p = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
    edges_clahe = cv2.Canny(gray_p, 50, 150)
    fig, axes = plt.subplots(2, 2, figsize=(12,8))
    axes[0,0].imshow(img_rgb); axes[0,0].set_title('Original')
    axes[0,1].imshow(processed_rgb); axes[0,1].set_title('CLAHE Enhanced')
    axes[1,0].imshow(edges_raw, cmap='gray'); axes[1,0].set_title('Edges (raw)')
    axes[1,1].imshow(edges_clahe, cmap='gray'); axes[1,1].set_title('Edges (CLAHE)')
    for ax in axes.flat: ax.axis('off')
    plt.tight_layout(); plt.show()"""),
])

nbs["03_road_damage_training.ipynb"] = nb([
    md("# NEXUS AI - 03 Road Damage YOLOv8 Training\nFine-tune YOLOv8n on RDD2022 using ultralytics."),
    code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
print('Model loaded. Classes:', model.names)"""),
    code("""DATA_YAML = str(Path('../datasets/road_damage/data.yaml').resolve())
print('data.yaml:', DATA_YAML)
# Uncomment below to run full training (requires GPU or several hours on CPU):
# results = model.train(data=DATA_YAML, epochs=50, imgsz=640, batch=16,
#                       device='cpu', project='../runs', name='rdd2022_yolov8n', patience=10)"""),
    code("""# Evaluate on val set (runs quickly with pretrained weights)
results = model.val(data=DATA_YAML, imgsz=640, split='val')
print('mAP50-95:', results.box.map)
print('mAP50:', results.box.map50)
print('Precision:', results.box.mp)
print('Recall:', results.box.mr)"""),
    code("""import cv2
samples = list(Path('../datasets/road_damage/images/val').glob('*.jpg'))[:2]
for img_path in samples:
    result = model.predict(str(img_path), conf=0.4, imgsz=640, verbose=False)
    annotated = cv2.cvtColor(result[0].numpy(), cv2.COLOR_BGR2RGB)
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10,7)); plt.imshow(annotated); plt.axis('off')
    plt.title('Detection: ' + img_path.name); plt.tight_layout(); plt.show()"""),
])

nbs["04_severity_analysis.ipynb"] = nb([
    md("# NEXUS AI - 04 Severity Analysis\nFeature extraction and XGBoost severity classification."),
    code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
import pandas as pd
import matplotlib.pyplot as plt
from ai_engine.severity.feature_extraction import FEATURE_NAMES

df = pd.read_csv('../datasets/severity_prediction/severity_data.csv')
print(len(df), 'rows'); print(list(df.columns)); df.head()"""),
    code("""sev_counts = df['severity'].value_counts()
plt.pie(sev_counts.values, labels=sev_counts.index, autopct='%1.1f%%',
        colors=['#22c55e','#f59e0b','#ef4444','#7c3aed'])
plt.title('Severity Distribution'); plt.tight_layout(); plt.show()"""),
    code("""num_cols = [c for c in FEATURE_NAMES if c in df.columns]
corr = df[num_cols].corr()
plt.figure(figsize=(12,8))
plt.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1)
plt.colorbar()
plt.xticks(range(len(num_cols)), num_cols, rotation=45, ha='right')
plt.yticks(range(len(num_cols)), num_cols)
plt.title('Feature Correlation Matrix'); plt.tight_layout(); plt.show()"""),
    code("""from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import classification_report

label_map = {'LOW':0,'MEDIUM':1,'HIGH':2,'CRITICAL':3}
X = df[[c for c in FEATURE_NAMES if c in df.columns]].values
y = df['severity'].map(label_map).values
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
clf = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1,
                         objective='multi:softprob', num_class=4)
clf.fit(Xtr, ytr)
pred = clf.predict(Xte)
print(classification_report(yte, pred, target_names=list(label_map.keys())))"""),
])

nbs["05_before_after_comparison.ipynb"] = nb([
    md("# NEXUS AI - 05 Before/After Repair Comparison\nSSIM, edge density, and AI repair verification."),
    code("""import cv2, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
import sys; sys.path.insert(0, str(Path.cwd().parent))
from ai_engine.resolution_verification.damage_comparison import (
    ssim_single, edge_density, region_comparison
)"""),
    code("""# Simulate before/after pair
np.random.seed(42)
before = np.random.randint(80, 200, (300, 400, 3), dtype=np.uint8)
after = before.copy()
mask = np.zeros((300, 400), dtype=bool)
mask[100:200, 150:250] = True
blurred = cv2.GaussianBlur(after, (15, 15), 0)
after[mask] = blurred[mask]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB)); axes[0].set_title('Before')
axes[1].imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB)); axes[1].set_title('After')
for ax in axes: ax.axis('off')
plt.tight_layout(); plt.show()"""),
    code("""score = ssim_single(before, after)
eb = edge_density(before); ea = edge_density(after)
reg = region_comparison(before, after)
print('SSIM:', round(score, 4))
print('Edge before:', round(eb, 4), 'Edge after:', round(ea, 4))
print('Edge reduction:', reg['edge_reduction_pct'], '%')"""),
    code("""import tempfile, os
from ai_engine.resolution_verification.compare_images import compare_images
bt = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
at = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
cv2.imwrite(bt.name, before); cv2.imwrite(at.name, after)
result = compare_images(bt.name, at.name)
print('resolved_probability:', result['resolved_probability'])
print('recommendation:', result['recommendation'])
os.unlink(bt.name); os.unlink(at.name)"""),
])

nbs["06_geographic_analysis.ipynb"] = nb([
    md("# NEXUS AI - 06 Geographic Analysis\nHotspot clustering, ward analytics, and map visualisation."),
    code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from ai_engine.geographic_intelligence.hotspot_analysis import find_hotspots, IssuePoint"""),
    code("""df = pd.read_csv('../datasets/geographic_intelligence/issue_coordinates.csv')
print(len(df), 'issues loaded'); df.head()"""),
    code("""points = []
for _, row in df.iterrows():
    points.append(IssuePoint(
        issue_id=int(row['issue_id']),
        lat=float(row['lat']), lon=float(row['lon']),
        severity=str(row.get('severity', 'medium')),
        category=str(row.get('category', 'other')),
        status='open',
        created_at=datetime.now(timezone.utc),
    ))
print(len(points), 'points ready')"""),
    code("""hotspots = find_hotspots(points, eps_km=0.3, min_pts=2)
for h in hotspots:
    print(h.hotspot_id, h.issue_count, 'issues', 'risk=', round(h.risk_score, 3), h.top_category, 'trend=', h.trend)"""),
    code("""try:
    import folium
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=11, tiles='CartoDB positron')
    sev_c = {'LOW':'green','MEDIUM':'orange','HIGH':'red','CRITICAL':'purple'}
    for p in points:
        folium.CircleMarker([p.lat, p.lon], radius=8,
            color=sev_c.get(p.severity.upper(), 'gray'), fill=True,
            popup=p.category + ' | ' + p.severity).add_to(m)
    for h in hotspots:
        folium.Circle([h.centroid_lat, h.centroid_lon],
            radius=int(h.radius_km * 1000), color='crimson',
            fill=True, fill_opacity=0.15,
            popup='Hotspot: ' + str(h.issue_count) + ' issues').add_to(m)
    m
except ImportError:
    print('Install folium: pip install folium')"""),
])

for name, data in nbs.items():
    out = os.path.join(base, name)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Created:", name)

print("All notebooks done")
