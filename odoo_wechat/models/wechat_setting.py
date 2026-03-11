# -*- coding: utf-8 -*-
import logging

import requests

from odoo import fields, models, api, exceptions


_logger = logging.getLogger(__name__)


class WechatSetting(models.Model):
    _name = 'wechat.setting'
    _description = '企业微信配置'
    
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string="公司", required=True, default=lambda self: self.env.company)
    name = fields.Char(string="企业名称", required=True)
    wechat_corp_id = fields.Char(string="CorpId", required=True)
    wechat_agent_id = fields.Char(string="AgentId", required=True)
    wechat_secret = fields.Char(string="Secret", required=True)
    wechat_supplier_group_chat_id = fields.Char(string="外部供应商群聊ID")
    wechat_js_sdk_file_name = fields.Char(string='JS SDK文件名')
    wechat_js_sdk_file = fields.Binary(string='JS SDK文件', attachment=True)

    is_create_wechat_user = fields.Boolean(string="是否创建系统用户")
    wechat_default_passwd = fields.Char(string="默认登录系统密码")
    description = fields.Text(string="备注")

    @api.model
    def get_company_setting(self, company_id):
        """
        获取指定公司的参数配置
        """
        return self.search([('company_id', '=', company_id)], limit=1)

    @api.model
    def get_wechat_client_corp_secret(self, company_id):
        """
        返回CorpId和Secret
        """
        setting_id = self.get_company_setting(company_id)
        if not setting_id:
            raise exceptions.ValidationError("请先配置该公司下的企业微信相关参数.")
        return setting_id.wechat_corp_id, setting_id.wechat_secret

    @api.model
    def get_wechat_is_create_wechat_user(self, company_id):
        """
        返回是否创建系统用户和默认的登录密码
        """
        setting_id = self.get_company_setting(company_id)
        return setting_id.is_create_wechat_user, setting_id.wechat_default_passwd

    @api.model
    def get_all_company_wechat_corp(self):
        """
        返回所有配置的公司参数
        """
        return [{
            'name': x.name,
            'wechat_corp_id': x.wechat_corp_id,
            'wechat_agent_id': x.wechat_agent_id,
        } for x in self.search([])]

    def send_external_group_text_message(self, text):
        """发送文本消息到企业微信外部群聊。"""
        self.ensure_one()
        if not self.wechat_supplier_group_chat_id:
            _logger.info("未配置外部供应商群聊ID，跳过企业微信消息发送。")
            return

        from wechatpy.enterprise import WeChatClient

        client = WeChatClient(self.wechat_corp_id, self.wechat_secret)
        response = requests.post(
            'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/send',
            params={'access_token': client.access_token},
            json={
                'chat_id': self.wechat_supplier_group_chat_id,
                'msgtype': 'text',
                'text': {
                    'content': text,
                }
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        if result.get('errcode'):
            raise exceptions.UserError(f"企业微信发送外部群消息失败：{result.get('errmsg')}")
