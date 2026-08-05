import unittest
import os
import json
import database
from seo_analyzer import run_seo_audit
from report_generator import generate_pdf_report, generate_csv_report
from app import app


class TestSEOScope(unittest.TestCase):

    def setUp(self):
        database.init_db()
        self.app = app.test_client()
        self.app.testing = True

    def test_01_database_init(self):
        """Test database initialization and table schema setup."""
        conn = database.get_db()
        self.assertIsNotNone(conn)
        if hasattr(conn, 'close'):
            conn.close()

    def test_02_seo_audit_engine(self):
        """Test SEO audit run on sample-blog.local demo site."""
        audit_res = run_seo_audit('sample-blog.local')
        
        self.assertIn('scores', audit_res)
        scores = audit_res['scores']
        
        # Expect high score for optimized blog sample
        self.assertGreaterEqual(scores['overall_score'], 80)
        self.assertEqual(scores['rating_grade'], 'Excellent')
        
        # Check sub-modules
        self.assertEqual(audit_res['metadata']['title']['status'], 'optimal')
        self.assertEqual(audit_res['headings']['breakdown']['h1_count'], 1)
        self.assertEqual(audit_res['images']['missing_alt_count'], 0)
        self.assertTrue(audit_res['technical']['is_https'])

    def test_03_poor_seo_audit_engine(self):
        """Test SEO audit run on poor-seo-demo.local."""
        audit_res = run_seo_audit('poor-seo-demo.local')
        scores = audit_res['scores']
        
        # Expect lower score for missing title/description/H1
        self.assertLess(scores['overall_score'], 65)
        self.assertEqual(audit_res['headings']['breakdown']['h1_count'], 0)
        self.assertGreater(audit_res['images']['missing_alt_count'], 0)

    def test_04_pdf_csv_generation(self):
        """Test PDF and CSV generator output."""
        audit_res = run_seo_audit('sample-blog.local')
        
        pdf_bytes = generate_pdf_report(audit_res)
        self.assertTrue(isinstance(pdf_bytes, bytes))
        self.assertGreater(len(pdf_bytes), 1000)

        csv_str = generate_csv_report(audit_res)
        self.assertTrue(isinstance(csv_str, str))
        self.assertIn('SEOScope Audit Report Export', csv_str)

    def test_05_flask_api_scan(self):
        """Test Flask REST API POST /api/scan endpoint."""
        response = self.app.post('/api/scan', json={'url': 'sample-blog.local'})
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('report_id', data)
        report_id = data['report_id']

        # Test PDF download endpoint
        pdf_res = self.app.get(f'/api/reports/{report_id}/pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.mimetype, 'application/pdf')

        # Test CSV download endpoint
        csv_res = self.app.get(f'/api/reports/{report_id}/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, 'text/csv')


if __name__ == '__main__':
    unittest.main()
