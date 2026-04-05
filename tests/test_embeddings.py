from __future__ import annotations

import unittest

from casemap.embeddings import HashEmbeddingBackend, create_embedding_backend


class EmbeddingBackendTests(unittest.TestCase):
    def test_hash_backend_is_deterministic(self) -> None:
        backend = HashEmbeddingBackend(dimensions=32)
        first = backend.embed_documents(["murder manslaughter theft"])[0]
        second = backend.embed_documents(["murder manslaughter theft"])[0]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 32)

    def test_create_embedding_backend_local_hash(self) -> None:
        backend = create_embedding_backend(backend="local-hash", dimensions=48)
        self.assertEqual(backend.name, "local-hash")
        self.assertEqual(backend.dimensions, 48)


if __name__ == "__main__":
    unittest.main()
