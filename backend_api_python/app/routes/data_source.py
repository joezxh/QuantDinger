"""
数据源管理 API 路由
提供数据源配置、API 密钥、数据集元数据、查询缓存的 CRUD 接口
"""
from flask import Blueprint, request, jsonify, g

from app.utils.auth import login_required, admin_required, get_current_user_id, get_current_user_role
from app.utils.logger import get_logger
from app.services.data_source_service import get_data_source_service
from app.services.api_key_service import get_api_key_service
from app.services.dataset_service import get_dataset_service
from app.services.query_cache_service import get_query_cache_service

logger = get_logger(__name__)
data_source_bp = Blueprint('data_source', __name__)


def _get_user_context():
    """获取当前用户上下文"""
    return {
        "user_id": get_current_user_id(),
        "user_role": get_current_user_role() or "user"
    }


# ==================== DataSourceConfig ====================

@data_source_bp.route('/configs', methods=['GET'])
@login_required
def list_configs():
    """列出数据源配置"""
    try:
        params = request.args
        result = get_data_source_service().list_configs(
            layer=params.get('layer'),
            market_category=params.get('market_category'),
            enabled=params.get('enabled', type=lambda x: x.lower() == 'true'),
            search=params.get('search'),
            page=params.get('page', 1, type=int),
            page_size=params.get('page_size', 50, type=int)
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"list_configs failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs/<int:config_id>', methods=['GET'])
@login_required
def get_config(config_id):
    """获取单个数据源配置"""
    try:
        config = get_data_source_service().get_config(config_id)
        if not config:
            return jsonify({'code': 0, 'msg': '配置不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': config})
    except Exception as e:
        logger.error(f"get_config failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs', methods=['POST'])
@login_required
@admin_required
def create_config():
    """创建数据源配置（admin only）"""
    try:
        data = request.get_json() or {}
        required = ['source_code', 'source_name']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'code': 0, 'msg': f'缺少必填字段: {field}'}), 400
        result = get_data_source_service().create_config(data)
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"create_config failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs/<int:config_id>', methods=['PUT'])
@login_required
@admin_required
def update_config(config_id):
    """更新数据源配置（admin only）"""
    try:
        data = request.get_json() or {}
        result = get_data_source_service().update_config(config_id, data)
        if not result:
            return jsonify({'code': 0, 'msg': '配置不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"update_config failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs/<int:config_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_config(config_id):
    """删除数据源配置（admin only）"""
    try:
        success = get_data_source_service().delete_config(config_id)
        if not success:
            return jsonify({'code': 0, 'msg': '配置不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"delete_config failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs/<int:config_id>/test', methods=['POST'])
@login_required
@admin_required
def test_config_connection(config_id):
    """测试数据源连接（admin only）"""
    try:
        result = get_data_source_service().test_connection(config_id)
        return jsonify({'code': 1 if result['success'] else 0, 'msg': result['message'], 'data': result})
    except Exception as e:
        logger.error(f"test_config_connection failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


# ==================== API Keys ====================

@data_source_bp.route('/keys', methods=['GET'])
@login_required
def list_keys():
    """列出 API 密钥（带权限过滤）"""
    try:
        ctx = _get_user_context()
        params = request.args
        result = get_api_key_service().list_keys(
            source_config_id=params.get('source_config_id', type=int),
            key_type=params.get('key_type'),
            status=params.get('status'),
            user_id=ctx['user_id'],
            user_role=ctx['user_role'],
            page=params.get('page', 1, type=int),
            page_size=params.get('page_size', 50, type=int)
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"list_keys failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/keys/<int:key_id>', methods=['GET'])
@login_required
def get_key(key_id):
    """获取单个 API 密钥"""
    try:
        ctx = _get_user_context()
        key = get_api_key_service().get_key(key_id, ctx['user_id'], ctx['user_role'])
        if not key:
            return jsonify({'code': 0, 'msg': '密钥不存在或无权限'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': key})
    except Exception as e:
        logger.error(f"get_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/keys', methods=['POST'])
@login_required
def create_key():
    """创建 API 密钥"""
    try:
        data = request.get_json() or {}
        required = ['source_config_id', 'key_value']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'code': 0, 'msg': f'缺少必填字段: {field}'}), 400

        ctx = _get_user_context()
        # 非管理员只能创建 private 密钥
        if ctx['user_role'] != 'admin' and data.get('key_type') == 'public':
            return jsonify({'code': 0, 'msg': '无权限创建公共密钥'}), 403

        # 非管理员自动将 user_id 设为当前用户
        if ctx['user_role'] != 'admin':
            data['user_id'] = ctx['user_id']
            data['key_type'] = 'private'

        result = get_api_key_service().create_key(data, created_by=ctx['user_id'])
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"create_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/keys/<int:key_id>', methods=['PUT'])
@login_required
def update_key(key_id):
    """更新 API 密钥"""
    try:
        data = request.get_json() or {}
        ctx = _get_user_context()
        result = get_api_key_service().update_key(
            key_id, data, ctx['user_id'], ctx['user_role']
        )
        if not result:
            return jsonify({'code': 0, 'msg': '密钥不存在或无权限'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"update_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    """删除 API 密钥"""
    try:
        ctx = _get_user_context()
        success = get_api_key_service().delete_key(key_id, ctx['user_id'], ctx['user_role'])
        if not success:
            return jsonify({'code': 0, 'msg': '密钥不存在或无权限'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"delete_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


# ==================== Datasets ====================

@data_source_bp.route('/datasets', methods=['GET'])
@login_required
def list_datasets():
    """列出数据集元数据"""
    try:
        params = request.args
        result = get_dataset_service().list_datasets(
            source_id=params.get('source_id', type=int),
            dataset_code=params.get('dataset_code'),
            search=params.get('search'),
            page=params.get('page', 1, type=int),
            page_size=params.get('page_size', 50, type=int)
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"list_datasets failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
@login_required
def get_dataset(dataset_id):
    """获取单个数据集"""
    try:
        dataset = get_dataset_service().get_dataset(dataset_id)
        if not dataset:
            return jsonify({'code': 0, 'msg': '数据集不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': dataset})
    except Exception as e:
        logger.error(f"get_dataset failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/datasets', methods=['POST'])
@login_required
@admin_required
def create_dataset():
    """创建数据集（admin only）"""
    try:
        data = request.get_json() or {}
        required = ['source_id', 'dataset_code', 'dataset_name']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'code': 0, 'msg': f'缺少必填字段: {field}'}), 400
        result = get_dataset_service().create_dataset(data)
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"create_dataset failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/datasets/<int:dataset_id>', methods=['PUT'])
@login_required
@admin_required
def update_dataset(dataset_id):
    """更新数据集（admin only）"""
    try:
        data = request.get_json() or {}
        result = get_dataset_service().update_dataset(dataset_id, data)
        if not result:
            return jsonify({'code': 0, 'msg': '数据集不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"update_dataset failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/datasets/<int:dataset_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_dataset(dataset_id):
    """删除数据集（admin only）"""
    try:
        success = get_dataset_service().delete_dataset(dataset_id)
        if not success:
            return jsonify({'code': 0, 'msg': '数据集不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"delete_dataset failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/configs/<int:config_id>/datasets', methods=['GET'])
@login_required
def get_config_datasets(config_id):
    """获取某个数据源下的所有数据集"""
    try:
        result = get_dataset_service().get_datasets_by_source(config_id)
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"get_config_datasets failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


# ==================== Query Cache ====================

@data_source_bp.route('/cache', methods=['GET'])
@login_required
@admin_required
def list_cache():
    """列出查询缓存（admin only）"""
    try:
        params = request.args
        result = get_query_cache_service().list_cache(
            source_code=params.get('source_code'),
            status=params.get('status'),
            page=params.get('page', 1, type=int),
            page_size=params.get('page_size', 50, type=int)
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"list_cache failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/cache/<int:cache_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_cache(cache_id):
    """删除缓存条目（admin only）"""
    try:
        success = get_query_cache_service().delete_cache(cache_id)
        if not success:
            return jsonify({'code': 0, 'msg': '缓存不存在'}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"delete_cache failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@data_source_bp.route('/cache/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_cache():
    """清理过期缓存（admin only）"""
    try:
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        count = get_query_cache_service().cleanup_expired(max_age_hours)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'deleted_count': count}})
    except Exception as e:
        logger.error(f"cleanup_cache failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500
