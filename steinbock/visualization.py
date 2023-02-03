from typing import Dict, Optional, Sequence

import napari
import numpy as np


def view(
    img: np.ndarray,
    masks: Optional[Dict[str, np.ndarray]] = None,
    channel_names: Optional[Sequence[str]] = None,
    pixel_size_um: float = 1.0,
    run: bool = True,
    **viewer_kwargs,
) -> Optional[napari.Viewer]:
    viewer = napari.Viewer(**viewer_kwargs)
    viewer.axes.visible = True
    viewer.dims.axis_labels = ("y", "x")
    viewer.scale_bar.visible = True
    viewer.scale_bar.unit = "um"
    viewer.add_image(
        data=img,
        channel_axis=0,
        colormap="gray",
        name=channel_names,
        scale=(pixel_size_um, pixel_size_um),
        blending="additive",
        visible=False,
    )
    if masks is not None:
        for mask_name, mask in masks.items():
            viewer.add_labels(
                data=mask,
                name=mask_name,
                scale=(pixel_size_um, pixel_size_um),
                blending="translucent",
                visible=False,
            )
    if run:
        napari.run()
        return None
    return viewer
