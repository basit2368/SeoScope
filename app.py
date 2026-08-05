import os
import json
from flask import Flask, render_template, request, jsonify, session, send_file, Response
from werkzeug.security import generate_password_hash, check_password_hash

import database
from seo_analyzer import run_seo_audit
from report_generator import generate_pdf_report, generate_csv_report

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'seoscope-super-secret-key-2026-production')

# Initialize DB on application startup
db_type = database.init_db()
print(f"[*] SEOScope backend initialized with active DB: {db_type}")


# --- HTML Frontend Route ---
@app.route('/')
def index():
    return render_template('index.html')


# --- REST API Endpoints ---

@app.route('/api/scan', methods=['POST'])
def scan_website():
    """Triggers automated SEO audit scan for submitted website URL."""
    payload = request.get_json() or {}
    target_url = payload.get('url', '').strip()

    if not target_url:
        return jsonify({'success': False, 'error': 'Website URL is required'}), 400

    try:
        # Run automated audit
        audit_result = run_seo_audit(target_url)

        # Extract summary scores
        user_id = session.get('user_id')
        seo_score = audit_result['scores']['overall_score']
        cat_scores = audit_result['scores']['category_scores']

        # Save report into database
        report_id = database.save_audit_report(
            user_id=user_id,
            website_url=audit_result['target_url'],
            seo_score=seo_score,
            technical_score=cat_scores.get('technical', 0),
            content_score=cat_scores.get('content', 0),
            images_score=cat_scores.get('images', 0),
            links_score=cat_scores.get('links', 0),
            audit_data=audit_result
        )

        audit_result['report_id'] = report_id

        return jsonify({
            'success': True,
            'report_id': report_id,
            'data': audit_result
        })
    except Exception as e:
        app.logger.error(f"Scan error for {target_url}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f"Scan failed: {str(e)}"}), 500


@app.route('/api/reports', methods=['GET'])
def get_reports_history():
    """Fetches audit reports history."""
    user_id = session.get('user_id')
    reports = database.get_all_audit_reports(limit=30, user_id=user_id)
    return jsonify({'success': True, 'reports': reports})


@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    """Retrieves full details of specific audit report."""
    report = database.get_audit_report_by_id(report_id)
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    return jsonify({'success': True, 'report': report})


@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Deletes an audit report."""
    success = database.delete_audit_report(report_id)
    if success:
        return jsonify({'success': True, 'message': 'Report deleted successfully'})
    return jsonify({'success': False, 'error': 'Failed to delete report'}), 500


@app.route('/api/reports/<int:report_id>/pdf', methods=['GET'])
def download_pdf(report_id):
    """Downloads audit report as PDF."""
    report = database.get_audit_report_by_id(report_id)
    if not report or 'audit_data' not in report:
        return jsonify({'error': 'Report not found'}), 404

    audit_data = report['audit_data']
    pdf_bytes = generate_pdf_report(audit_data)

    safe_filename = f"SEOScope_Report_{report_id}.pdf"
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'}
    )


@app.route('/api/reports/<int:report_id>/csv', methods=['GET'])
def download_csv(report_id):
    """Downloads audit report as CSV."""
    report = database.get_audit_report_by_id(report_id)
    if not report or 'audit_data' not in report:
        return jsonify({'error': 'Report not found'}), 404

    audit_data = report['audit_data']
    csv_string = generate_csv_report(audit_data)

    safe_filename = f"SEOScope_Report_{report_id}.csv"
    return Response(
        csv_string,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{safe_filename}"'}
    )


# --- User Authentication Routes ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    payload = request.get_json() or {}
    name = payload.get('name', '').strip()
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')

    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'Name, email, and password are required'}), 400

    existing = database.get_user_by_email(email)
    if existing:
        return jsonify({'success': False, 'error': 'Email is already registered'}), 400

    pwd_hash = generate_password_hash(password)
    user_id = database.create_user(name, email, pwd_hash)

    session['user_id'] = user_id
    session['user_name'] = name

    return jsonify({
        'success': True,
        'user': {'id': user_id, 'name': name, 'email': email}
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    payload = request.get_json() or {}
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')

    user = database.get_user_by_email(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']

    return jsonify({
        'success': True,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
    })


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False})

    user = database.get_user_by_id(user_id)
    if user:
        return jsonify({'authenticated': True, 'user': user})
    return jsonify({'authenticated': False})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
