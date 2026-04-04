from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import csv
import io
import os
from datetime import datetime, timezone

app = Flask(__name__)
DB  = os.environ.get('DB_PATH', 'burns.db')
CSV = os.environ.get('CSV_PATH', 'burns_export.csv')

# ── Konfiguracja ──────────────────────────────────────────────────────────────
XNT_FEE_REQUIRED = 0.1  # testowo; zmień na 1.0 gdy gotowe

# ── Baza danych ───────────────────────────────────────────────────────────────
def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    con.execute('''
        CREATE TABLE IF NOT EXISTS burns (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            evm_address  TEXT    NOT NULL,
            burn_tx      TEXT    NOT NULL,
            burn_amount  TEXT    DEFAULT "0",
            epoch_date   TEXT    NOT NULL,
            created_at   TEXT    NOT NULL
        )
    ''')
    con.execute('''
        CREATE TABLE IF NOT EXISTS wallet_links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            evm_address TEXT    NOT NULL UNIQUE,
            svm_address TEXT    NOT NULL,
            xnt_tx      TEXT,
            created_at  TEXT    NOT NULL
        )
    ''')
    con.commit()
    con.close()

init_db()

# ── Pomocnicze ────────────────────────────────────────────────────────────────
def current_epoch():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def epoch_ends_at(epoch_date):
    from datetime import timedelta
    d = datetime.strptime(epoch_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    return (d + timedelta(days=1)).isoformat()

def rebuild_csv():
    """Regeneruje burns_export.csv z bazy — zawsze aktualny z SVM."""
    con = get_db()
    rows = con.execute('''
        SELECT b.evm_address, w.svm_address,
               b.burn_amount, b.created_at, b.epoch_date, b.burn_tx
        FROM burns b
        LEFT JOIN wallet_links w ON b.evm_address = w.evm_address
        ORDER BY b.created_at ASC
    ''').fetchall()
    con.close()

    with open(CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['evm_address', 'svm_address', 'burn_amount',
                         'date', 'epoch', 'burn_tx'])
        for r in rows:
            writer.writerow([r['evm_address'], r['svm_address'] or '',
                             r['burn_amount'], r['created_at'],
                             r['epoch_date'], r['burn_tx']])

# ── Endpointy ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ── BURN — rejestracja spalenia ───────────────────────────────────────────────
@app.route('/api/burn', methods=['POST'])
def register_burn():
    data        = request.get_json(silent=True) or {}
    evm         = (data.get('evm_address') or '').lower().strip()
    burn_tx     = data.get('burn_tx', '')
    burn_amount = data.get('burn_amount', '0')

    if not evm:
        return jsonify({'error': 'Missing EVM address'}), 400
    if not burn_tx:
        return jsonify({'error': 'Missing burn txHash'}), 400

    epoch = current_epoch()
    now   = datetime.now(timezone.utc).isoformat()

    con = get_db()
    try:
        cur = con.execute('''
            INSERT INTO burns (evm_address, burn_tx, burn_amount, epoch_date, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (evm, burn_tx, burn_amount, epoch, now))
        con.commit()
        burn_id = cur.lastrowid

        rebuild_csv()

        # Statystyki epoki
        row = con.execute('''
            SELECT SUM(CAST(burn_amount AS REAL)) AS my_total
            FROM burns WHERE evm_address = ? AND epoch_date = ?
        ''', (evm, epoch)).fetchone()
        my_total = row['my_total'] or 0

        row2 = con.execute('''
            SELECT SUM(CAST(burn_amount AS REAL)) AS epoch_total,
                   COUNT(DISTINCT evm_address)    AS participants
            FROM burns WHERE epoch_date = ?
        ''', (epoch,)).fetchone()
        epoch_total  = row2['epoch_total'] or 0
        participants = row2['participants'] or 0

        my_share = (my_total / epoch_total * 100) if epoch_total > 0 else 0

        return jsonify({
            'success':      True,
            'burn_id':      burn_id,
            'epoch':        epoch,
            'epoch_ends':   epoch_ends_at(epoch),
            'my_total':     my_total,
            'epoch_total':  epoch_total,
            'my_share_pct': round(my_share, 4),
            'participants': participants
        })
    except sqlite3.IntegrityError as e:
        return jsonify({'error': str(e)}), 409
    finally:
        con.close()

# ── LINK — powiązanie portfeli EVM↔SVM + opłata XNT ──────────────────────────
@app.route('/api/link', methods=['POST'])
def link_wallets():
    data   = request.get_json(silent=True) or {}
    evm    = (data.get('evm_address') or '').lower().strip()
    svm    = (data.get('svm_address') or '').strip()
    xnt_tx = data.get('xnt_tx', '')

    if not evm or not svm:
        return jsonify({'error': 'Both wallet addresses required'}), 400
    if not xnt_tx:
        return jsonify({'error': 'Missing XNT fee txHash'}), 400

    now = datetime.now(timezone.utc).isoformat()
    con = get_db()
    try:
        con.execute('''
            INSERT INTO wallet_links (evm_address, svm_address, xnt_tx, created_at)
            VALUES (?, ?, ?, ?)
        ''', (evm, svm, xnt_tx, now))
        con.commit()
        rebuild_csv()
        return jsonify({'success': True, 'evm_address': evm, 'svm_address': svm})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'This EVM wallet is already linked to an SVM wallet'}), 409
    finally:
        con.close()

# ── STATUS ────────────────────────────────────────────────────────────────────
@app.route('/api/status/<evm_address>', methods=['GET'])
def check_status(evm_address):
    evm   = evm_address.lower()
    epoch = current_epoch()
    con   = get_db()

    link = con.execute(
        'SELECT * FROM wallet_links WHERE evm_address = ?', (evm,)
    ).fetchone()

    burns = con.execute('''
        SELECT burn_tx, burn_amount, created_at
        FROM burns WHERE evm_address = ? AND epoch_date = ?
        ORDER BY created_at DESC
    ''', (evm, epoch)).fetchall()

    my_total = sum(float(b['burn_amount']) for b in burns)

    row = con.execute('''
        SELECT SUM(CAST(burn_amount AS REAL)) AS epoch_total
        FROM burns WHERE epoch_date = ?
    ''', (epoch,)).fetchone()
    epoch_total = row['epoch_total'] or 0
    con.close()

    my_share = (my_total / epoch_total * 100) if epoch_total > 0 else 0

    return jsonify({
        'linked':       link is not None,
        'svm_address':  link['svm_address'] if link else None,
        'epoch':        epoch,
        'epoch_ends':   epoch_ends_at(epoch),
        'burns_today':  [dict(b) for b in burns],
        'my_total':     my_total,
        'epoch_total':  epoch_total,
        'my_share_pct': round(my_share, 4)
    })

# ── LEADERBOARD ──────────────────────────────────────────────────────────────
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    epoch = request.args.get('epoch', current_epoch())
    con   = get_db()
    rows  = con.execute('''
        SELECT b.evm_address,
               SUM(CAST(b.burn_amount AS REAL)) AS total_burned,
               COUNT(*)                         AS burn_count,
               w.svm_address
        FROM burns b
        LEFT JOIN wallet_links w ON b.evm_address = w.evm_address
        WHERE b.epoch_date = ?
        GROUP BY b.evm_address
        ORDER BY total_burned DESC
        LIMIT 25
    ''', (epoch,)).fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

# ── STATS ─────────────────────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def stats():
    epoch = current_epoch()
    con   = get_db()
    g = con.execute('''
        SELECT COUNT(*)                       AS total_burns,
               COUNT(DISTINCT evm_address)    AS total_wallets,
               SUM(CAST(burn_amount AS REAL)) AS total_burned
        FROM burns
    ''').fetchone()
    e = con.execute('''
        SELECT COUNT(*)                       AS epoch_burns,
               COUNT(DISTINCT evm_address)    AS epoch_wallets,
               SUM(CAST(burn_amount AS REAL)) AS epoch_burned
        FROM burns WHERE epoch_date = ?
    ''', (epoch,)).fetchone()
    links = con.execute('SELECT COUNT(*) AS cnt FROM wallet_links').fetchone()
    con.close()

    return jsonify({
        'current_epoch':  epoch,
        'epoch_ends':     epoch_ends_at(epoch),
        'global': dict(g),
        'epoch':  dict(e),
        'linked_wallets': links['cnt']
    })

# ── BROWSE DB ─────────────────────────────────────────────────────────────────
@app.route('/api/db/burns', methods=['GET'])
def db_burns():
    con  = get_db()
    rows = con.execute('SELECT * FROM burns ORDER BY created_at DESC LIMIT 200').fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/db/links', methods=['GET'])
def db_links():
    con  = get_db()
    rows = con.execute('SELECT * FROM wallet_links ORDER BY created_at DESC').fetchall()
    con.close()
    return jsonify([dict(r) for r in rows])

# ── CSV EXPORT ────────────────────────────────────────────────────────────────
@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    con  = get_db()
    rows = con.execute('''
        SELECT b.evm_address, w.svm_address,
               b.burn_amount, b.created_at, b.epoch_date,
               b.burn_tx, b.id
        FROM burns b
        LEFT JOIN wallet_links w ON b.evm_address = w.evm_address
        ORDER BY b.created_at DESC
    ''').fetchall()
    con.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['evm_address', 'svm_address', 'burn_amount',
                     'date', 'epoch', 'burn_tx', 'id'])
    for r in rows:
        writer.writerow([r['evm_address'], r['svm_address'],
                         r['burn_amount'], r['created_at'],
                         r['epoch_date'], r['burn_tx'], r['id']])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=burns_export.csv'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
