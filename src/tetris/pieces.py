"""Tetris blok tanımları.

Bu dosya farklı Tetris parçalarının koordinat şekillerini saklar.
"""

from dataclasses import dataclass
from typing import List

@dataclass
class Piece:
    """Bir Tetris parçası."""
    shape: List[List[int]]
    color_index: int

# Farklı parça tanımları
PIECES = [
    Piece(shape=[[1, 1, 1, 1]], color_index=0),  # I parçası - Ateş
    Piece(shape=[[1, 1], [1, 1]], color_index=1),  # O parçası - Su
    Piece(shape=[[0, 1, 0], [1, 1, 1]], color_index=2),  # T parçası - Toprak
    Piece(shape=[[1, 1, 0], [0, 1, 1]], color_index=3),  # S parçası - Hava
]
