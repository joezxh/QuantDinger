/*
 Navicat Premium Dump SQL

 Source Server         : tencent-mysql
 Source Server Type    : MySQL
 Source Server Version : 50718 (5.7.18-txsql-log)
 Source Host           : gz-cdb-e0i0vczt.sql.tencentcdb.com:29017
 Source Schema         : fama-ai

 Target Server Type    : MySQL
 Target Server Version : 50718 (5.7.18-txsql-log)
 File Encoding         : 65001

 Date: 24/04/2026 07:51:13
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for ai_api_key
-- ----------------------------
DROP TABLE IF EXISTS `ai_api_key`;
CREATE TABLE `ai_api_key`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '名称',
  `model_id` bigint(20) NULL DEFAULT NULL COMMENT '模型编号',
  `api_key` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '密钥',
  `platform` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '平台',
  `url` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'API 地址',
  `status` smallint(6) NULL DEFAULT NULL COMMENT '启用',
  `creator` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '创建者',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '更新者',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` bit(1) NULL DEFAULT b'0' COMMENT '是否删除',
  `property` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '配置',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 16 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'AI API 秘钥' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for ai_model
-- ----------------------------
DROP TABLE IF EXISTS `ai_model`;
CREATE TABLE `ai_model`  (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'id',
  `name` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '模型名字\n',
  `model` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '模型类型(自己定义qianwen、yiyan、xinghuo、openai)\n',
  `platform` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '平台',
  `sort` int(11) NULL DEFAULT NULL COMMENT '排序',
  `status` tinyint(4) NULL DEFAULT NULL COMMENT '禁用 0、正常 1、禁用\n',
  `temperature` double NULL DEFAULT 0.85 COMMENT '温度参数',
  `max_tokens` int(11) NULL DEFAULT 1500 COMMENT '单条回复的最大 Token 数量',
  `top_p` float NULL DEFAULT 0.8 COMMENT 'topP',
  `top_k` int(11) NULL DEFAULT 70 COMMENT 'topk',
  `seed` int(11) NULL DEFAULT 1234 COMMENT 'seed',
  `max_contexts` int(11) NULL DEFAULT 50 COMMENT '上下文的最大 Message 数量',
  `max_turns` int(11) NULL DEFAULT 20 COMMENT '单个会话最大对话轮次',
  `create_time` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `creator` bigint(20) NULL DEFAULT NULL COMMENT '创建用户',
  `updater` bigint(20) NULL DEFAULT NULL COMMENT '更新用户',
  `deleted` bit(1) NULL DEFAULT b'0' COMMENT '删除',
  `type` int(11) NULL DEFAULT NULL COMMENT '类型',
  `balance_type` varchar(32) NULL DEFAULT NULL COMMENT '负载均衡类型',
  `dimensions` int(11) NULL DEFAULT NULL COMMENT 'Dimensions值',
  `retry` int(11) NULL DEFAULT 3 COMMENT '重试次数',
  `timeout` int(11) NULL DEFAULT 180 COMMENT '段式超时时间',
  `stream_timeout` int(11) NULL DEFAULT 120 COMMENT '流式超时时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uid_model_platform`(`model`, `platform`, `key_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 78 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'AI 模型信息' ROW_FORMAT = DYNAMIC;

SET FOREIGN_KEY_CHECKS = 1;
