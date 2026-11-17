"""Project Atlas: Flask API and compiled React web shell.

AWS infrastructure injects non-secret configuration and the ARN of an RDS-managed
secret. Credentials never enter source control, GitHub Actions, or browser code.
"""
import json
import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import boto3
import psycopg
from flask import Flask, abort, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'web' / 'dist'

application = Flask(__name__, static_folder=None)
app = application
application.config.update(JSON_SORT_KEYS=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('atlas')
logger.setLevel(logging.INFO)

if os.getenv('APP_LOG_GROUP'):
    try:
        import watchtower
        handler = watchtower.CloudWatchLogHandler(
            log_group_name=os.environ['APP_LOG_GROUP'],
            log_stream_name=f"web-{os.getenv('HOSTNAME', 'instance')}",
            create_log_group=False,
        )
        logger.addHandler(handler)
    except Exception:
        logger.exception('Could not start CloudWatch event handler')


@lru_cache(maxsize=1)
def db_credentials():
    arn = os.getenv('DB_SECRET_ARN')
    if arn:
        secret = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION_NAME'))
        value = json.loads(secret.get_secret_value(SecretId=arn)['SecretString'])
        return value['username'], value['password']
    # Local integration testing only. Do not set plaintext DB_PASSWORD in Elastic Beanstalk.
    return os.getenv('DB_USER', 'atlasadmin'), os.getenv('DB_PASSWORD', '')


def connection():
    user, password = db_credentials()
    if not password:
        raise RuntimeError('Database credentials were not configured')
    return psycopg.connect(
        host=os.environ.get('DB_HOST', 'localhost'), port=5432,
        dbname=os.environ.get('DB_NAME', 'atlasdb'),
        user=user, password=password, connect_timeout=3,
        sslmode='verify-full' if os.getenv('DB_CA_BUNDLE') else 'require',
        **({'sslrootcert': os.environ['DB_CA_BUNDLE']} if os.getenv('DB_CA_BUNDLE') else {}),
    )


def catalog():
    # In a larger application use a dedicated schema migration job (e.g. Alembic).
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS catalog_item (
                slug VARCHAR(48) PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                detail TEXT NOT NULL
            )''')
            cur.executemany('''INSERT INTO catalog_item (slug, title, detail)
                VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING''', [
                ('availability', 'Availability by design', 'Private application instances across two zones'),
                ('storage', 'Private image delivery', 'CloudFront signs requests to an S3 origin'),
                ('insight', 'Useful operational signals', 'Requests stream to Kinesis and CSV in S3'),
            ])
            cur.execute('SELECT slug, title, detail FROM catalog_item ORDER BY slug')
            return [dict(zip(('slug', 'title', 'detail'), row)) for row in cur.fetchall()]


@application.before_request
def start_request_clock():
    request._atlas_started = time.perf_counter()
    request._atlas_request_id = request.headers.get('X-Request-Id', '')[:64] or str(uuid4())


@application.after_request
def add_headers_and_log(response):
    duration_ms = round((time.perf_counter() - request._atlas_started) * 1000, 2)
    response.headers['X-Request-Id'] = request._atlas_request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if request.path.startswith('/assets/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif request.path.startswith('/api/') or request.path == '/':
        response.headers['Cache-Control'] = 'no-store'
    event = {
        'event_type': 'http_request',
        'method': request.method,
        'route': request.path[:256],
        'status': response.status_code,
        'latency_ms': duration_ms,
        'request_id': request._atlas_request_id,
    }
    # No tokens, secret values, request bodies, or client IP addresses are logged.
    logger.info(json.dumps(event, separators=(',', ':')))
    return response


@application.get('/health')
def health():
    # Keep the load-balancer liveness probe independent of RDS failures.
    return jsonify({'status': 'healthy', 'service': 'atlas-web'})


@application.get('/api/status')
def api_status():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
        return jsonify({'api': 'healthy', 'database': 'reachable'})
    except Exception:
        logger.warning('Database readiness check failed', exc_info=False)
        return jsonify({'api': 'degraded', 'database': 'unavailable'}), 503


@application.get('/api/catalog')
def api_catalog():
    try:
        return jsonify({'items': catalog()})
    except Exception:
        logger.warning('Catalog fetch failed', exc_info=False)
        return jsonify({'error': 'Catalog temporarily unavailable'}), 503


@application.get('/')
@application.get('/<path:requested_path>')
def frontend(requested_path=''):
    if requested_path.startswith('api/') or requested_path == 'health':
        abort(404)
    candidate = (DIST / requested_path).resolve()
    if requested_path and candidate.is_file() and DIST.resolve() in candidate.parents:
        return send_from_directory(str(DIST), requested_path)
    if '.' in Path(requested_path).name:
        abort(404)
    if not (DIST / 'index.html').is_file():
        return jsonify({'notice': 'Frontend has not been built. Run npm run build.'}), 503
    return send_from_directory(str(DIST), 'index.html')


if __name__ == '__main__':
    application.run(host='127.0.0.1', port=8000)
