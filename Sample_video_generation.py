"""
Sample_video_generation.py

Generates a slideshow summary video directly from a manually written summary.
No lecture video or audio required — just fill in the summary data below and run.

Usage:
    python Sample_video_generation.py

Output:
    sample_output/sample_slideshow.mp4
"""

import os
import sys

# Make sure the pipeline module is importable
sys.path.insert(0, os.path.dirname(__file__))

from pipeline.slideshow_video import create_slideshow_video

# ─────────────────────────────────────────────────────────────────────────────
# EDIT THIS SECTION — provide your lecture summary here
# ─────────────────────────────────────────────────────────────────────────────

overall_summary = {
    "lecture_title": "Introduction to Machine Learning",
    "main_topic": "Supervised Learning, Model Evaluation, and Neural Networks",
    "intro_voiceover": (
        "Welcome to this AI-generated summary of Introduction to Machine Learning. "
        "In this video, we'll cover the core concepts of supervised learning, "
        "how to evaluate models, and the fundamentals of neural networks."
    ),
    "key_takeaways": [
        "Supervised learning uses labelled data to train predictive models.",
        "Train/test splits and cross-validation prevent overfitting.",
        "Accuracy, precision, recall, and F1 score measure model performance.",
        "Neural networks learn hierarchical feature representations.",
        "Gradient descent optimises model weights by minimising loss.",
        "Regularisation techniques like dropout reduce overfitting in deep networks.",
    ],
}

fused_slides = [
    {
        "slide_number": 1,
        "timestamp": 60,   # seconds into the lecture where this slide appeared
        "summary": {
            "title": "What is Supervised Learning?",
            "summary": (
                "Supervised learning is a type of machine learning where a model is trained "
                "on labelled input-output pairs. The model learns a mapping from inputs to "
                "outputs and can then predict labels for unseen data."
            ),
            "key_concepts": [
                "Labelled training data (features + target)",
                "Classification vs Regression tasks",
                "Generalisation to unseen examples",
                "Examples: spam detection, house price prediction",
            ],
            "code_example": "",
            "voiceover_script": (
                "Supervised learning trains a model on labelled data — pairs of inputs and "
                "correct outputs. The model learns patterns so it can predict labels for new, "
                "unseen examples. Common tasks include classification and regression."
            ),
        },
    },
    {
        "slide_number": 2,
        "timestamp": 180,
        "summary": {
            "title": "Train / Test Split and Cross-Validation",
            "summary": (
                "To evaluate how well a model generalises, data is split into training and "
                "test sets. Cross-validation rotates the validation set across multiple folds "
                "to give a more reliable performance estimate."
            ),
            "key_concepts": [
                "Training set: used to fit the model",
                "Test set: held-out data for final evaluation",
                "K-Fold cross-validation reduces variance in evaluation",
                "Avoid data leakage between splits",
            ],
            "code_example": (
                "from sklearn.model_selection import train_test_split, KFold\n"
                "X_train, X_test, y_train, y_test = train_test_split(\n"
                "    X, y, test_size=0.2, random_state=42\n"
                ")\n"
                "kf = KFold(n_splits=5, shuffle=True)"
            ),
            "voiceover_script": (
                "We split data into training and test sets to check if our model generalises. "
                "K-Fold cross-validation rotates the validation portion across five folds, "
                "giving a more reliable accuracy estimate than a single split."
            ),
        },
    },
    {
        "slide_number": 3,
        "timestamp": 360,
        "summary": {
            "title": "Model Evaluation Metrics",
            "summary": (
                "Accuracy alone is misleading on imbalanced datasets. Precision, recall, and "
                "F1 score give a fuller picture. The confusion matrix shows exactly where "
                "the model makes mistakes."
            ),
            "key_concepts": [
                "Accuracy = correct predictions / total predictions",
                "Precision = TP / (TP + FP)  —  avoids false alarms",
                "Recall = TP / (TP + FN)  —  avoids missed positives",
                "F1 = harmonic mean of precision and recall",
            ],
            "code_example": (
                "from sklearn.metrics import classification_report\n"
                "print(classification_report(y_test, y_pred))"
            ),
            "voiceover_script": (
                "Accuracy can be misleading when classes are imbalanced. Instead, we use "
                "precision, recall, and F1 score. The classification report from scikit-learn "
                "shows all three metrics at once, along with a per-class breakdown."
            ),
        },
    },
    {
        "slide_number": 4,
        "timestamp": 540,
        "summary": {
            "title": "Introduction to Neural Networks",
            "summary": (
                "A neural network is a stack of layers, each applying a linear transformation "
                "followed by a non-linear activation function. Deep networks learn hierarchical "
                "feature representations from raw data."
            ),
            "key_concepts": [
                "Input layer → Hidden layers → Output layer",
                "Activation functions: ReLU, Sigmoid, Softmax",
                "Forward pass computes predictions",
                "Backpropagation computes gradients for weight updates",
            ],
            "code_example": (
                "import torch.nn as nn\n"
                "model = nn.Sequential(\n"
                "    nn.Linear(784, 256),\n"
                "    nn.ReLU(),\n"
                "    nn.Linear(256, 10),\n"
                "    nn.Softmax(dim=1)\n"
                ")"
            ),
            "voiceover_script": (
                "Neural networks stack layers of linear transformations and activation functions. "
                "During the forward pass, data flows through each layer to produce a prediction. "
                "Backpropagation then computes gradients so gradient descent can update the weights."
            ),
        },
    },
    {
        "slide_number": 5,
        "timestamp": 720,
        "summary": {
            "title": "Gradient Descent and Regularisation",
            "summary": (
                "Gradient descent minimises the loss function by iteratively updating weights "
                "in the direction of the negative gradient. Regularisation techniques such as "
                "L2 weight decay and dropout reduce overfitting."
            ),
            "key_concepts": [
                "Learning rate controls step size during optimisation",
                "Mini-batch SGD balances speed and stability",
                "L2 regularisation penalises large weights",
                "Dropout randomly zeros neurons during training",
            ],
            "code_example": (
                "optimizer = torch.optim.Adam(model.parameters(), lr=1e-3,\n"
                "                             weight_decay=1e-4)\n"
                "dropout = nn.Dropout(p=0.3)"
            ),
            "voiceover_script": (
                "Gradient descent updates model weights by moving in the direction that reduces "
                "the loss. The learning rate controls how big each step is. To prevent overfitting, "
                "L2 regularisation penalises large weights, and dropout randomly disables neurons "
                "during training."
            ),
        },
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# OUTPUT SETTINGS — change paths if needed
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_output")
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "sample_slideshow.mp4")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("=" * 60)
    print("  Sample Slideshow Video Generator")
    print("=" * 60)
    print(f"  Slides   : {len(fused_slides)}")
    print(f"  Output   : {OUTPUT_VIDEO}")
    print("=" * 60)

    def progress(p):
        bar = int(p * 40)
        print(f"\r  Progress : [{'█' * bar}{'░' * (40 - bar)}] {int(p * 100):3d}%", end="", flush=True)

    result = create_slideshow_video(
        fused_slides=fused_slides,
        overall_summary=overall_summary,
        output_path=OUTPUT_VIDEO,
        temp_dir=TEMP_DIR,
        progress_callback=progress,
    )

    print(f"\n\n  Done! Video saved to:\n  {result}\n")
