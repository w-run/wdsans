#!/usr/bin/env python3
# -*- encoding: utf8 -*-
import numpy as np
from rasterize import rasterize
from segmentation import get_skeleton_segments
import cv2
# skimage 在 musl/alpine 上装不了，改用 OpenCV 等价实现

class RefFinder(object):

  def __init__(self, glyph, scale_factor):
    self.glyph = glyph
    self.glyph_img = rasterize(glyph, scale=scale_factor) > 128
    h, w = self.glyph_img.shape
    self.scale_factor = scale_factor
    # Labled by connectivity
    _n, self.labeled = cv2.connectedComponents(
        self.glyph_img.astype(np.uint8))
    n_labels = _n - 1
    # medial_axis 等价：距离变换 + thinning
    dist = cv2.distanceTransform(
        self.glyph_img.astype(np.uint8), cv2.DIST_L2, 5)
    axis = cv2.ximgproc.thinning(
        (self.glyph_img * 255).astype(np.uint8)) > 0
    # Estimated stroke width
    self.stroke_width = np.average(dist[axis]) * 2
    # Smoothed image
    smooth = cv2.GaussianBlur(
        self.glyph_img.astype(np.float32), (0, 0), 8 * scale_factor) > 0.6
    # Skeleton image
    _sk = cv2.ximgproc.thinning(
        (smooth * 255).astype(np.uint8)) > 0
    skel = np.logical_and(_sk, dist >= self.stroke_width * 0.3)
    # Skeleton segments
    skel_segments = get_skeleton_segments(skel, 
      prune_length=self.stroke_width * 0.25)
    # Reference skeleton points
    self.skel_pts = (np.array(
      [ pt[::-1] for segment in skel_segments for pt in segment ])
      /scale_factor).astype(int)
    # Skeleton points by their belonging region labels
    self.skel_pts_by_label = [ [] for _ in range(n_labels) ]
    for pt in self.skel_pts:
      ptx = int(pt[0] * scale_factor + 0.5)
      pty = int(pt[1] * scale_factor + 0.5)
      ptx = w-1 if ptx >= w else 0 if ptx < 0 else ptx
      pty = h-1 if pty >= h else 0 if pty < 0 else pty
      pt_label = self.labeled[pty, ptx]
      self.skel_pts_by_label[pt_label-1].append(pt)

  def find_ref(self, x, y):
    result = np.array([ x, y ])
    h, w = self.labeled.shape
    scale = self.scale_factor
    xi = int(x * scale + 0.5); yi = int(y * scale + 0.5)
    if yi-2 < 0 or yi+3 >= h or xi-2 < 0 or xi+3 >= w: return result
    neighbors = list(filter(
      lambda m: m != 0, self.labeled[yi-2:yi+3,xi-2:xi+3].reshape((25))))
    if len(neighbors) == 0: return result
    # Region label of the query coordinate
    pt_label = np.argmax(np.bincount(neighbors))
    # Find the closest skeleton point of the region
    nearest_dist = 1000**2*2
    for pt in self.skel_pts_by_label[pt_label-1]:
      dist = (pt[0] - x)**2 + (pt[1] - y)**2
      if dist < nearest_dist:
        result = pt; nearest_dist = dist
    return result
