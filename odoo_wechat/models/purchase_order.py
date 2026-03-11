# -*- coding: utf-8 -*-
import logging

from odoo import models


_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_rfq_send(self):
        result = super().action_rfq_send()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for order in self:
            setting = self.env['wechat.setting'].sudo().get_company_setting(order.company_id.id)
            if not setting:
                continue

            if not setting.wechat_supplier_group_chat_id:
                continue

            order_url = f"{base_url}/web#id={order.id}&model=purchase.order&view_type=form"
            msg = (
                f"【RFQ通知】\n"
                f"询价单：{order.name}\n"
                f"供应商：{order.partner_id.display_name}\n"
                f"查看链接：{order_url}"
            )
            try:
                setting.send_external_group_text_message(msg)
            except Exception:
                _logger.exception("发送RFQ到企业微信外部供应商群失败，RFQ=%s", order.name)
        return result
