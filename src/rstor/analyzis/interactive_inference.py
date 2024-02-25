from rstor.synthetic_data.interactive.interactive_dead_leaves import generate_deadleave
from rstor.learning.experiments import get_training_content
from rstor.learning.experiments_definition import get_experiment_config
from rstor.properties import DEVICE
import sys
import numpy as np
from interactive_pipe import interactive_pipeline, interactive
import torch
import cv2
from pathlib import Path
MODELS_PATH = Path("scripts")/"__output"


def infer(degraded, model):
    degraded_tensor = torch.from_numpy(degraded).permute(-1, 0, 1).float().unsqueeze(0)
    model.eval()
    with torch.no_grad():
        output = model(degraded_tensor.to(DEVICE))
    output = output.squeeze().permute(1, 2, 0).cpu().numpy()
    return np.ascontiguousarray(output)


@interactive(
    k_size_x=(1, [1, 10]),
    k_size_y=(1, [1, 10])
)
def degrade(chart, k_size_x=1, k_size_y=1):
    return cv2.GaussianBlur(chart, (2*k_size_x+1, 2*k_size_y+1), 0)


@interactive(
    model_name=("vanilla", ["vanilla", "unittest", "NAFNET"])
)
def model_selector(models_dict: dict, model_name="vanilla"):
    return models_dict[model_name]


def deadleave_inference_pipeline(models_dict: dict):
    groundtruth = generate_deadleave()
    model = model_selector(models_dict)
    degraded_chart = degrade(groundtruth)
    restored_chart = infer(degraded_chart, model)
    return groundtruth, degraded_chart, restored_chart


def main(argv):
    model_dict = {}
    for exp, name in [(1000, "vanilla"), (-1, "unittest")]:
        config = get_experiment_config(exp)
        model, _, _ = get_training_content(config, training_mode=False)
        model.load_state_dict(torch.load(MODELS_PATH/f"{exp:04d}"/"best_model.pt"))
        model = model.to(DEVICE)
        model_dict[name] = model
    interactive_pipeline(gui="auto")(deadleave_inference_pipeline)(model_dict)


if __name__ == "__main__":
    main(sys.argv[1:])