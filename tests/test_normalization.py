"""Unit tests for string normalization helpers."""

import unittest

from deezer_playlist_generator.normalization import normalize, similarity


class NormalizeTests(unittest.TestCase):
    def test_accented_characters(self) -> None:
        self.assertEqual(normalize("Björk"), "bjork")
        self.assertEqual(normalize("Beyoncé"), "beyonce")
        self.assertEqual(normalize("Sigur Rós"), "sigurros")
        self.assertEqual(normalize("Motörhead"), "motorhead")

    def test_case_folding(self) -> None:
        self.assertEqual(normalize("BJÖRK"), "bjork")
        self.assertEqual(normalize("björk"), "bjork")
        self.assertEqual(normalize("BeYoNcÉ"), "beyonce")

    def test_punctuation_and_whitespace(self) -> None:
        self.assertEqual(normalize("AC/DC"), "acdc")
        self.assertEqual(normalize("Guns N' Roses"), "gunsnroses")
        self.assertEqual(normalize("  Sigur   Rós  "), "sigurros")
        self.assertEqual(normalize("Motörhead!"), "motorhead")

    def test_empty_string(self) -> None:
        self.assertEqual(normalize(""), "")


class SimilarityTests(unittest.TestCase):
    def test_identical_after_diacritic_removal(self) -> None:
        self.assertEqual(similarity("Björk", "Bjork"), 1.0)
        self.assertEqual(similarity("Beyoncé", "beyonce"), 1.0)
        self.assertEqual(similarity("Motörhead", "Motorhead"), 1.0)

    def test_empty_strings(self) -> None:
        self.assertEqual(similarity("", ""), 1.0)
        self.assertEqual(similarity("Björk", ""), 0.0)


if __name__ == "__main__":
    unittest.main()
