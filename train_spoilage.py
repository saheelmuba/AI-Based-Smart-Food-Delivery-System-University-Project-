"""
Training Script for Spoilage Detection Model
"""
import argparse
from pathlib import Path
from spoilage_detector import SpoilageDetector
from food_ai_config import GOOD_FOOD_DATASET, SPOILAGE_DATASET, MODEL_CONFIG


def setup_directories():
    """Create necessary dataset directories"""
    GOOD_FOOD_DATASET.mkdir(parents=True, exist_ok=True)
    SPOILAGE_DATASET.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created dataset directories:")
    print(f"  Good food images:   {GOOD_FOOD_DATASET}")
    print(f"  Spoiled images:     {SPOILAGE_DATASET}")


def check_dataset():
    """Check if dataset is ready"""
    good_images = list(GOOD_FOOD_DATASET.glob('**/*.jpg')) + list(GOOD_FOOD_DATASET.glob('**/*.png'))
    spoiled_images = list(SPOILAGE_DATASET.glob('**/*.jpg')) + list(SPOILAGE_DATASET.glob('**/*.png'))
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  Good food images:  {len(good_images)} images")
    print(f"  Spoiled images:    {len(spoiled_images)} images")
    print(f"  Total:             {len(good_images) + len(spoiled_images)} images")
    
    min_required = 20
    if len(good_images) < min_required or len(spoiled_images) < min_required:
        print(f"\n⚠ Warning: Minimum {min_required} images per class recommended")
        print(f"  Current: Good={len(good_images)}, Spoiled={len(spoiled_images)}")
        return False
    
    return True


def train_model(epochs=50, batch_size=32, learning_rate=0.001):
    """Train the spoilage detection model"""
    
    print("\n🏋️  Training Spoilage Detection Model")
    print("=" * 60)
    
    # Check dataset
    if not check_dataset():
        print("\n❌ Insufficient training data. Please add more images to the dataset.")
        return False
    
    # Initialize model
    device = 'cuda' if __import__('torch').cuda.is_available() else 'cpu'
    print(f"\n🖥️  Using device: {device.upper()}")
    
    detector = SpoilageDetector(backbone='efficientnet_b0', device=device)
    
    # Train
    print(f"\n⚙️  Training configuration:")
    print(f"  Epochs:           {epochs}")
    print(f"  Batch size:       {batch_size}")
    print(f"  Learning rate:    {learning_rate}")
    print(f"  Backbone:         efficientnet_b0")
    
    success = detector.train(
        epochs=epochs,
        batch_size=batch_size,
        lr=learning_rate
    )
    
    if success:
        print(f"\n✅ Training completed successfully!")
        print(f"Model saved to: {detector.model.__dict__.get('_modules', {}).get('backbone')}")
    else:
        print(f"\n❌ Training failed")
    
    return success


def test_inference(image_path: str):
    """Test the trained model on a single image"""
    print(f"\n🧪 Testing inference on: {image_path}")
    print("=" * 60)
    
    detector = SpoilageDetector(device='cpu')
    result = detector.infer(image_path)
    
    if result.get('success'):
        print(f"✓ Status: {result['status']}")
        print(f"✓ Good probability: {result['good_probability']:.2%}")
        print(f"✓ Spoiled probability: {result['spoiled_probability']:.2%}")
        print(f"✓ Confidence: {result['confidence']:.2%}")
    else:
        print(f"✗ Error: {result.get('error')}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Train spoilage detection model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Setup directories
  python train_spoilage.py setup
  
  # Train model with default settings
  python train_spoilage.py train
  
  # Train with custom parameters
  python train_spoilage.py train --epochs 100 --batch-size 16 --lr 0.0001
  
  # Test inference
  python train_spoilage.py test path/to/image.jpg
  
  # Check dataset
  python train_spoilage.py check
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    subparsers.add_parser('setup', help='Setup dataset directories')
    
    # Check command
    subparsers.add_parser('check', help='Check dataset statistics')
    
    # Train command
    train_cmd = subparsers.add_parser('train', help='Train the model')
    train_cmd.add_argument('--epochs', type=int, default=50,
                          help='Number of epochs (default: 50)')
    train_cmd.add_argument('--batch-size', type=int, default=32,
                          help='Batch size (default: 32)')
    train_cmd.add_argument('--lr', '--learning-rate', type=float, default=0.001,
                          help='Learning rate (default: 0.001)')
    
    # Test command
    test_cmd = subparsers.add_parser('test', help='Test inference on image')
    test_cmd.add_argument('image', help='Path to test image')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'setup':
        setup_directories()
    
    elif args.command == 'check':
        check_dataset()
    
    elif args.command == 'train':
        train_model(
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr
        )
    
    elif args.command == 'test':
        test_inference(args.image)


if __name__ == '__main__':
    main()
