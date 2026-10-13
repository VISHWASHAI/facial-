"""Evaluate the emotion model on the FER2013 test images and save metric pictures.

    python evaluate.py --per-class 100     # random sample (fast)
    python evaluate.py                     # full test set (slow disk reads)

FER2013 images are already face crops, so face detection is skipped. The model also has a
"Contempt" class that FER2013 does not, so it is excluded when picking the prediction.
"""
import argparse
import random
from pathlib import Path

import cv2
import matplotlib
import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.emotion import get_engine  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / "data" / "fer2013_test"
OUT_DIR = ROOT / "docs" / "v2-evaluation"

# FER2013 folder -> label used by the app's model
FOLDER_TO_LABEL = {"angry": "Angry", "disgust": "Disgusted", "fear": "Fearful", "happy": "Happy",
                   "neutral": "Neutral", "sad": "Sad", "surprise": "Surprised"}
GROUPS = {"Angry": "Negative", "Disgusted": "Negative", "Fearful": "Negative", "Sad": "Negative",
          "Neutral": "Neutral", "Happy": "Positive", "Surprised": "Positive"}


def load_sample(per_class):
    random.seed(0)  # same sampling as the v1 evaluation, so the same images are compared
    images, labels = [], []
    folders = sorted(p.name for p in TEST_DIR.iterdir() if p.is_dir())
    for folder in folders:
        files = sorted((TEST_DIR / folder).iterdir())
        if per_class:
            files = random.sample(files, min(per_class, len(files)))
        for f in files:
            img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            images.append(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
            labels.append(FOLDER_TO_LABEL[folder])
    return images, labels


def plot(y_true, y_pred, names, title, path, figsize):
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=range(len(names)))
    cm_norm = cm / cm.sum(axis=1, keepdims=True)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=range(len(names)), zero_division=0)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=figsize)
    a1.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    a1.set_xticks(range(len(names)), names, rotation=45, ha="right")
    a1.set_yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(names)):
            a1.text(j, i, f"{cm_norm[i, j]:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if cm_norm[i, j] > 0.5 else "black")
    a1.set_xlabel("Predicted")
    a1.set_ylabel("True")
    a1.set_title("Confusion matrix (row-normalised)")
    pos = np.arange(len(names))
    a2.bar(pos - 0.27, prec, 0.27, label="Precision")
    a2.bar(pos, rec, 0.27, label="Recall")
    a2.bar(pos + 0.27, f1, 0.27, label="F1-score")
    a2.set_xticks(pos, names, rotation=45, ha="right")
    a2.set_ylim(0, 1)
    a2.set_title("Per-class metrics")
    a2.legend()
    fig.suptitle(f"{title} - accuracy {acc:.1%}", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return acc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=None)
    args = parser.parse_args()
    scope = f"sample of {args.per_class} images per class" if args.per_class else "full test set"

    images, labels = load_sample(args.per_class)
    names = sorted(set(labels))
    engine = get_engine()
    y_true = np.array([names.index(l) for l in labels])
    y_pred = []
    for img in images:
        scores = engine.classify_face(img)
        y_pred.append(names.index(max(names, key=lambda n: scores[n])))  # ignores "Contempt"
    y_pred = np.array(y_pred)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = (f"Model: HSEmotion enet_b0_8_best_vgaf (pretrained, not fine-tuned)\n"
              f"Evaluation on FER2013 {scope} ({len(y_true)} images)\n"
              f"Overall accuracy: {accuracy_score(y_true, y_pred):.4f}\n\n"
              + classification_report(y_true, y_pred, target_names=names, digits=3))

    group_names = ["Negative", "Neutral", "Positive"]
    to_group = np.array([group_names.index(GROUPS[n]) for n in names])
    g_true, g_pred = to_group[y_true], to_group[y_pred]
    report += (f"\n\nMood-group evaluation (Negative = angry/disgusted/fearful/sad, Neutral, "
               f"Positive = happy/surprised)\nOverall accuracy: {accuracy_score(g_true, g_pred):.4f}\n\n"
               + classification_report(g_true, g_pred, target_names=group_names, digits=3))
    print(report)
    (OUT_DIR / "evaluation_report.txt").write_text(report, encoding="utf-8")

    title = f"Emotion model on FER2013 ({scope}, {len(y_true)} images)"
    plot(y_true, y_pred, names, title, OUT_DIR / "evaluation_metrics.png", (14, 6))
    plot(g_true, g_pred, group_names, "Mood groups: " + title, OUT_DIR / "evaluation_mood_groups.png", (12, 5))
    print(f"Saved results to {OUT_DIR}")


if __name__ == "__main__":
    main()
