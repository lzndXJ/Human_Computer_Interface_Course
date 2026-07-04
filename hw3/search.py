from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
PROMPT_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "fresh",
    "fruit",
    "grocery",
    "image",
    "in",
    "item",
    "of",
    "photo",
    "picture",
    "product",
    "store",
    "the",
}


@dataclass(frozen=True)
class SearchResult:
    path: str
    score: float


def list_images(image_dir: str | Path) -> list[Path]:
    root = Path(image_dir)
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def normalize_label_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def query_terms(value: str) -> list[str]:
    normalized = normalize_label_text(value)
    if not normalized:
        return []

    terms = [normalized]
    terms.extend(
        token
        for token in normalized.split()
        if len(token) >= 3 and token not in PROMPT_STOPWORDS
    )
    return list(dict.fromkeys(terms))


def prompt_variants(query: str) -> list[str]:
    query = query.strip()
    return [
        query,
        f"a photo of {query}",
        f"a grocery store product photo of {query}",
        f"fresh {query}",
    ]


def load_clip(model_name: str, device: str | None = None):
    os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")

    import torch
    from transformers import CLIPModel, CLIPProcessor

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
        model = CLIPModel.from_pretrained(
            model_name,
            local_files_only=True,
            use_safetensors=False,
        ).to(device)
    except OSError:
        processor = CLIPProcessor.from_pretrained(model_name)
        model = CLIPModel.from_pretrained(model_name, use_safetensors=False).to(device)
    model.eval()
    return model, processor, device


def encode_images(
    image_paths: list[Path],
    model,
    processor,
    device: str,
    batch_size: int = 16,
) -> np.ndarray:
    import torch

    embeddings: list[np.ndarray] = []
    for start in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[start : start + batch_size]
        images = [Image.open(path).convert("RGB") for path in batch_paths]
        inputs = processor(images=images, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        if hasattr(features, "pooler_output"):
            features = features.pooler_output
        features = features.detach().cpu().numpy().astype("float32")
        embeddings.append(features)

    if not embeddings:
        return np.empty((0, 512), dtype="float32")
    return l2_normalize(np.vstack(embeddings)).astype("float32")


def encode_text(text: str, model, processor, device: str) -> np.ndarray:
    return encode_texts([text], model, processor, device)[0]


def encode_texts(texts: list[str], model, processor, device: str) -> np.ndarray:
    import torch

    inputs = processor(
        text=texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
    ).to(device)
    with torch.no_grad():
        features = model.get_text_features(**inputs)
    if hasattr(features, "pooler_output"):
        features = features.pooler_output
    return l2_normalize(features.detach().cpu().numpy().astype("float32"))


def encode_text_query(text: str, model, processor, device: str) -> np.ndarray:
    vectors = encode_texts(prompt_variants(text), model, processor, device)
    return l2_normalize(vectors.mean(axis=0, keepdims=True).astype("float32"))[0]


def label_from_path(path: str) -> str:
    parts = Path(path).parts
    markers = {"train", "test", "val", "iconic-images-and-descriptions"}
    for index, part in enumerate(parts):
        if part in markers and index + 1 < len(parts):
            return normalize_label_text(Path(path).parent.name)

    stem = Path(path).stem.replace("_Iconic", "")
    return normalize_label_text(stem)


def encode_query_image(image, model, processor, device: str) -> np.ndarray:
    import torch

    if not isinstance(image, Image.Image):
        image = Image.open(image)
    image = image.convert("RGB")
    inputs = processor(images=[image], return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    if hasattr(features, "pooler_output"):
        features = features.pooler_output
    return l2_normalize(features.detach().cpu().numpy().astype("float32"))[0]


class LocalImageSearchIndex:
    def __init__(
        self,
        index_dir: str | Path = "index",
        model_name: str = "openai/clip-vit-base-patch32",
        device: str | None = None,
    ) -> None:
        self.index_dir = Path(index_dir)
        self.embeddings_path = self.index_dir / "image_embeddings.npy"
        self.paths_path = self.index_dir / "image_paths.json"
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None
        self.image_paths: list[str] = []
        self.path_texts: list[str] = []
        self.path_labels: list[str] = []
        self.label_names: list[str] = []
        self.label_vectors: np.ndarray | None = None
        self.embeddings = np.empty((0, 512), dtype="float32")

    def load(self) -> None:
        if not self.embeddings_path.exists() or not self.paths_path.exists():
            raise FileNotFoundError(
                "Image index not found. Put images in data/images, then run: "
                "python build_index.py"
            )

        self.embeddings = np.load(self.embeddings_path).astype("float32")
        self.embeddings = l2_normalize(self.embeddings)
        self.image_paths = json.loads(self.paths_path.read_text(encoding="utf-8"))
        self.path_texts = [normalize_label_text(path) for path in self.image_paths]
        self.path_labels = [label_from_path(path) for path in self.image_paths]
        self.label_names = sorted({label for label in self.path_labels if label})

    def ensure_model(self) -> None:
        if self.model is None or self.processor is None:
            self.model, self.processor, self.device = load_clip(
                self.model_name, self.device
            )

    def search_by_text(self, text: str, top_k: int = 8) -> list[SearchResult]:
        query = text.strip()
        if not query:
            return []
        self.ensure_model()
        vector = encode_text_query(query, self.model, self.processor, self.device)
        return self._search(vector, top_k, text_hint=query)

    def search_by_image(
        self,
        image,
        top_k: int = 8,
        text_hint: str = "",
        image_weight: float = 0.7,
        text_weight: float = 0.3,
    ) -> list[SearchResult]:
        if image is None:
            return []
        self.ensure_model()
        vector = encode_query_image(image, self.model, self.processor, self.device)
        hint = text_hint.strip()
        if hint:
            text_vector = encode_text_query(hint, self.model, self.processor, self.device)
            vector = l2_normalize(
                (image_weight * vector + text_weight * text_vector).reshape(1, -1)
            )[0]
            return self._search(vector, top_k, text_hint=hint)

        auto_hint = self._infer_neighbor_label_hint(vector)
        return self._search(vector, top_k, text_hint=auto_hint, label_boost=0.08)

    def _ensure_label_vectors(self) -> None:
        if self.label_vectors is not None:
            return
        if not self.label_names:
            self.label_vectors = np.empty((0, self.embeddings.shape[1]), dtype="float32")
            return
        self.ensure_model()
        prompts = [
            f"a grocery store product photo of {label}"
            for label in self.label_names
        ]
        self.label_vectors = encode_texts(
            prompts,
            self.model,
            self.processor,
            self.device,
        )

    def _infer_neighbor_label_hint(self, query_vector: np.ndarray) -> str:
        if self.embeddings.size == 0 or not self.path_labels:
            return ""
        base_scores = self.embeddings @ query_vector
        best_index = int(np.argmax(base_scores))
        if base_scores[best_index] < 0.25:
            return ""
        return self.path_labels[best_index]

    def _label_match_scores(self, text_hint: str) -> np.ndarray:
        terms = query_terms(text_hint)
        if not terms:
            return np.zeros(len(self.image_paths), dtype="float32")

        scores = np.zeros(len(self.image_paths), dtype="float32")
        for index, path_text in enumerate(self.path_texts):
            if terms[0] and terms[0] in path_text:
                scores[index] = 1.0
                continue

            matches = sum(1 for term in terms[1:] if term in path_text)
            if matches:
                scores[index] = matches / max(1, len(terms) - 1)
        return scores

    def _search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        text_hint: str = "",
        label_boost: float = 0.16,
    ) -> list[SearchResult]:
        if self.embeddings.size == 0:
            return []
        top_k = max(1, min(int(top_k), len(self.image_paths)))
        scores = self.embeddings @ query_vector
        if text_hint.strip():
            scores = scores + label_boost * self._label_match_scores(text_hint)
        order = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(path=self.image_paths[index], score=float(scores[index]))
            for index in order
        ]


