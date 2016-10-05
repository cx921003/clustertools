"""Visualization tools independent of OpenCV and available headless."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def apply_colormap(image, vmin=None, vmax=None, cmap='viridis'):
    """Apply a matplotlib colormap to an image."""
    image = image.astype("float64")
    # Normalization.
    imin, imax = np.min(image), np.max(image)
    if vmin is not None:
        imin = float(vmin)
    if vmax is not None:
        imax = float(vmax)
    image -= imin
    image /= (imax - imin)
    # Visualization.
    cmap_ = plt.get_cmap(cmap)
    vis = cmap_(image, bytes=True)
    return vis