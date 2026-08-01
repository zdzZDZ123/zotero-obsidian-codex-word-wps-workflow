from __future__ import annotations

import base64
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "submission_formatter.py"
SPEC = importlib.util.spec_from_file_location("submission_formatter", MODULE_PATH)
assert SPEC and SPEC.loader
formatter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(formatter)


class FormatterUnitTests(unittest.TestCase):
    def test_custom_profile_reports_invalid_alignment_clearly(self) -> None:
        profile = formatter.yaml_load(SKILL_ROOT / "assets" / "profiles" / "generic-double-blind.yaml")
        profile["styles"]["normal"]["alignment"] = "justified"
        with self.assertRaisesRegex(formatter.FormatterError, "alignment must be left, center, right, or justify"):
            formatter.validate_profile(profile)

    def test_semantic_manifest_and_evidence_gate(self) -> None:
        text = "# Result\n\nEvidence [@smith2024].\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
        manifest = formatter.semantic_manifest(text)
        self.assertEqual(manifest["citation_keys"], ["smith2024"])
        self.assertEqual(manifest["heading_count"], 1)
        self.assertEqual(manifest["table_count"], 1)
        self.assertEqual(formatter.scan_refusal_markers(text), [])
        blocked = text + "\n[UNVERIFIED CITATION — NO ORIGINAL]\n"
        self.assertEqual(formatter.scan_refusal_markers(blocked)[0]["kind"], "unverified_original")

    def test_template_distillation_is_read_only_and_usable_as_reference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pubfmt-test-") as name:
            root = Path(name)
            template = root / "template.docx"
            document = formatter.Document()
            document.add_heading("Template", level=1)
            document.save(template)
            before = formatter.sha256_file(template)
            contract = formatter.distill_template(template, root / "contract", render=False)
            self.assertEqual(formatter.sha256_file(template), before)
            self.assertEqual(contract["reference"]["sha256"], before)
            self.assertEqual(contract["mode"], "style_reference")
            self.assertEqual(contract["unresolved"], [])

    def test_visual_finalization_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pubfmt-test-") as name:
            run = Path(name)
            page = run / "page-1.png"
            page.write_bytes(b"synthetic-page")
            manifest_path = run / "run-manifest.json"
            formatter.json_dump({
                "status": "qa_pending_visual_inspection",
                "desktop_copy_requested": False,
                "variants": {
                    "anonymized": {
                        "libreoffice_render": {"status": "passed", "pages": [str(page)]},
                        "editor_render": {"status": "not_applicable"},
                    }
                },
            }, manifest_path)
            with self.assertRaises(formatter.FormatterError):
                formatter.finalize_visual_qa(manifest_path, reviewer="Codex", confirm_every_page=False)
            report = formatter.finalize_visual_qa(manifest_path, reviewer="Codex", confirm_every_page=True)
            self.assertEqual(report["status"], "qa_passed")


