"""
Servicio de detección usando OpenCV y algoritmos ORB/AKAZE (mejorado).
Mantiene compatibilidad con tu API actual y agrega:
- Preprocesado (LAB+CLAHE) y mapa de bordes para más keypoints.
- Backend intercambiable ORB/AKAZE.
- Banco de referencias (múltiples imágenes).
- Segmentación de candidatos por saturación (HSV) + filtros geométricos.
- Verificación de forma con Hu moments.
- Validación de homografía por IoU con ROI.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, List, TYPE_CHECKING

from ..config.settings import ORBConfig, DrawingConfig
from ..utils.logging import setup_logger
from ..utils.colors import rgb_to_bgr

if TYPE_CHECKING:
    import cv2 as _cv2_type  # noqa: F401
    import numpy as _np_type  # noqa: F401


@dataclass
class DetectionResult:
    frame_with_overlay: Any
    mask: Optional[Any]
    matches_found: int
    has_detection: bool
    homography: Optional[Any] = None


@dataclass
class ReferenceData:
    image: Any
    gray: Any
    keypoints: List[Any]
    descriptors: Any
    height: int
    width: int
    hu: Optional[Any] = None
    edge: Optional[Any] = None
    name: str = ""


class OpenCVService:
    """Servicio mejorado para detección usando OpenCV."""

    def __init__(
        self,
        orb_config: ORBConfig,
        drawing_config: DrawingConfig,
        feature_backend: str = "AKAZE",
    ):
        self.orb_config = orb_config
        self.drawing_config = drawing_config
        self.logger = setup_logger(__name__)
        self.feature_backend = (feature_backend or "ORB").upper()

        # Inicialización diferida
        self._feat: Optional[Any] = None
        self._norm: Optional[int] = None
        self._bf_matcher: Optional[Any] = None

        # Soporta referencia única (compat) o banco múltiple
        self._reference_data: Optional[ReferenceData] = None
        self._reference_bank: List[ReferenceData] = []

    # ---------- Backend de keypoints ----------
    @property
    def feat(self) -> Any:
        if self._feat is None:
            import cv2 as _cv2
            if self.feature_backend == "AKAZE":
                self._feat = _cv2.AKAZE_create(threshold=1e-3)
                self._norm = _cv2.NORM_HAMMING
            else:
                self._feat = _cv2.ORB_create(
                    nfeatures=max(1500, self.orb_config.n_features),
                    scaleFactor=1.1,
                    nlevels=12,
                    edgeThreshold=15,
                    WTA_K=2,
                )
                self._norm = _cv2.NORM_HAMMING
        return self._feat

    @property
    def bf_matcher(self) -> Any:
        if self._bf_matcher is None:
            import cv2 as _cv2
            self._bf_matcher = _cv2.BFMatcher(
                self._norm or _cv2.NORM_HAMMING, crossCheck=False
            )
        return self._bf_matcher

    # ---------- Carga de referencias ----------
    def load_reference(self, ref_path: str) -> None:
        """Compat: carga una sola referencia (igual que antes), ahora con Hu y edge."""
        ref = self._load_single_reference(ref_path)
        self._reference_data = ref
        self._reference_bank = [ref]
        self.logger.info(
            "Referencia cargada: %s (%d kp)", ref_path, len(ref.keypoints)
        )

    def load_references(self, paths: List[str]) -> None:
        """Nuevo: carga múltiples referencias para mayor diversidad."""
        bank: List[ReferenceData] = []
        for p in paths:
            try:
                bank.append(self._load_single_reference(p))
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.logger.warning("No se pudo cargar referencia %s: %s", p, e)
        if not bank:
            raise RuntimeError("No se pudo cargar ninguna referencia")
        self._reference_bank = bank
        self._reference_data = bank[0]
        self.logger.info("%d referencias cargadas.", len(bank))

    def _load_single_reference(self, ref_path: str) -> ReferenceData:
        import cv2 as _cv2

        if not Path(ref_path).exists():
            raise FileNotFoundError(f"Imagen de referencia no encontrada: {ref_path}")

        img = _cv2.imread(ref_path)
        if img is None:
            raise RuntimeError(f"No se pudo leer la imagen de referencia: {ref_path}")

        gray = _cv2.cvtColor(img, _cv2.COLOR_BGR2GRAY)
        kp, des = self.feat.detectAndCompute(gray, None)
        if des is None or len(kp) < 8:
            raise RuntimeError(
                "Muy pocos puntos clave en la referencia. Usa una imagen con más textura/detalle."
            )

        hu = self._compute_hu_moments(gray)
        edge = self._make_edge_map(img)
        h, w = gray.shape[:2]
        return ReferenceData(
            image=img,
            gray=gray,
            keypoints=kp,
            descriptors=des,
            height=h,
            width=w,
            hu=hu,
            edge=edge,
            name=Path(ref_path).name,
        )

    # ---------- Preprocesado y candidatos ----------
    def _preprocess_for_keypoints(self, frame_bgr):
        import cv2 as _cv2
        # LAB + CLAHE
        lab = _cv2.cvtColor(frame_bgr, _cv2.COLOR_BGR2LAB)
        l_ch, a_ch, b_ch = _cv2.split(lab)
        clahe = _cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_eq = clahe.apply(l_ch)
        labc = _cv2.merge([l_eq, a_ch, b_ch])
        gray = _cv2.cvtColor(labc, _cv2.COLOR_LAB2BGR)
        gray = _cv2.cvtColor(gray, _cv2.COLOR_BGR2GRAY)
        # Edges
        edges = _cv2.Canny(gray, 60, 180)
        edges = _cv2.dilate(
            edges, _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (3, 3)), 1
        )
        # Mezcla
        comb = _cv2.addWeighted(edges, 0.7, gray, 0.3, 0)
        return comb, edges, gray

    def _find_candidates(self, frame_bgr):
        """Segmenta regiones con alta saturación y filtra por geometría (forma de penca)."""
        import cv2 as _cv2

        hsv = _cv2.cvtColor(frame_bgr, _cv2.COLOR_BGR2HSV)
        _h, s, _v = _cv2.split(hsv)  # noqa: F841
        sat_mask = _cv2.inRange(s, 90, 255)  # neón/saturado
        sat_mask = _cv2.morphologyEx(
            sat_mask,
            _cv2.MORPH_CLOSE,
            _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (5, 5)),
            2,
        )
        cnts, _ = _cv2.findContours(
            sat_mask, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE
        )
        rois = []
        for c in cnts:
            area = _cv2.contourArea(c)
            if area < 800:
                continue
            x, y, w, h = _cv2.boundingRect(c)
            ar = w / float(h)
            peri = _cv2.arcLength(c, True)
            if peri == 0:
                continue
            circularity = 4.0 * 3.14159265 * area / (peri * peri)
            if 0.5 <= ar <= 2.0 and 0.55 <= circularity <= 0.95:
                rois.append((x, y, w, h, c))
        return rois

    def _compute_hu_moments(self, gray):
        import cv2 as _cv2
        edges = _cv2.Canny(gray, 60, 180)
        cnts, _ = _cv2.findContours(
            edges, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE
        )
        if not cnts:
            return None
        c = max(cnts, key=_cv2.contourArea)
        return _cv2.HuMoments(_cv2.moments(c)).flatten()

    def _make_edge_map(self, bgr):
        import cv2 as _cv2
        g = _cv2.cvtColor(bgr, _cv2.COLOR_BGR2GRAY)
        e = _cv2.Canny(g, 60, 180)
        return e

    # ---------- Detección ----------
    def detect_in_frame(self, frame: Any) -> DetectionResult:
        import cv2 as _cv2

        if not self._reference_bank:
            raise RuntimeError("No se ha cargado la(s) imagen(es) de referencia")

        output_frame = frame.copy()
        mask = None
        matches_found = 0
        has_detection = False
        homography = None

        preproc, _edges, _gray = self._preprocess_for_keypoints(frame)  # noqa: F841
        candidates = self._find_candidates(frame)

        # Fallback: si no hay candidatos, intenta global
        if not candidates:
            kp_frame, des_frame = self.feat.detectAndCompute(preproc, None)
            if des_frame is None or not kp_frame or len(kp_frame) < 8:
                self._draw_few_keypoints(output_frame)
                return DetectionResult(output_frame, None, 0, False, None)

            for ref in self._reference_bank:
                gm, has_detection, homography, mask = self._try_match_and_draw(
                    ref, kp_frame, des_frame, output_frame, None
                )
                matches_found = max(matches_found, gm)
                if has_detection:
                    break

            if not has_detection:
                self._draw_insufficient_matches(output_frame)
            else:
                self._draw_matches_info(output_frame, matches_found)

            return DetectionResult(
                output_frame, mask, matches_found, has_detection, homography
            )

        # Con candidatos (recomendado)
        best = {"gm": 0, "H": None, "mask": None}
        for (x, y, w, h, _cnt) in candidates:  # noqa: F841
            roi = frame[y : y + h, x : x + w]
            preproc_roi, _, _ = self._preprocess_for_keypoints(roi)
            kp_roi, des_roi = self.feat.detectAndCompute(preproc_roi, None)
            if des_roi is None or not kp_roi or len(kp_roi) < 8:
                continue

            # Comparación de forma rápida vía Hu moments
            hu_roi = self._compute_hu_moments(
                _cv2.cvtColor(roi, _cv2.COLOR_BGR2GRAY)
            )

            for ref in self._reference_bank:
                if ref.hu is not None and hu_roi is not None:
                    import numpy as _np
                    d = _np.linalg.norm(
                        _np.log10(_np.abs(ref.hu + 1e-12))
                        - _np.log10(_np.abs(hu_roi + 1e-12))
                    )
                    if d > 6.0:  # umbral conservador; ajústalo según datos
                        continue

                gm, ok, H, m = self._try_match_and_draw(
                    ref, kp_roi, des_roi, output_frame, (x, y, w, h)
                )
                if ok and gm > best["gm"]:
                    best.update({"gm": gm, "H": H, "mask": m})

        if best["H"] is not None:
            has_detection = True
            homography = best["H"]
            mask = best["mask"]
            matches_found = best["gm"]
            self._draw_matches_info(output_frame, matches_found)
        else:
            self._draw_insufficient_matches(output_frame)

        return DetectionResult(
            output_frame, mask, matches_found, has_detection, homography
        )

    # ---------- Matching + Homografía + Validación ----------
    def _try_match_and_draw(self, ref: ReferenceData, kp_frame, des_frame, output_frame, roi_box):
        import cv2 as _cv2
        import numpy as _np

        matches = self.bf_matcher.knnMatch(ref.descriptors, des_frame, k=2)
        good = []
        for pair in matches:
            if len(pair) == 2:
                m, n = pair
                if m.distance < self.orb_config.ratio_threshold * n.distance:
                    good.append(m)

        # min_matches adaptativo si hay ROI
        min_matches = self.orb_config.min_matches
        if roi_box is not None:
            _x, _y, w, h = roi_box  # noqa: F841
            peri = 2 * (w + h)
            min_matches = max(12, min_matches, int(0.02 * peri))

        if len(good) < min_matches:
            return len(good), False, None, None

        src_pts = _np.float32([ref.keypoints[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = _np.float32([kp_frame[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        H, _inliers = _cv2.findHomography(src_pts, dst_pts, _cv2.RANSAC, self.orb_config.ransac_threshold)
        if H is None:
            return len(good), False, None, None

        # Esquinas de la referencia → sistema del destino (ROI o global)
        corners = _np.float32([[0, 0], [ref.width, 0], [ref.width, ref.height], [0, ref.height]]).reshape(-1, 1, 2)
        proj = _cv2.perspectiveTransform(corners, H)
        proj_int = _np.int32(proj)

        # Si es ROI, desplazamos a coords globales y validamos IoU con ROI
        if roi_box is not None:
            x, y, w, h = roi_box
            proj_int[:, 0, 0] += x
            proj_int[:, 0, 1] += y

            iou_ok = self._iou_poly_rect_ok(proj_int, (x, y, w, h), threshold=0.3)
            if not iou_ok:
                return len(good), False, None, None

        # Crear máscara y dibujar
        mask = _np.zeros(output_frame.shape[:2], dtype=_np.uint8)
        _cv2.fillPoly(mask, [proj_int], 255)

        self._draw_overlay_and_border(output_frame, proj_int)
        self._draw_label(output_frame, proj_int)

        return len(good), True, H, mask

    def _iou_poly_rect_ok(self, poly, rect, threshold=0.3):
        """Calcula IoU aproximado entre polígono proyectado y rect ROI."""
        import cv2 as _cv2
        import numpy as _np

        x, y, w, h = rect
        H = max(y + h + 10, 1)
        W = max(x + w + 10, 1)
        m1 = _np.zeros((H, W), _np.uint8)
        m2 = _np.zeros((H, W), _np.uint8)
        _cv2.fillPoly(m1, [poly], 255)
        _cv2.rectangle(m2, (x, y), (x + w, y + h), 255, -1)
        inter = _cv2.countNonZero(_cv2.bitwise_and(m1, m2))
        union = _cv2.countNonZero(_cv2.bitwise_or(m1, m2))
        if union == 0:
            return False
        iou = inter / float(union)
        return iou >= threshold

    # ---------- Dibujo (sin cambios de contrato) ----------
    def _draw_overlay_and_border(self, output_frame: Any, corners: Any) -> None:
        import cv2 as _cv2
        fill_bgr = rgb_to_bgr(self.drawing_config.fill_color)
        border_bgr = rgb_to_bgr(self.drawing_config.border_color)
        overlay = output_frame.copy()
        _cv2.fillPoly(overlay, [corners], fill_bgr)
        _cv2.addWeighted(
            overlay,
            self.drawing_config.fill_alpha,
            output_frame,
            1.0 - self.drawing_config.fill_alpha,
            0.0,
            output_frame,
        )
        _cv2.polylines(
            output_frame,
            [corners],
            True,
            border_bgr,
            self.drawing_config.border_thickness,
            _cv2.LINE_AA,
        )

    def _draw_label(self, output_frame: Any, corners: Any) -> None:
        import cv2 as _cv2
        x0, y0 = int(corners[0, 0, 0]), int(corners[0, 0, 1])
        border_bgr = rgb_to_bgr(self.drawing_config.border_color)
        _cv2.putText(
            output_frame,
            "NOPAL DETECTADO",
            (x0, max(20, y0 - 10)),
            _cv2.FONT_HERSHEY_SIMPLEX,
            self.drawing_config.font_scale,
            border_bgr,
            self.drawing_config.font_thickness,
        )

    def _draw_matches_info(self, output_frame: Any, matches_found: int) -> None:
        import cv2 as _cv2
        border_bgr = rgb_to_bgr(self.drawing_config.border_color)
        _cv2.putText(
            output_frame,
            f"Matches: {matches_found}",
            (10, 28),
            _cv2.FONT_HERSHEY_SIMPLEX,
            self.drawing_config.font_scale,
            border_bgr,
            self.drawing_config.font_thickness,
        )

    def _draw_insufficient_matches(self, output_frame: Any) -> None:
        import cv2 as _cv2
        _cv2.putText(
            output_frame,
            f"Matches insuficientes (min: {self.orb_config.min_matches})",
            (10, 58),
            _cv2.FONT_HERSHEY_SIMPLEX,
            self.drawing_config.font_scale * 0.8,
            (0, 255, 255),
            self.drawing_config.font_thickness,
        )

    def _draw_no_homography(self, output_frame: Any) -> None:
        import cv2 as _cv2
        _cv2.putText(
            output_frame,
            "Sin homografia valida",
            (10, 58),
            _cv2.FONT_HERSHEY_SIMPLEX,
            self.drawing_config.font_scale * 0.8,
            (0, 255, 255),
            self.drawing_config.font_thickness,
        )

    def _draw_few_keypoints(self, output_frame: Any) -> None:
        import cv2 as _cv2
        _cv2.putText(
            output_frame,
            "Pocos puntos clave en frame",
            (10, 28),
            _cv2.FONT_HERSHEY_SIMPLEX,
            self.drawing_config.font_scale,
            (0, 255, 255),
            self.drawing_config.font_thickness,
        )
