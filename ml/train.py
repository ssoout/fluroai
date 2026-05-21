from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import torch  # type: ignore[import]
import torch.nn as nn  # type: ignore[import]
from torch.optim import AdamW  # type: ignore[import]
from torch.optim.lr_scheduler import CosineAnnealingLR  # type: ignore[import]
from torch.utils.data import DataLoader, WeightedRandomSampler  # type: ignore[import]
from torchvision import datasets, models, transforms  # type: ignore[import]
from tqdm import tqdm

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_dataloaders(
    dataset_root: Path, batch_size: int = 32
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    train_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            normalize,
        ]
    )
    eval_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            normalize,
        ]
    )

    train_ds = datasets.ImageFolder(dataset_root / "train", transform=train_transform)
    val_ds = datasets.ImageFolder(dataset_root / "val", transform=eval_transform)
    test_ds = datasets.ImageFolder(dataset_root / "test", transform=eval_transform)

    # handle class imbalance via weighted sampler
    class_counts = torch.bincount(torch.tensor(train_ds.targets))
    class_weights = 1.0 / class_counts.float()
    sample_weights = class_weights[train_ds.targets]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=4)
    return train_loader, val_loader, test_loader


def build_model(num_classes: int = 2, pretrained: bool = True) -> nn.Module:
    if pretrained:
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    else:
        model = models.resnet18(weights=None)
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, num_classes),
    )
    return model


def train_one_epoch(model: nn.Module, loader: DataLoader, criterion, optimizer) -> float:
    model.train()
    running_loss = 0.0
    for inputs, labels in tqdm(loader, desc="train", leave=False):
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
    return running_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, labels in loader:
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        running_loss += loss.item() * inputs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)
    return {
        "loss": running_loss / len(loader.dataset),
        "accuracy": correct / total if total else 0.0,
    }


def save_checkpoint(model: nn.Module, class_to_idx: Dict[str, int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "class_to_idx": class_to_idx,
        },
        output_path,
    )

    with (output_path.with_suffix(".json")).open("w", encoding="utf-8") as fp:
        json.dump({"class_to_idx": class_to_idx}, fp, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train FluoroDesk chest X-ray classifier")
    parser.add_argument("--data-dir", type=Path, default=Path("chest_xray"), help="Root of dataset (train/val/test)")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output", type=Path, default=Path("ml/models/resnet18_fluoro.pth"))
    parser.add_argument("--eval-only", action="store_true", help="Skip training, just evaluate saved model")
    parser.add_argument("--no-pretrained", action="store_true", help="Use model without pretrained weights (faster start, but worse results)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_loader, val_loader, test_loader = build_dataloaders(args.data_dir, args.batch_size)

    model = build_model(num_classes=len(train_loader.dataset.classes), pretrained=not args.no_pretrained).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    history = []

    if args.eval_only:
        checkpoint = torch.load(args.output, map_location=DEVICE)
        model.load_state_dict(checkpoint["state_dict"])
        metrics = evaluate(model, test_loader, criterion)
        print("Eval:", metrics)
        return

    for epoch in range(1, args.epochs + 1):
        print(f"Epoch {epoch}/{args.epochs}")
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer)
        val_metrics = evaluate(model, val_loader, criterion)
        scheduler.step()

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_metrics["loss"],
                "val_accuracy": val_metrics["accuracy"],
            }
        )
        print(f"train_loss={train_loss:.4f} val_loss={val_metrics['loss']:.4f} acc={val_metrics['accuracy']:.4f}")

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            save_checkpoint(model, train_loader.dataset.class_to_idx, args.output)

    print("Training complete. Best val acc:", best_val_acc)
    best_checkpoint = torch.load(args.output, map_location=DEVICE)
    model.load_state_dict(best_checkpoint["state_dict"])
    test_metrics = evaluate(model, test_loader, criterion)
    print("Test metrics:", test_metrics)

    history_path = args.output.with_suffix(".history.json")
    with history_path.open("w", encoding="utf-8") as fp:
        json.dump(history, fp, ensure_ascii=False, indent=2)
    print(f"Saved training history to {history_path}")


if __name__ == "__main__":
    main()

