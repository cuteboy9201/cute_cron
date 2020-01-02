#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@Author: Youshumin
@Date: 2019-08-26 10:26:19
@LastEditors: Please set LastEditors
@LastEditTime: 2019-12-03 17:21:45
@desc: 管理定时任务 添加post, 修改状态patch, 删除delete,  修改内容put, 获取任务get
'''

import json
import logging

import apscheduler
from oslo.form.form import form_error
from oslo.web.requesthandler import MixinRequestHandler
from oslo.web.route import route
from tornado import gen
from forms.cron import (CronDeleteForm, CronGetForm, CronPatchForm,
                        CronPostFrom, CronPutForm)
from utils.cron import register_task, scheduler

LOG = logging.getLogger(__name__)


@route("/cron/")
class CronTaskHandler(MixinRequestHandler):
    def post(self):
        """
            添加定时任务
        """
        form = CronPostFrom(self)
        if form.is_valid():
            cron_id = form.value_dict["cron_id"]
            cron_type = form.value_dict["cron_type"]
            cron_body = form.value_dict["cron_body"]
            cron_time_trigger = form.value_dict["cron_time_trigger"]
            cron_time_body = form.value_dict["cron_time_body"]
        else:
            form_error(self, form)
            return

        return_id = register_task(cron_id, cron_type, cron_body,
                                  cron_time_trigger, cron_time_body)
        if return_id:
            self.send_ok(data="")
        else:
            self.send_fail(msg="添加任务失败")
        return

    def put(self):
        """
            修改定时任务
        """
        form = CronPutForm(self)
        if form.is_valid():
            cron_id = form.value_dict["cron_id"]
            cron_type = form.value_dict["cron_type"]
            cron_body = form.value_dict["cron_body"]
            cron_time_trigger = form.value_dict["cron_time_trigger"]
            cron_time_body = form.value_dict["cron_time_body"]
        else:
            form_error(self, form)
            return

        old_cron = scheduler.get_job(cron_id)
        if old_cron:
            return_id = register_task(cron_id, cron_type, cron_body,
                                      cron_time_trigger, cron_time_body)
            if return_id:
                self.send_ok(data="")
                return
        else:
            self.send_fail(msg="修改任务失败")
            return

    def delete(self):
        """
            删除定时任务 
        """
        form = CronDeleteForm(self)
        if form.is_valid():
            cron_id = form.value_dict["cron_id"]
        else:
            form_error(self, form)
            return
        try:
            scheduler.remove_job(cron_id)
            self.send_ok(data="")
        except Exception:
            self.send_fail(msg="删除任务失败")
        return

    def get(self):
        """
            获取定时任务
        """
        form = CronGetForm(self)
        if form.is_valid():
            pageIndex = form.value_dict["pageIndex"]
            pageLimit = form.value_dict["pageLimit"]
            cron_id = form.value_dict["cron_id"]
        else:
            form_error(self, form)
            return

        start = (int(pageIndex) - 1) * int(pageLimit)
        end = int(pageIndex) * int(pageLimit)
        reps_list = []

        try:
            if not cron_id:
                cron_list = scheduler.get_jobs()
            else:
                cron_list = [scheduler.get_jobs(cron_id)]
                start = 0

            for cron in cron_list:
                if isinstance(cron.trigger,
                              apscheduler.triggers.interval.IntervalTrigger):
                    # 解析 interval 触发器时间
                    cron_task = dict(
                        cron_body=cron.kwargs.get('data'),
                        status='0' if cron.next_run_time else '1',
                        next_run_time=str(cron.next_run_time),
                        tigger="interval",
                        cron_time=cron.trigger.interval.total_seconds(),
                        cron_id=cron.id)
                    reps_list.append(cron_task)
                elif isinstance(cron.trigger,
                                apscheduler.triggers.cron.CronTrigger):
                    # 解析cron 时间触发器
                    start_date = cron.trigger.start_date
                    end_date = cron.trigger.end_date
                    fields = cron.trigger.fields

                    cron_time = {}
                    for item in fields:
                        cron_time.setdefault(item.name, str(item))

                    cron_task = dict(cron_body=cron.kwargs.get('data'),
                                     status='0' if cron.next_run_time else '1',
                                     trigger="cron",
                                     cron_time=cron_time,
                                     next_run_time=str(cron.next_run_time),
                                     cron_id=cron.id)
                    reps_list.append(cron_task)
                elif isinstance(cron.trigger,
                                apscheduler.triggers.date.DateTrigger):
                    # 解析 date时间触发器
                    cron_task = dict(cron_body=cron.kwargs.get('data'),
                                     status='0' if cron.next_run_time else '1',
                                     trigger="date",
                                     cron_time=str(cron.trigger.run_date),
                                     next_run_time=str(cron.next_run_time),
                                     cron_id=cron.id)
                    reps_list.append(cron_task)
                else:
                    print(cron.trigger)
                    print(type(cron.trigger))
                LOG.debug(reps_list)

            retList = reps_list[start:end]
            totalCount = len(reps_list)
        except Exception as e:
            retList = []
            totalCount = 0
            LOG.debug(str(e))
        return self.send_ok(data={"rows": retList, "totalCount": totalCount})

    def patch(self):
        """
            暂停或者恢复任务
        """
        form = CronPatchForm(self)
        if form.is_valid():
            cron_id = form.value_dict["cron_id"]
        else:
            form_error(self, form)
            return

        if scheduler.get_job(cron_id).next_run_time:
            option = "pause"
        else:
            option = "resume"

        if option == "pause":
            try:
                scheduler.pause_job(cron_id)
                self.send_ok(data="")
            except Exception as e:
                self.send_fail(msg=str(e))
        elif option == "resume":
            try:
                scheduler.resume_job(cron_id)
                self.send_ok(data="")
            except Exception as e:
                self.send_fail(msg=str(e))
        else:
            self.send_fail(nsg="未知错误")
        return


@route("/test/mq/")
class TestHandler(MixinRequestHandler):
    @gen.coroutine
    def get(self):
        hostinfo = [
            dict(host="192.168.2.132",
                 port=22051,
                 user="root",
                 password="",
                 ansible_ssh_private_key_file="~/.ssh/youshumin"),
        ]
        mq_server = self.application.mq_server

        data = dict(msg_id="2019-12-15",
                    msg_task="setup",
                    msg_data=hostinfo,
                    msg_return=True)
        from configs.setting import MQ_ANSIBLE_EXCHANGE, MQ_ANSIBLE_ROUTING_KEY
        yield mq_server.send_msg(json.dumps(data), MQ_ANSIBLE_EXCHANGE,
                                 MQ_ANSIBLE_ROUTING_KEY)
        return self.send_ok(data="")