def build_local_index(
    image_dir: str | Path = "data/images",
    index_dir: str | Path = "index",
    model_name: str = "openai/clip-vit-base-patch32",
    batch_size: int = 16,
    device: str | None = None,
) -> tuple[int, Path]:
    image_paths = list_images(image_dir)
    if not image_paths:
        raise FileNotFoundError(
            f"No images found in {Path(image_dir).resolve()}. "
            "Add .jpg/.png/.webp files before building the index."
        )

    model, processor, resolved_device = load_clip(model_name, device)
    embeddings = encode_images(image_paths, model, processor, resolved_device, batch_size)

    index_root = Path(index_dir)
    index_root.mkdir(parents=True, exist_ok=True)
    np.save(index_root / "image_embeddings.npy", embeddings)
    (index_root / "image_paths.json").write_text(
        json.dumps([str(path) for path in image_paths], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metadata = {
        "model_name": model_name,
        "image_dir": str(Path(image_dir)),
        "image_count": len(image_paths),
        "embedding_dim": int(embeddings.shape[1]),
    }
    (index_root / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(image_paths), index_root


def result_gallery_items(
    results: list[SearchResult],
) -> list[tuple[str, str]]:
    return [
        (result.path, f"score: {result.score:.3f}")
        for result in results
    ]


def format_result_table(results: list[SearchResult]) -> list[list[str | float]]:
    return [
        [index + 1, result.path, round(result.score, 4)]
        for index, result in enumerate(results)
    ]


SearchMode = Literal["Text", "Image"]
