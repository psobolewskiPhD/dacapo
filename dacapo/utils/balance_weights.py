from dacapo.experiments.datasplits.datasets.arrays import NumpyArray

import numpy as np

import itertools


def balance_weights(
    labels, num_classes, masks=list(), slab=None, clipmin=0.05, clipmax=0.95
):

    label_data = labels[labels.roi]

    assert len(np.unique(label_data)) <= num_classes, (
        "Found more unique labels than classes in %s." % labels
    )
    assert 0 <= np.min(label_data) < num_classes, (
        "Labels %s are not in [0, num_classes)." % labels
    )
    assert 0 <= np.max(label_data) < num_classes, (
        "Labels %s are not in [0, num_classes)." % labels
    )

    # initialize error scale with 1s
    error_scale = np.ones(label_data.shape, dtype=np.float32)

    # set error_scale to 0 in masked-out areas
    for mask in masks:
        error_scale *= mask[mask.roi]

    if slab is None:
        slab = error_scale.shape
    else:
        # slab with -1 replaced by shape
        slab = tuple(m if s == -1 else s for m, s in zip(error_scale.shape, slab))

    slab_ranges = (range(0, m, s) for m, s in zip(error_scale.shape, slab))

    for start in itertools.product(*slab_ranges):
        slices = tuple(slice(start[d], start[d] + slab[d]) for d in range(len(slab)))
        # operate on slab independently
        scale_slab = error_scale[slices]
        labels_slab = label_data[slices]
        # in the masked-in area, compute the fraction of per-class samples
        masked_in = scale_slab.sum()
        classes, counts = np.unique(
            labels_slab[np.nonzero(scale_slab)], return_counts=True
        )
        fracs = (
            counts.astype(float) / masked_in if masked_in > 0 else np.zeros(counts.size)
        )
        if clipmin is not None or clipmax is not None:
            np.clip(fracs, clipmin, clipmax, fracs)

        # compute the class weights
        if len(classes) == 1:
            total_frac = 1.0
        else:
            total_frac = 1.0
        w_sparse = total_frac / float(num_classes) / fracs
        w = np.zeros(num_classes)
        w[classes] = w_sparse

        # if labels_slab are uint64 take gets very upset
        labels_slab = labels_slab.astype(np.int64)
        # scale_slab the masked-in scale_slab with the class weights
        scale_slab *= np.take(w, labels_slab)

    weights = NumpyArray.from_np_array(
        error_scale, labels.roi, labels.voxel_size, labels.axes
    )
    return weights
