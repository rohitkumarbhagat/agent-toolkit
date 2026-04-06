"""
Reranker implementations for indicator search.
"""

from typing import Protocol


DEFAULT_RERANK_MODEL = "mixedbread-ai/mxbai-rerank-base-v1"


class IndicatorReranker(Protocol):
    """Reranks query-document pairs and returns one score per pair."""

    def predict(self, query_document_pairs: list[tuple[str, str]]) -> list[float]:
        """Score query-document pairs."""


class LocalCrossEncoderReranker:
    """Local cross-encoder reranker backed by sentence-transformers."""

    def __init__(self, model_name: str, batch_size: int) -> None:
        try:
            from sentence_transformers.cross_encoder import CrossEncoder
        except ImportError as exc:
            raise ImportError(
                "Install datacommons-mcp[rerank] to enable local reranking."
            ) from exc

        self._batch_size = batch_size
        self._model = CrossEncoder(model_name)

    def predict(self, query_document_pairs: list[tuple[str, str]]) -> list[float]:
        if not query_document_pairs:
            return []

        scores = self._model.predict(
            query_document_pairs, batch_size=self._batch_size
        )
        return [float(score) for score in scores]
