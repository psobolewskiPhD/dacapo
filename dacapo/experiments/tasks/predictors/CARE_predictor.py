from .predictor import Predictor
from dacapo.experiments import Model
from dacapo.experiments.arraytypes import IntensitiesArray
from dacapo.experiments.datasplits.datasets.arrays import NumpyArray

from funlib.geometry import Coordinate  # TODO: pip install

import numpy as np
import torch


class CAREPredictor(Predictor):
    def __init__(self, embedding_dims):
        self.embedding_dims = embedding_dims

    def create_model(self, architecture):
        # edit architecture in MODEL
        head = torch.nn.Conv3d(
            architecture.num_out_channels, self.embedding_dims, kernel_size=3
        )

        return Model(architecture, head)

    def create_target(self, gt):
        # zeros
        return NumpyArray.from_np_array(
            np.zeros((self.embedding_dims,) + gt.data.shape[-gt.dims :]),
            gt.roi,
            gt.voxel_size,
            ["c"] + gt.axes,
        )

    def create_weight(self, gt):
        # ones
        return NumpyArray.from_np_array(
            np.ones(gt.data.shape),
            gt.roi,
            gt.voxel_size,
            gt.axes,
        )

    @property
    def output_array_type(self):
        return IntensitiesArray(self.embedding_dims)
    
    def gt_region_for_roi(self, target_spec):
        if self.mask_distances:
            gt_spec = target_spec.copy()
            gt_spec.roi = gt_spec.roi.grow(
                Coordinate((self.max_distance,) * gt_spec.voxel_size.dims),
                Coordinate((self.max_distance,) * gt_spec.voxel_size.dims),
            ).snap_to_grid(gt_spec.voxel_size, mode="shrink")
        else:
            gt_spec = target_spec.copy()
        return gt_spec

    def padding(self, gt_voxel_size: Coordinate) -> Coordinate:
        return Coordinate((self.max_distance,) * gt_voxel_size.dims)


