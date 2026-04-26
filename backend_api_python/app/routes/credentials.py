"""Exchange credentials vault.

encrypted_config stores Fernet ciphertext derived from SECRET_KEY.
"""
import traceback
import json
from flask import Blueprint, request, jsonify, g

import requests as rq

from app.database.repositories.credential_repository import CredentialRepository
from app.database.session import get_session
from app.utils.logger import get_logger
from app.utils.auth import login_required
from app.utils.credential_crypto import encrypt_credential_blob, decrypt_credential_blob

logger = get_logger(__name__)
credentials_bp = Blueprint('credentials', __name__)


def _api_key_hint(api_key: str) -> str:
    if not api_key:
        return ''
    s = str(api_key)
    if len(s) <= 8:
        return s[:2] + '***'
    return f"{s[:4]}...{s[-4:]}"


@credentials_bp.route('/list', methods=['GET'])
@login_required
def list_credentials():
    """
    ---
    tags:
      - Exchange/Credentials
    summary: "List exchange credentials"
    description: "Return the current user's exchange credential list with masked API keys."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with credential list
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
              properties:
                items:
                  type: array
                  items:
                    type: object
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        with get_session() as session:
            rows = CredentialRepository(session).list_user_credentials(user_id)
        items = []
        for row in rows:
            item = {
                'id': row.id,
                'user_id': row.user_id,
                'name': row.name,
                'exchange_id': row.exchange_id,
                'api_key_hint': row.api_key_hint,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'enable_demo_trading': False,
            }
            try:
                plain = decrypt_credential_blob(row.encrypted_config)
                cfg = json.loads(plain) if plain else {}
                item['enable_demo_trading'] = bool(cfg.get('enable_demo_trading') or cfg.get('enableDemoTrading'))
            except Exception:
                item['enable_demo_trading'] = False
            items.append(item)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'items': items}})
    except Exception as e:
        logger.error(f"list_credentials failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': {'items': []}}), 500


CRYPTO_EXCHANGES = ['binance', 'okx', 'bitget', 'bybit', 'coinbaseexchange', 'kraken', 'kucoin', 'gate', 'deepcoin', 'htx']


def _egress_ipify(url: str) -> str:
    try:
        r = rq.get(url, timeout=8)
        if r.status_code != 200:
            return ""
        j = r.json()
        if not isinstance(j, dict):
            return ""
        return str(j.get("ip") or "").strip()
    except Exception:
        return ""


@credentials_bp.route('/create', methods=['POST'])
@login_required
def create_credential():
    """
    ---
    tags:
      - Exchange/Credentials
    summary: "Create exchange credential"
    description: "Add a new exchange/IBKR/MT5 credential with encrypted storage."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - exchange_id
          properties:
            name:
              type: string
              description: "Credential display name"
            exchange_id:
              type: string
              description: "Exchange identifier (binance, okx, ibkr, mt5, etc.)"
            api_key:
              type: string
              description: "API key (for crypto exchanges)"
            secret_key:
              type: string
              description: "Secret key (for crypto exchanges)"
            passphrase:
              type: string
              description: "Passphrase (required by some exchanges)"
            enable_demo_trading:
              type: boolean
              description: "Enable demo/sandbox trading"
            ibkr_host:
              type: string
              description: "IBKR TWS/Gateway host address"
            ibkr_port:
              type: integer
              description: "IBKR port number"
            ibkr_client_id:
              type: integer
              description: "IBKR client ID"
            ibkr_account:
              type: string
              description: "IBKR account number"
            mt5_server:
              type: string
              description: "MT5 server address"
            mt5_login:
              type: string
              description: "MT5 login name"
            mt5_password:
              type: string
              description: "MT5 password"
            mt5_terminal_path:
              type: string
              description: "MT5 terminal installation path"
    responses:
      200:
        description: Credential created successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
              properties:
                id:
                  type: integer
                  description: "New credential ID"
      400:
        description: Missing required fields or unsupported exchange
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        exchange_id = (data.get('exchange_id') or '').strip().lower()
        if not exchange_id:
            return jsonify({'code': 0, 'msg': 'Missing exchange_id', 'data': None}), 400
        config = {'exchange_id': exchange_id}
        hint = ''
        if exchange_id == 'ibkr':
            config.update({'ibkr_host': (data.get('ibkr_host') or '127.0.0.1').strip(), 'ibkr_port': int(data.get('ibkr_port') or 7497), 'ibkr_client_id': int(data.get('ibkr_client_id') or 1), 'ibkr_account': (data.get('ibkr_account') or '').strip()})
            hint = f"{config['ibkr_host']}:{config['ibkr_port']}"
        elif exchange_id == 'mt5':
            mt5_server = (data.get('mt5_server') or '').strip()
            mt5_login = str(data.get('mt5_login') or '').strip()
            mt5_password = (data.get('mt5_password') or '').strip()
            if not mt5_server or not mt5_login or not mt5_password:
                return jsonify({'code': 0, 'msg': 'Missing mt5_server/mt5_login/mt5_password', 'data': None}), 400
            config.update({'mt5_server': mt5_server, 'mt5_login': mt5_login, 'mt5_password': mt5_password, 'mt5_terminal_path': (data.get('mt5_terminal_path') or '').strip()})
            hint = f"{mt5_server}/{mt5_login}"
        elif exchange_id in CRYPTO_EXCHANGES:
            api_key = (data.get('api_key') or '').strip()
            secret_key = (data.get('secret_key') or '').strip()
            if not api_key or not secret_key:
                return jsonify({'code': 0, 'msg': 'Missing api_key/secret_key', 'data': None}), 400
            config.update({'api_key': api_key, 'secret_key': secret_key, 'passphrase': (data.get('passphrase') or '').strip(), 'enable_demo_trading': bool(data.get('enable_demo_trading', False))})
            hint = _api_key_hint(api_key)
        else:
            return jsonify({'code': 0, 'msg': f'Unsupported exchange: {exchange_id}', 'data': None}), 400
        stored_blob = encrypt_credential_blob(json.dumps(config, ensure_ascii=False))
        with get_session() as session:
            row = CredentialRepository(session).create_credential(user_id=user_id, name=name, exchange_id=exchange_id, api_key_hint=hint, encrypted_config=stored_blob)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'id': row.id}})
    except Exception as e:
        logger.error(f"create_credential failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@credentials_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_credential():
    """
    ---
    tags:
      - Exchange/Credentials
    summary: "Delete exchange credential"
    description: "Delete the current user's exchange credential by ID."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: query
        type: integer
        required: true
        description: "Credential ID"
    responses:
      200:
        description: Credential deleted successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
      400:
        description: Missing credential ID
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        cred_id = request.args.get('id', type=int)
        if not cred_id:
            return jsonify({'code': 0, 'msg': 'Missing id', 'data': None}), 400
        with get_session() as session:
            CredentialRepository(session).delete_credential(cred_id, user_id)
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"delete_credential failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@credentials_bp.route('/get', methods=['GET'])
@login_required
def get_credential():
    """
    ---
    tags:
      - Exchange/Credentials
    summary: "Get credential detail with decrypted config"
    description: "Return the full decrypted configuration for a specific credential, including sensitive fields like API keys."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: query
        type: integer
        required: true
        description: "Credential ID"
    responses:
      200:
        description: Successful response with decrypted config
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing credential ID
      401:
        description: Unauthorized
      404:
        description: Credential not found
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        cred_id = request.args.get('id', type=int)
        if not cred_id:
            return jsonify({'code': 0, 'msg': 'Missing id', 'data': None}), 400
        with get_session() as session:
            row = CredentialRepository(session).get_credential(cred_id, user_id)
        if not row:
            return jsonify({'code': 0, 'msg': 'Not found', 'data': None}), 404
        plain = decrypt_credential_blob(row.encrypted_config)
        decrypted = json.loads(plain) if plain else {}
        decrypted['exchange_id'] = row.exchange_id or decrypted.get('exchange_id')
        return jsonify({'code': 1, 'msg': 'success', 'data': {'id': row.id, 'name': row.name, 'exchange_id': row.exchange_id, 'api_key_hint': row.api_key_hint, 'config': decrypted}})
    except Exception as e:
        logger.error(f"get_credential failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
