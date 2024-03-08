from typing import Tuple, Optional
import numpy as np
import cv2


from rstor.synthetic_data.color_sampler import sample_rgb_values


def dead_leaves_chart(size: Tuple[int, int] = (100, 100),
                      number_of_circles: int = -1,
                      background_color: Optional[Tuple[float, float, float]] = (0.5, 0.5, 0.5),
                      colored: Optional[bool] = True,
                      radius_min: Optional[int] = -1,
                      radius_max: Optional[int] = -1,
                      radius_alpha: Optional[int] = 3,
                      seed: int = None,
                      reverse: Optional[bool] = True) -> np.ndarray:
    """
    Generation of a dead leaves chart by splatting circles on top of each other.

    Args:
        size (Tuple[int, int], optional): size of the generated chart. Defaults to (100, 100).
        number_of_circles (int, optional): number of circles to generate.
        If negative, it is computed based on the size. Defaults to -1.
        background_color (Optional[Tuple[float, float, float]], optional):
        background color of the chart. Defaults to gray (0.5, 0.5, 0.5).
        colored (Optional[bool], optional): Whether to generate colored circles. Defaults to True.
        radius_min (Optional[int], optional): minimum radius of the circles. Defaults to -1. (=> 1)
        radius_max (Optional[int], optional): maximum radius of the circles. Defaults to -1. (=> 2000)
        radius_alpha (Optional[int], optional): standard deviation of the radius of the circles.
        If negative, it is calculated based on the size. Defaults to -1.
        seed (int, optional): seed for the random number generator. Defaults to None
        reverse: (Optional[bool], optional): View circles from the back view
        by reversing order. Defaults to True.
        WARNING: This option is extremely slow on GPU.

    Returns:
        np.ndarray: generated dead leaves chart as a NumPy array.
    """
    rng = np.random.default_rng(np.random.SeedSequence(seed))

    if number_of_circles < 0:
        number_of_circles = 30 * max(size)
    if radius_min < 0.:
        radius_min = 1.
    if radius_max < 0.:
        radius_max = 2000.

    # Pick random circle centers and radii
    center_x = rng.integers(0, size[1], size=number_of_circles)
    center_y = rng.integers(0, size[0], size=number_of_circles)

    # Sample from a power law distribution for the p(radius=r) = (r.clip(radius_min, radius_max))^(-alpha)

    radius = rng.uniform(
        low=radius_max ** (1 - radius_alpha),
        high=radius_min ** (1 - radius_alpha),
        size=number_of_circles
    )
    # Using the change of variables formula for random variables.
    radius = radius ** (-1/(radius_alpha - 1))
    radius = radius.round().astype(int)

    # Pick random colors
    if colored:
        color = sample_rgb_values(number_of_circles, seed=rng.integers(0, 1e10)).astype(float)
    else:
        color = rng.uniform(0.25, 0.75, size=(number_of_circles, 1))
        color = np.concatenate((color, color, color), axis=1)

    if reverse:
        chart = np.zeros((size[0], size[1], 3), dtype=np.float32)
        buffer = np.zeros_like(chart)
        is_not_covered_mask = np.ones((*chart.shape[:2], 1))
        for i in range(number_of_circles):
            cv2.circle(buffer, (center_x[i], center_y[i]), radius[i], color[i], -1)
            chart += buffer * is_not_covered_mask
            is_not_covered_mask = cv2.circle(is_not_covered_mask, (center_x[i], center_y[i]), radius[i], 0, -1)

            if not np.any(is_not_covered_mask):
                break

        chart += np.multiply(background_color, np.ones((size[0], size[1], 3), dtype=np.float32)) * is_not_covered_mask
    else:
        chart = np.multiply(background_color, np.ones((size[0], size[1], 3), dtype=np.float32))
        for i in range(number_of_circles):
            # circle is inplace
            cv2.circle(chart, (center_x[i], center_y[i]), radius[i], color[i], -1)

    chart = chart.clip(0, 1)

    if not colored:
        chart = chart[:, :, 0, None]  # return shape [h, w, 1] in gray mode
    return chart