class FormatterEndToEndTests(unittest.TestCase):
    def test_uploaded_template_is_authoritative_and_privacy_sanitized(self) -> None:
        environment = formatter.detect_environment()
        if not all(environment[name]["available"] for name in ("pandoc", "libreoffice", "pdftoppm")):
            self.skipTest("Pandoc, LibreOffice, and pdftoppm are required for the template test")
        with tempfile.TemporaryDirectory(prefix="pubfmt-template-e2e-") as name:
            project = Path(name)
            (project / "profiles").mkdir()
            (project / "templates-local").mkdir()
            shutil.copy2(SKILL_ROOT / "assets" / "profiles" / "generic-double-blind.yaml", project / "profiles" / "safe.yaml")
            reference = project / "templates-local" / "uploaded-reference.docx"
            document = formatter.Document()
            section = document.sections[0]
            section.page_width, section.page_height = formatter.Cm(21), formatter.Cm(29.7)
            section.top_margin = formatter.Cm(1.7)
            section.bottom_margin = formatter.Cm(2.1)
            section.left_margin = formatter.Cm(2.3)
            section.right_margin = formatter.Cm(1.9)
            normal = document.styles["Normal"]
            normal.font.name = "Calibri"
            normal.font.size = formatter.Pt(10.5)
            normal.paragraph_format.line_spacing = 1.15
            heading = document.styles["Heading 1"]
            heading.font.name = "Calibri"
            heading.font.size = formatter.Pt(15)
            heading.font.bold = True
            heading.font.color.rgb = formatter.RGBColor(0x1F, 0x4E, 0x79)
            document.sections[0].header.paragraphs[0].text = "PRIVATE SOURCE AUTHOR"
            document.add_heading("Uploaded format sample", level=1)
            document.add_paragraph("Reference prose must never be copied.")
            document.save(reference)
            before = formatter.sha256_file(reference)
            contract = formatter.distill_template(reference, project / "templates-local" / "contract", render=False)
            self.assertEqual(formatter.sha256_file(reference), before)
            self.assertEqual(contract["unresolved"], [])
            (project / "manuscript.md").write_text(
                "---\ntitle: User manuscript\n---\n\n# Methods\n\nOnly user content may appear.\n",
                encoding="utf-8",
            )
            (project / "submission.yaml").write_text(
                "schema_version: 1\nmanuscript: manuscript.md\n"
                "journal_profile: profiles/safe.yaml\n"
                "template: templates-local/uploaded-reference.docx\n"
                "template_contract: templates-local/contract/template-contract.json\n"
                "template_mode: template_authoritative\neditor: none\nvariants: [anonymized]\n"
                "outputs: [docx, pdf]\noutput_root: submission-output\n",
                encoding="utf-8",
            )
            result = formatter.format_submission(project / "submission.yaml", editor_override="none")
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            fidelity = manifest["variants"]["anonymized"]["template_fidelity"]
            self.assertTrue(fidelity["passed"])
            output = Path(result["run_dir"]) / "anonymized" / "manuscript-anonymized.docx"
            output_doc = formatter.Document(output)
            output_text = "\n".join(paragraph.text for paragraph in output_doc.paragraphs)
            header_text = "\n".join(paragraph.text for paragraph in output_doc.sections[0].header.paragraphs)
            self.assertNotIn("Reference prose", output_text)
            self.assertNotIn("PRIVATE SOURCE AUTHOR", header_text)
            self.assertIn("Anonymous manuscript", header_text)
            self.assertAlmostEqual(output_doc.sections[0].top_margin / 360000, 1.7, places=2)
            self.assertEqual(output_doc.styles["Normal"].font.name, "Calibri")
            self.assertEqual(output_doc.styles["Heading 1"].font.size.pt, 15)

    def test_citation_to_docx_pdf_and_rendered_pages(self) -> None:
        environment = formatter.detect_environment()
        if not all(environment[name]["available"] for name in ("pandoc", "libreoffice", "pdftoppm")):
            self.skipTest("Pandoc, LibreOffice, and pdftoppm are required for the end-to-end test")
        with tempfile.TemporaryDirectory(prefix="pubfmt-e2e-") as name:
            project = Path(name)
            (project / "profiles").mkdir()
            (project / "assets").mkdir()
            shutil.copy2(SKILL_ROOT / "assets" / "profiles" / "generic-double-blind.yaml", project / "profiles" / "generic.yaml")
            shutil.copy2(SKILL_ROOT / "assets" / "profiles" / "ijns-local-baseline.yaml", project / "profiles" / "ijns.yaml")
            # Original synthetic 1x1 PNG; no third-party asset is used.
            (project / "assets" / "figure.png").write_bytes(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ))
            (project / "manuscript.md").write_text(
                "---\ntitle: Synthetic nursing manuscript\nauthor: Private Test Author\n---\n\n"
                "# Abstract\n\nA synthetic result [@smith2024].\n\n"
                "# Methods\n\n| Variable | Value |\n|---|---|\n| Sample | 10 |\n\n"
                "![Synthetic figure](assets/figure.png)\n\n"
                "# References\n\n::: {#refs}\n:::\n",
                encoding="utf-8",
            )
            (project / "references.json").write_text(json.dumps([{
                "id": "smith2024", "type": "article-journal", "title": "Synthetic study",
                "author": [{"family": "Smith", "given": "A"}], "issued": {"date-parts": [[2024]]},
                "container-title": "Test Journal", "volume": "1", "page": "1-2",
            }]), encoding="utf-8")
            (project / "submission.yaml").write_text(
                "schema_version: 1\nmanuscript: manuscript.md\nbibliography: references.json\n"
                "journal_profile: profiles/generic.yaml\neditor: none\nvariants: [anonymized]\n"
                "outputs: [docx, pdf]\noutput_root: submission-output\nblind_terms: [Private Test Author]\n",
                encoding="utf-8",
            )
            result = formatter.format_submission(project / "submission.yaml", editor_override="none")
            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "qa_pending_visual_inspection")
            self.assertEqual(manifest["source_semantics"]["citation_keys"], ["smith2024"])
            self.assertEqual(manifest["variants"]["anonymized"]["libreoffice_render"]["status"], "passed")
            roles = {item["role"] for item in manifest["files"]}
            self.assertIn("core_anonymized", roles)
            self.assertIn("core_pdf_anonymized", roles)

            first_core = Path(result["run_dir"]) / "anonymized" / "manuscript-anonymized.docx"
            (project / "submission.yaml").write_text(
                "schema_version: 1\nmanuscript: manuscript.md\nbibliography: references.json\n"
                "journal_profile: profiles/ijns.yaml\neditor: none\nvariants: [anonymized]\n"
                "outputs: [docx, pdf]\noutput_root: submission-output-ijns\nblind_terms: [Private Test Author]\n",
                encoding="utf-8",
            )
            switched = formatter.format_submission(project / "submission.yaml", editor_override="none")
            second_manifest = json.loads(Path(switched["manifest"]).read_text(encoding="utf-8"))
            second_core = Path(switched["run_dir"]) / "anonymized" / "manuscript-anonymized.docx"
            self.assertEqual(manifest["source_semantics"], second_manifest["source_semantics"])
            first_doc = formatter.Document(first_core)
            second_doc = formatter.Document(second_core)
            self.assertEqual([p.text for p in first_doc.paragraphs], [p.text for p in second_doc.paragraphs])
            self.assertEqual(
                [[[cell.text for cell in row.cells] for row in table.rows] for table in first_doc.tables],
                [[[cell.text for cell in row.cells] for row in table.rows] for table in second_doc.tables],
            )
            self.assertEqual(len(first_doc.inline_shapes), len(second_doc.inline_shapes))


if __name__ == "__main__":
    unittest.main()
