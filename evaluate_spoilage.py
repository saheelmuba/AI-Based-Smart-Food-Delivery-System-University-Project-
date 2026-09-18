"""
Evaluate spoilage detector on labeled dataset directories and print simple metrics.
Usage: python evaluate_spoilage.py
"""
from spoilage_detector import SpoilageDetector, SimpleSpoilageClassifier
from food_ai_config import SPOILAGE_DATASET, GOOD_FOOD_DATASET, SPOILAGE_MODEL_PATH
from pathlib import Path


def evaluate(detector: SpoilageDetector):
    pos = list(Path(SPOILAGE_DATASET).glob('**/*'))
    neg = list(Path(GOOD_FOOD_DATASET).glob('**/*'))
    pos = [p for p in pos if p.suffix.lower() in ['.jpg','.png','.jpeg']]
    neg = [p for p in neg if p.suffix.lower() in ['.jpg','.png','.jpeg']]

    y_true = []
    y_pred = []

    for p in pos:
        res = detector.infer(str(p))
        if res.get('success'):
            y_true.append(1)
            y_pred.append(1 if res.get('status')=='SPOILED' else 0)

    for p in neg:
        res = detector.infer(str(p))
        if res.get('success'):
            y_true.append(0)
            y_pred.append(1 if res.get('status')=='SPOILED' else 0)

    # compute simple metrics
    tp = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==1)
    tn = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==0)
    fp = sum(1 for t,p in zip(y_true,y_pred) if t==0 and p==1)
    fn = sum(1 for t,p in zip(y_true,y_pred) if t==1 and p==0)

    total = len(y_true)
    acc = (tp+tn)/total if total>0 else 0
    precision = tp/(tp+fp) if (tp+fp)>0 else 0
    recall = tp/(tp+fn) if (tp+fn)>0 else 0
    f1 = 2*(precision*recall)/(precision+recall) if (precision+recall)>0 else 0

    print(f'Total samples: {total}')
    print(f'Accuracy: {acc:.4f} Precision: {precision:.4f} Recall: {recall:.4f} F1: {f1:.4f}')


if __name__ == '__main__':
    sd = SpoilageDetector()
    if Path(SPOILAGE_MODEL_PATH).exists():
        sd.load(str(SPOILAGE_MODEL_PATH))
        evaluate(sd)
    else:
        print('No trained spoilage model found; using SimpleSpoilageClassifier for heuristic evaluation')
        simple = SimpleSpoilageClassifier()
        # Wrap simple infer into the same interface
        class Wrapper:
            def infer(self, p):
                return simple.infer_simple(p)
        evaluate(Wrapper())
