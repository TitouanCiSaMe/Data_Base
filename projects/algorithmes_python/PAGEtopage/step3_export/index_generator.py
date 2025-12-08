"""
Générateur d'index et métadonnées

Génère les fichiers d'index JSON, mapping images, etc.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging

from ..models import AnnotatedPage

logger = logging.getLogger(__name__)


class IndexGenerator:
    """
    Génère les fichiers d'index et métadonnées

    Produit:
    - pages_index.json : Index de toutes les pages
    - images_mapping.txt : Correspondance page → image
    - corpus_stats.json : Statistiques du corpus
    """

    def __init__(self, output_folder: Path):
        """
        Args:
            output_folder: Dossier de sortie
        """
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def generate_all(
        self,
        pages: List[AnnotatedPage],
        page_files: Dict[str, str]
    ) -> None:
        """
        Génère tous les fichiers d'index

        Args:
            pages: Liste des pages annotées
            page_files: Mapping {folio: chemin_fichier_sortie}
        """
        self.generate_pages_index(pages, page_files)
        self.generate_images_mapping(pages, page_files)
        self.generate_corpus_stats(pages)

    def generate_pages_index(
        self,
        pages: List[AnnotatedPage],
        page_files: Dict[str, str]
    ) -> Path:
        """
        Génère l'index JSON des pages

        Args:
            pages: Liste des pages
            page_files: Mapping folio → fichier

        Returns:
            Chemin du fichier créé
        """
        index = {
            "generated_at": datetime.now().isoformat(),
            "total_pages": len(pages),
            "pages": []
        }

        for page in pages:
            meta = page.metadata
            page_entry = {
                "folio": meta.folio,
                "page_number": meta.page_number,
                "running_title": meta.running_title,
                "is_empty": page.is_empty,
                "sentence_count": len(page.sentences),
                "token_count": sum(len(s.tokens) for s in page.sentences),
                "output_file": page_files.get(meta.folio, ""),
            }

            # Ajoute les métadonnées du corpus
            page_entry.update(meta.corpus_metadata)

            index["pages"].append(page_entry)

        output_path = self.output_folder / "pages_index.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info(f"Index des pages généré: {output_path}")
        return output_path

    def generate_images_mapping(
        self,
        pages: List[AnnotatedPage],
        page_files: Dict[str, str]
    ) -> Path:
        """
        Génère le mapping images → pages

        Args:
            pages: Liste des pages
            page_files: Mapping folio → fichier

        Returns:
            Chemin du fichier créé
        """
        output_path = self.output_folder / "images_mapping.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Mapping: image_source → page_output\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("#" + "=" * 60 + "\n\n")

            for page in pages:
                folio = page.metadata.folio
                output_file = page_files.get(folio, "N/A")

                # Nom d'image (remplace .xml par .jpg/.png)
                image_name = folio.replace(".xml", ".jpg")

                f.write(f"{image_name}\t→\t{output_file}\n")

        logger.info(f"Mapping images généré: {output_path}")
        return output_path

    def generate_corpus_stats(self, pages: List[AnnotatedPage]) -> Path:
        """
        Génère les statistiques du corpus

        Args:
            pages: Liste des pages

        Returns:
            Chemin du fichier créé
        """
        total_sentences = 0
        total_tokens = 0
        pos_counts: Dict[str, int] = {}
        lemma_counts: Dict[str, int] = {}
        empty_pages = 0

        for page in pages:
            if page.is_empty:
                empty_pages += 1
                continue

            total_sentences += len(page.sentences)

            for sentence in page.sentences:
                total_tokens += len(sentence.tokens)

                for token in sentence.tokens:
                    # Compte les POS
                    pos_counts[token.pos] = pos_counts.get(token.pos, 0) + 1

                    # Compte les lemmes (top 100)
                    if token.pos != "PUNCT":
                        lemma_counts[token.lemma] = lemma_counts.get(token.lemma, 0) + 1

        # Top 100 lemmes
        top_lemmas = sorted(
            lemma_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:100]

        stats = {
            "generated_at": datetime.now().isoformat(),
            "corpus_statistics": {
                "total_pages": len(pages),
                "empty_pages": empty_pages,
                "total_sentences": total_sentences,
                "total_tokens": total_tokens,
                "avg_sentences_per_page": round(total_sentences / max(len(pages) - empty_pages, 1), 2),
                "avg_tokens_per_sentence": round(total_tokens / max(total_sentences, 1), 2),
            },
            "pos_distribution": dict(sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)),
            "top_100_lemmas": [{"lemma": l, "count": c} for l, c in top_lemmas],
        }

        output_path = self.output_folder / "corpus_stats.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"Statistiques du corpus générées: {output_path}")
        return output_path


def generate_index(
    pages: List[AnnotatedPage],
    page_files: Dict[str, str],
    output_folder: Path
) -> None:
    """
    Fonction utilitaire pour générer tous les index

    Args:
        pages: Liste des pages
        page_files: Mapping folio → fichier
        output_folder: Dossier de sortie
    """
    generator = IndexGenerator(output_folder)
    generator.generate_all(pages, page_files)
