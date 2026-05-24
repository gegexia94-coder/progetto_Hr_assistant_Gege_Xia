import re
import numpy as np

from custom_embedding import CustomEmbeddingFunction


class SemanticChunking:
    def __init__(self, breakpoint_percentile=85, buffer_size=1):
        self.embedding_function = CustomEmbeddingFunction()
        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size

    def _split_sentences(self, text):
        sentences = re.split(r"(?<=[.?!])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _combine_with_context(self, sentences):
        items = []

        for index, sentence in enumerate(sentences):
            start = max(0, index - self.buffer_size)
            end = min(len(sentences), index + self.buffer_size + 1)

            items.append({
                "sentence": sentence,
                "combined": " ".join(sentences[start:end]),
            })

        return items

    def _cosine_distance(self, vector_a, vector_b):
        a = np.array(vector_a)
        b = np.array(vector_b)

        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        return 1 - similarity

    def _calculate_distances(self, items):
        embeddings = self.embedding_function(
            [item["combined"] for item in items]
        )

        distances = []

        for index in range(len(items) - 1):
            distance = self._cosine_distance(
                embeddings[index],
                embeddings[index + 1],
            )
            distances.append(distance)

        return distances

    def chunk_text(self, text):
        sentences = self._split_sentences(text)

        if len(sentences) <= 2:
            return [text.strip()] if text.strip() else []

        items = self._combine_with_context(sentences)
        distances = self._calculate_distances(items)

        if not distances:
            return [text.strip()]

        threshold = np.percentile(distances, self.breakpoint_percentile)
        split_points = [
            index for index, distance in enumerate(distances)
            if distance > threshold
        ]

        chunks = []
        start = 0

        for point in split_points + [len(sentences) - 1]:
            chunk = " ".join(sentences[start:point + 1]).strip()

            if chunk:
                chunks.append(chunk)

            start = point + 1

        return chunks
