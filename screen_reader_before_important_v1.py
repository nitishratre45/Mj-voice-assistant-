import re
from difflib import SequenceMatcher

import pytesseract
from pytesseract import Output


class ScreenReader:
    """
    MJ Screen Reader
    Part 18+

    OCR + intelligent visible-text matching.

    Features:
        - Tesseract OCR
        - Exact matching
        - Partial matching
        - Fuzzy matching
        - Case-insensitive matching
        - OCR punctuation cleanup
        - Multi-word target matching
        - Duplicate OCR result cleanup
        - Confidence-aware selection
    """

    def __init__(self):

        self.tesseract_path = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        pytesseract.pytesseract.tesseract_cmd = (
            self.tesseract_path
        )

    # =========================================================
    # NORMALIZE
    # =========================================================

    @staticmethod
    def normalize(text):

        text = (
            str(text or "")
            .lower()
            .strip()
        )

        text = re.sub(
            r"[^a-zA-Z0-9\u0900-\u097F\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # =========================================================
    # SIMILARITY
    # =========================================================

    @staticmethod
    def similarity(a, b):

        a = ScreenReader.normalize(a)
        b = ScreenReader.normalize(b)

        if not a or not b:
            return 0.0

        if a == b:
            return 1.0

        return SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

    # =========================================================
    # READ IMAGE
    # =========================================================

    def read_image(self, image):

        if image is None:
            return []

        try:

            data = pytesseract.image_to_data(
                image,
                output_type=Output.DICT,
                config="--psm 6",
            )

            results = []

            count = len(
                data.get(
                    "text",
                    [],
                )
            )

            for i in range(count):

                raw_text = (
                    data["text"][i]
                    or ""
                )

                text = raw_text.strip()

                if not text:
                    continue

                # ---------------------------------------------
                # Confidence
                # ---------------------------------------------

                try:

                    confidence = float(
                        data["conf"][i]
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    confidence = 0.0

                if confidence < 15:
                    continue

                # ---------------------------------------------
                # Coordinates
                # ---------------------------------------------

                try:

                    x = int(
                        data["left"][i]
                    )

                    y = int(
                        data["top"][i]
                    )

                    w = int(
                        data["width"][i]
                    )

                    h = int(
                        data["height"][i]
                    )

                except (
                    TypeError,
                    ValueError,
                    KeyError,
                ):

                    continue

                if w <= 0 or h <= 0:
                    continue

                normalized = self.normalize(
                    text
                )

                if not normalized:
                    continue

                results.append(
                    {
                        "text": text,
                        "normalized": normalized,
                        "confidence": confidence,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "center_x": x + w // 2,
                        "center_y": y + h // 2,
                    }
                )

            # Remove obvious duplicate OCR boxes.
            results = self._deduplicate(
                results
            )

            return results

        except Exception as exc:

            print(
                "MJ OCR ERROR:",
                exc,
            )

            return []

    # =========================================================
    # DEDUPLICATE
    # =========================================================

    def _deduplicate(self, items):

        cleaned = []

        for item in items:

            duplicate = False

            for existing in cleaned:

                same_text = (
                    item["normalized"]
                    == existing["normalized"]
                )

                if not same_text:
                    continue

                dx = abs(
                    item["center_x"]
                    - existing["center_x"]
                )

                dy = abs(
                    item["center_y"]
                    - existing["center_y"]
                )

                if (
                    dx <= 8
                    and dy <= 8
                ):

                    duplicate = True

                    if (
                        item["confidence"]
                        >
                        existing["confidence"]
                    ):

                        existing.update(
                            item
                        )

                    break

            if not duplicate:
                cleaned.append(
                    item
                )

        return cleaned

    # =========================================================
    # READ SCREEN
    # =========================================================

    def read_screen(self, screen):

        image = screen.capture(
            save=False
        )

        return self.read_image(
            image
        )

    # =========================================================
    # SCORE MATCH
    # =========================================================

    def _match_score(
        self,
        target,
        item,
    ):

        target = self.normalize(
            target
        )

        text = self.normalize(
            item.get(
                "text",
                "",
            )
        )

        if not target or not text:
            return 0.0

        # ---------------------------------------------
        # Exact
        # ---------------------------------------------

        if text == target:
            return 100.0

        # ---------------------------------------------
        # Target contained in OCR text
        # ---------------------------------------------

        if target in text:
            return 94.0

        # ---------------------------------------------
        # OCR text contained in target
        # ---------------------------------------------

        if text in target:
            return 88.0

        # ---------------------------------------------
        # Word-level match
        # ---------------------------------------------

        target_words = target.split()
        text_words = text.split()

        if (
            len(target_words) > 1
            and
            all(
                word in text_words
                for word in target_words
            )
        ):

            return 92.0

        # ---------------------------------------------
        # Fuzzy similarity
        # ---------------------------------------------

        similarity = self.similarity(
            target,
            text,
        )

        score = similarity * 85.0

        # OCR confidence contributes slightly.
        confidence = float(
            item.get(
                "confidence",
                0,
            )
        )

        confidence_bonus = min(
            10.0,
            max(
                0.0,
                confidence / 10.0,
            ),
        )

        score += confidence_bonus

        return min(
            93.0,
            score,
        )

    # =========================================================
    # FIND TEXT
    # =========================================================

    def find_text(
        self,
        screen,
        target,
    ):

        target = self.normalize(
            target
        )

        if not target:
            return None

        items = self.read_screen(
            screen
        )

        if not items:
            return None

        # =====================================================
        # EXACT MATCH
        # =====================================================

        exact_matches = []

        for item in items:

            if (
                item["normalized"]
                == target
            ):

                exact_matches.append(
                    item
                )

        if exact_matches:

            best = max(
                exact_matches,
                key=lambda x:
                x.get(
                    "confidence",
                    0,
                ),
            )

            return best

        # =====================================================
        # PARTIAL MATCH
        # =====================================================

        partial_matches = []

        for item in items:

            text = item[
                "normalized"
            ]

            if (
                target in text
                or
                text in target
            ):

                partial_matches.append(
                    item
                )

        if partial_matches:

            best = max(
                partial_matches,
                key=lambda x:
                self._match_score(
                    target,
                    x,
                ),
            )

            return best

        # =====================================================
        # FUZZY MATCH
        # =====================================================

        candidates = []

        for item in items:

            score = self._match_score(
                target,
                item,
            )

            if score >= 60.0:

                candidates.append(
                    (
                        score,
                        item,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda pair:
            pair[0],
            reverse=True,
        )

        best_score, best_item = (
            candidates[0]
        )

        # ---------------------------------------------
        # Require stronger confidence for fuzzy match.
        # ---------------------------------------------

        if best_score < 68.0:

            return None

        result = dict(
            best_item
        )

        result[
            "match_score"
        ] = best_score

        return result