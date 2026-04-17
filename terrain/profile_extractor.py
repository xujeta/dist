# файл: terrain/profile_extractor.py
import cv2
import numpy as np
import sknw
from shapely.geometry import LineString, Point, MultiPoint, GeometryCollection
import math
from skimage.morphology import skeletonize

def extract_contour_mask_color_from_bgr(img_bgr):
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([5, 50, 30], dtype=np.uint8)
    upper = np.array([25, 255, 230], dtype=np.uint8)
    brown_mask = cv2.inRange(img_hsv, lower, upper)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, dark_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    dark_mask_inv = cv2.bitwise_not(dark_mask)
    contours_mask = cv2.bitwise_and(brown_mask, brown_mask, mask=dark_mask_inv)
    contours_mask = cv2.morphologyEx(contours_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    contours_mask = cv2.dilate(contours_mask, None, iterations=1)
    return contours_mask

class TerrainProfileExtractor:
    def __init__(self, step=10, mode="gray"):
        self.step = step
        self.mode = mode

    def _get_line_mask(self, img_bgr):
        # Переводим в ЧБ
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        if self.mode == "gray":
            # Адаптивный порог: выделяет линии даже при плохом свете
            # 21 — размер блока (должен быть нечетным), 7 — константа вычитания
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 21, 7
            )
            
            # Убираем мелкий визуальный мусор (точки)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            return mask

    def _skeletonize(self, mask):
        binary = mask > 0
        skel = skeletonize(binary)
        return (skel * 255).astype(np.uint8)

    def _build_polylines(self, skeleton):
        graph = sknw.build_sknw(skeleton > 0)
        polylines = []
        for (s, e) in graph.edges():
            pts = graph[s][e]['pts']
            pts = [(float(p[1]), float(p[0])) for p in pts]
            if len(pts) >= 3:
                polylines.append(LineString(pts))
        return polylines

    def _extract_intersection_coords(self, geom):
        coords = []
        if geom.geom_type == 'Point':
            coords.append((geom.x, geom.y))
        elif geom.geom_type == 'MultiPoint':
            for p in geom.geoms:
                coords.append((p.x, p.y))
        elif geom.geom_type == 'GeometryCollection':
            for g in geom.geoms:
                if g.geom_type in ['Point', 'MultiPoint']:
                    coords.extend(self._extract_intersection_coords(g))
        return coords

    def extract_profile(self, img_bgr, point_a, point_b, height_a, height_b, extrema=None):
        if extrema is None:
            extrema = []
            
        if img_bgr is None:
            return {"error": "image read error"}

        line_mask = self._get_line_mask(img_bgr)
        skeleton = self._skeletonize(line_mask)
        polylines = self._build_polylines(skeleton)

        # 1. Прямая линия профиля
        profile_line = LineString([point_a, point_b])
        total_length = profile_line.length

        # 2. Ищем ВСЕ пересечения
        raw_intersections = []
        for poly in polylines:
            if profile_line.intersects(poly):
                inter = profile_line.intersection(poly)
                raw_intersections.extend(self._extract_intersection_coords(inter))

        # Превращаем в список (dist, x, y)
        inter_list = []
        for x, y in raw_intersections:
            d = profile_line.project(Point(x, y))
            inter_list.append((d, x, y))
        inter_list.sort(key=lambda x: x[0])

        # 3. Подготавливаем ключевые точки (A, B и ручные экстремумы)
        # Формат: (dist, height, type, (x, y))
        key_points = [(0.0, height_a, 'keypoint_A', point_a)]
        for ext in extrema:
            pt = Point(ext[0], ext[1])
            d = profile_line.project(pt)
            key_points.append((d, ext[2], ext[3], (ext[0], ext[1])))
        key_points.append((total_length, height_b, 'keypoint_B', point_b))
        key_points.sort(key=lambda x: x[0])

        # --- МЯГКОЕ ОБЪЕДИНЕНИЕ (Фильтрация дублей) ---
        MERGE_DIST = 10  # Порог в пикселях. Если пересечение ближе к экстремуму, удаляем его.
        
        filtered_intersections = []
        for i_dist, i_x, i_y in inter_list:
            is_redundant = False
            # Проверяем, не совпадает ли пересечение с уже имеющейся ключевой точкой
            for k_dist, _, _, _ in key_points:
                if abs(i_dist - k_dist) < MERGE_DIST:
                    is_redundant = True
                    break
            
            # Дополнительная проверка: не склеивается ли это пересечение с предыдущим добавленным
            if not is_redundant and filtered_intersections:
                if abs(i_dist - filtered_intersections[-1][0]) < MERGE_DIST:
                    is_redundant = True
            
            if not is_redundant:
                filtered_intersections.append((i_dist, i_x, i_y))

        # 4. Сборка финального профиля по сегментам между ключевыми точками
        profile_data = []
        
        for i in range(len(key_points) - 1):
            kp_start = key_points[i]
            kp_end = key_points[i+1]
            
            d_start, h_start, p_type, coords_start = kp_start
            d_end, h_end, _, _ = kp_end
            
            # Добавляем саму ключевую точку
            profile_data.append({
                'dist': d_start, 'h': h_start, 'type': p_type, 
                'x': coords_start[0], 'y': coords_start[1]
            })
            
            # Ищем отфильтрованные пересечения внутри этого сегмента
            EPS = 1e-3
            seg_ints = [item for item in filtered_intersections if d_start + EPS < item[0] < d_end - EPS]
            
            # Логика шага высоты
            if h_end > h_start: direction = 1
            elif h_end < h_start: direction = -1
            else: direction = 0
            
            # Определение начальной высоты первого пересечения в сегменте
            if direction != 0:
                if h_start % self.step == 0:
                    first_h = h_start + self.step * direction
                else:
                    first_h = (math.ceil(h_start / self.step) if direction == 1 else math.floor(h_start / self.step)) * self.step
            else:
                first_h = h_start # Если высоты ключевых точек равны (плато)

            for j, inter in enumerate(seg_ints):
                h_inter = first_h + j * self.step * direction
                profile_data.append({
                    'dist': inter[0], 'h': h_inter, 'type': 'intersection',
                    'x': inter[1], 'y': inter[2]
                })

        # Добавляем последнюю точку B
        last_kp = key_points[-1]
        profile_data.append({
            'dist': last_kp[0], 'h': last_kp[1], 'type': last_kp[2],
            'x': last_kp[3][0], 'y': last_kp[3][1]
        })

        return {
            "profile_data": profile_data,
            "intersections_count": len(filtered_intersections)
        }
