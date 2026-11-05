
"""
LIA - Data Loader & Preprocessing Module

Supports:
1. PDF, TXT, Markdown files.
2. GeoJSON files with feature properties and geometry metadata.
3. Excel files with multiple worksheets.
4. SHA-256 content hashing for deduplication.
5. Text chunking with overlapping windows.
"""

import asyncio
import json
import logging
from pathlib import Path

import pymupdf
from app.core.security import get_file_hash

logger = logging.getLogger("uvicorn.error")

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".md",
    ".geojson", ".json",
    ".xlsx", ".xls"
}


class DataPreprocessor:
    """Handles file loading, preprocessing, hashing and text chunking."""

    @staticmethod
    def compute_hash(path: str | Path) -> str:
        file_path = Path(path)
        file_bytes = file_path.read_bytes()
        return get_file_hash(file_bytes)

    @staticmethod
    def _build_file_metadata(path: Path, file_bytes: bytes) -> dict:
        return {
            "file_path": str(path),
            "filename": path.name,
            "file_hash": get_file_hash(file_bytes),
            "file_size_bytes": len(file_bytes)
        }

    @staticmethod
    def load_txt(path: str | Path) -> dict:
        path = Path(path)
        file_bytes = path.read_bytes()
        text = file_bytes.decode("utf-8", errors="replace")

        return {
            **DataPreprocessor._build_file_metadata(path, file_bytes),
            "pages": [
                {"page_number": 1, "text": text}
            ] if text.strip() else []
        }

    @staticmethod
    def load_pdf(path: str | Path) -> dict:
        path = Path(path)
        file_bytes = path.read_bytes()

        pages = []

        with pymupdf.open(str(path)) as pdf:
            for page in pdf:
                page_text = page.get_text()

                if page_text and page_text.strip():
                    pages.append({
                        "page_number": page.number + 1,
                        "text": page_text
                    })

        return {
            **DataPreprocessor._build_file_metadata(path, file_bytes),
            "pages": pages
        }

    @staticmethod
    def _get_coordinate_bounds(coordinates) -> dict | None:
        """Extracts bounding coordinates from nested GeoJSON coordinates."""

        points = []

        def collect(value):
            if (
                isinstance(value, (list, tuple))
                and len(value) >= 2
                and isinstance(value[0], (int, float))
                and isinstance(value[1], (int, float))
            ):
                points.append((value[0], value[1]))

            elif isinstance(value, (list, tuple)):
                for item in value:
                    collect(item)

        collect(coordinates)

        if not points:
            return None

        longitudes = [point[0] for point in points]
        latitudes = [point[1] for point in points]

        return {
            "min_longitude": min(longitudes),
            "min_latitude": min(latitudes),
            "max_longitude": max(longitudes),
            "max_latitude": max(latitudes)
        }

    @staticmethod
    def load_geojson(path: str | Path) -> dict:
        """
        Loads GeoJSON features.

        Extracts properties and geometry metadata for RAG.
        Preserves original geometry separately for spatial operations.
        """

        path = Path(path)
        file_bytes = path.read_bytes()

        try:
            geojson = json.loads(file_bytes.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid GeoJSON file: {exc}") from exc

        geojson_type = geojson.get("type")

        if geojson_type == "FeatureCollection":
            features = geojson.get("features", [])

        elif geojson_type == "Feature":
            features = [geojson]

        else:
            raise ValueError(
                "GeoJSON must contain a FeatureCollection or Feature."
            )

        pages = []
        structured_features = []

        for index, feature in enumerate(features, start=1):

            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                logger.warning("Skipping invalid GeoJSON feature %s", index)
                continue

            properties = feature.get("properties") or {}
            geometry = feature.get("geometry")

            geometry_type = (
                geometry.get("type")
                if isinstance(geometry, dict)
                else "Unknown"
            )

            coordinates = (
                geometry.get("coordinates")
                if isinstance(geometry, dict)
                else None
            )

            bounds = (
                DataPreprocessor._get_coordinate_bounds(coordinates)
                if coordinates is not None
                else None
            )

            feature_id = feature.get("id", index)

            # Convert feature properties into searchable text.
            property_text = "\n".join(
                f"{key}: {value}"
                for key, value in properties.items()
                if value is not None
            )

            text_parts = [
                f"Feature ID: {feature_id}",
                f"Geometry Type: {geometry_type}",
                f"Properties:\n{property_text}"
            ]

            if bounds:
                text_parts.append(
                    "Geographic Bounds: "
                    f"Longitude {bounds['min_longitude']} to "
                    f"{bounds['max_longitude']}, "
                    f"Latitude {bounds['min_latitude']} to "
                    f"{bounds['max_latitude']}"
                )

            feature_text = "\n".join(text_parts)

            pages.append({
                "page_number": index,
                "text": feature_text,
                "feature_id": feature_id,
                "geometry_type": geometry_type
            })

            # Preserve complete geometry and properties separately.
            structured_features.append({
                "feature_id": feature_id,
                "properties": properties,
                "geometry": geometry,
                "geometry_type": geometry_type,
                "bounds": bounds
            })

        return {
            **DataPreprocessor._build_file_metadata(path, file_bytes),
            "pages": pages,
            "features": structured_features,
            "total_features": len(structured_features)
        }

    @staticmethod
    def load_excel(path: str | Path) -> dict:
        """
        Loads Excel workbooks, including multiple worksheets.
        Converts each worksheet row into searchable text.
        """

        import pandas as pd

        path = Path(path)
        file_bytes = path.read_bytes()

        try:
            workbook = pd.read_excel(
                path,
                sheet_name=None,
                dtype=str,
                keep_default_na=False
            )
        except Exception as exc:
            raise ValueError(f"Excel loading failed: {exc}") from exc

        pages = []

        for sheet_number, (sheet_name, dataframe) in enumerate(
            workbook.items(), start=1
        ):

            for row_index, row in dataframe.iterrows():

                row_data = [
                    f"{column}: {value}"
                    for column, value in row.items()
                    if str(value).strip()
                ]

                if not row_data:
                    continue

                text = (
                    f"Worksheet: {sheet_name}\n"
                    f"Row: {row_index + 2}\n"
                    + "\n".join(row_data)
                )

                pages.append({
                    "page_number": sheet_number,
                    "sheet_name": sheet_name,
                    "text": text
                })

        return {
            **DataPreprocessor._build_file_metadata(path, file_bytes),
            "pages": pages,
            "total_sheets": len(workbook)
        }

    @staticmethod
    def load_file(path: str | Path) -> dict | None:
        """Selects the appropriate loader based on file extension."""

        extension = Path(path).suffix.lower()

        if extension in (".txt", ".md"):
            return DataPreprocessor.load_txt(path)

        if extension == ".pdf":
            return DataPreprocessor.load_pdf(path)

        if extension in (".geojson", ".json"):
            return DataPreprocessor.load_geojson(path)

        if extension in (".xlsx", ".xls"):
            return DataPreprocessor.load_excel(path)

        return None

    @staticmethod
    def chunk_text(
        pages: list[dict],
        chunk_size: int = 300,
        overlap: int = 50
    ) -> list[dict]:

        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError(
                "chunk_size must be positive and overlap must be "
                "between 0 and chunk_size - 1."
            )

        chunks = []
        chunk_index = 0
        step = chunk_size - overlap

        for page in pages:
            page_number = page["page_number"]
            words = page["text"].split()

            if not words:
                continue

            for start in range(0, len(words), step):
                chunk_words = words[start:start + chunk_size]

                chunk = {
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "text": " ".join(chunk_words)
                }

                # Preserve source metadata for retrieval and citations.
                for key in ("sheet_name", "feature_id", "geometry_type"):
                    if key in page:
                        chunk[key] = page[key]

                chunks.append(chunk)
                chunk_index += 1

                if start + chunk_size >= len(words):
                    break

        return chunks

    @staticmethod
    def list_files(folder_path: str | Path) -> list[Path]:
        """Lists supported files in the uploads directory."""

        folder = Path(folder_path)

        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created uploads folder at: {folder.resolve()}")
            return []

        return sorted(
            path for path in folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    @staticmethod
    def _process_file(path: str | Path) -> dict:
        """Synchronous file processing helper."""

        content = DataPreprocessor.load_file(path)

        if content is None:
            raise ValueError(f"Unsupported file type: {path}")

        chunks = DataPreprocessor.chunk_text(content["pages"])

        content["chunks"] = chunks
        content["total_chunks"] = len(chunks)

        return content

    @staticmethod
    async def process_file(path: str | Path) -> dict:
        """Processes files asynchronously without blocking the event loop."""

        return await asyncio.to_thread(
            DataPreprocessor._process_file, path
        )


# Singleton instance
data_processor = DataPreprocessor()
