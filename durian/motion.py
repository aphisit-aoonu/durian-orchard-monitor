"""Camera motion between frames, so fruit positions can be compared after the camera moves."""
import cv2
import numpy as np

WORK_WIDTH = 640
MIN_INLIERS = 25


class CameraMotion:
    """Tracks a 3x3 transform from the current frame to a fixed 'world' frame (the first frame).

    Uses ORB features on the background; RANSAC ignores the few points on moving fruit or people.
    """

    def __init__(self):
        self.orb = cv2.ORB_create(1500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.prev = None
        self.to_world = np.eye(3)
        self.lost = False

    def update(self, frame_bgr) -> np.ndarray:
        h, w = frame_bgr.shape[:2]
        s = WORK_WIDTH / w
        gray = cv2.cvtColor(cv2.resize(frame_bgr, (WORK_WIDTH, round(h * s))), cv2.COLOR_BGR2GRAY)
        kp, des = self.orb.detectAndCompute(gray, None)
        self.lost = False
        if self.prev is not None and des is not None and self.prev[1] is not None:
            m = self._estimate(self.prev[0], self.prev[1], kp, des)
            if m is None:
                self.lost = True
            else:
                scale = np.diag([1 / s, 1 / s, 1.0])
                prev_to_cur = scale @ np.vstack([m, [0, 0, 1]]) @ np.linalg.inv(scale)
                self.to_world = self.to_world @ np.linalg.inv(prev_to_cur)
        self.prev = (kp, des)
        return self.to_world

    def _estimate(self, kp1, des1, kp2, des2):
        matches = self.matcher.match(des1, des2)
        if len(matches) < MIN_INLIERS:
            return None
        a = np.float32([kp1[m.queryIdx].pt for m in matches])
        b = np.float32([kp2[m.trainIdx].pt for m in matches])
        m, inliers = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=3.0)
        if m is None or inliers is None or inliers.sum() < MIN_INLIERS:
            return None
        return m


def apply(transform: np.ndarray, box) -> list[float]:
    """Map a box through a 3x3 transform; returns the bounding box of the mapped corners."""
    x1, y1, x2, y2 = box
    pts = np.array([[x1, y1, 1], [x2, y1, 1], [x1, y2, 1], [x2, y2, 1]], dtype=float) @ transform.T
    pts = pts[:, :2] / pts[:, 2:3]
    return [float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())]
