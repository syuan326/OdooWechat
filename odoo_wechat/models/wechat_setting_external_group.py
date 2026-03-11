# -*- coding: utf-8 -*-
import json
import logging
from urllib import error, parse, request

from odoo import fields, models, exceptions


_logger = logging.getLogger(__name__)


class WechatSettingExternalGroup(models.Model):
    _inherit = 'wechat.setting'

    wechat_supplier_group_chat_id = fields.Char(string="外部供应商群聊ID")

    def send_external_group_text_message(self, text):
        """发送文本消息到企业微信外部群聊。"""
        self.ensure_one()
        if not self.wechat_supplier_group_chat_id:
            _logger.info("未配置外部供应商群聊ID，跳过企业微信消息发送。")
            return

        from wechatpy.enterprise import WeChatClient

        client = WeChatClient(self.wechat_corp_id, self.wechat_secret)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/send?%s' % parse.urlencode(
            {'access_token': client.access_token}
        )
        payload = json.dumps({
            'chat_id': self.wechat_supplier_group_chat_id,
            'msgtype': 'text',
            'text': {
                'content': text,
            }
        }).encode('utf-8')
        req = request.Request(
            url=url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
        except error.URLError as exc:
            raise exceptions.UserError(f"企业微信发送外部群消息请求失败：{exc}") from exc

        if result.get('errcode'):
            raise exceptions.UserError(f"企业微信发送外部群消息失败：{result.get('errmsg')}")
