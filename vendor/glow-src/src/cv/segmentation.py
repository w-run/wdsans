#!/usr/bin/env python3
# -*- encoding: utf8 -*-
import numpy as np
import cv2
import numpy as _np

def binary_dilation(img, selem):
    k = _np.ones((selem[0], selem[1]), dtype=_np.uint8)
    return cv2.dilate((img * 255).astype(_np.uint8), k) > 0

def square(n):
    return (n, n)

# Find the junctions of the skeleton image
# REF: https://answers.opencv.org/question/103162/detection-of-contours-intersections/
def find_junctions(skeleton):
    """骨架分支点（邻居数 >= 3）。

    原实现用 cv2.morphologyEx(HITMISS)，在 aarch64/musl 上会 segfault，
    这里改成纯 numpy 邻居计数，语义等价且不依赖 OpenCV 形态学。
    """
    from numpy.lib.stride_tricks import sliding_window_view
    b = (skeleton > 0).astype(np.uint8)
    if not b.any():
        return np.zeros(b.shape, dtype=np.uint8)
    padded = np.pad(b, 1)
    win = sliding_window_view(padded, (3, 3))
    nb = win.sum(axis=(-1, -2)) - b
    is_branch = (nb >= 3) & (b == 1)
    return (is_branch.astype(np.uint8) * 255)


def get_skeleton_segments(
    skeleton,
    prune_length = 0,
    dilated_kernel_size = 3,
    return_junction_image = False,
    junction_dilated = False):

    """Give the skeleton segments of a binary image.

    Parameters
    ----------
    skeleton: numpy.ndarray
        A binary image of the skeleton, with '0' representing the backgroud, and
        '1' representing the object.
    prune_length: int
        Number of pixels in a smallest segment.
    dilated_kernel_size: int
        Size of the kernel to dilate at the junctions.
    return_junction_image: boolean
        Return the junction image or not.
    junction_dilated: boolean
        If the returning junction image is dilated.

    Returns
    ----------
    segments: list
        A list of skeleton segments
    junction_img: numpy.ndarray
        The image for the found junctions
    """

    junction_image = find_junctions(skeleton)
    # The image border should be all-black
    junction_image[0] = junction_image[-1] = 0
    junction_image[:,0] = junction_image[:,-1] = 0
    # Dilate the junction image
    dilated_junctions = binary_dilation(junction_image//255,
        square(dilated_kernel_size))
    # skeleton with no intersections
    intersection_eliminated = np.logical_and(
        skeleton, 1 - dilated_junctions).astype(np.uint8)
    _res = cv2.findContours(intersection_eliminated * 255,
        cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    segment_contours = _res[-2]  # opencv 4: (contours, hierarchy)
    segment_contours = [ contour[:,0,::-1] for contour in segment_contours ]
    sorted_segments = []

    for contour in segment_contours:
        contour_list = [ pt.tolist() for pt in contour ]
        # The indices of the end points of a segment
        ends = [ i
            for i, pt in enumerate(contour_list)
            if contour_list.count(pt) < 2 ]
        sorted_segments.append(contour[min(ends) : max(ends) + 1])

    # Pruning
    sorted_segments = list(filter(  
        lambda segment: cv2.arcLength(segment, closed=False) >= prune_length,
        sorted_segments))

    if return_junction_image:
        return (sorted_segments,
            dilated_junctions if junction_dilated else junction_image)
    else:
        return sorted_segments
