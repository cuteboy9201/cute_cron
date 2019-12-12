import datetime
import logging
import time

from apscheduler.schedulers.tornado import TornadoScheduler

from configs.setting import RBAC_DB

LOG = logging.getLogger(__name__)
scheduler = TornadoScheduler()
scheduler.add_jobstore("sqlalchemy", url=RBAC_DB)


def crontrigger(cron_trigger, cron_body):
    """
        根据定时任务触发器  设置任务时间 date interval cron
    """
    cron_body = eval(cron_body)
    if cron_trigger == "date":
        run_date = cron_body.get("run_date", None)
        try:
            run_date = datetime.datetime.strptime(run_date,
                                                  "%Y-%m-%d %H:%M:%S")
            return True, dict(trigger="date", run_date=run_date)
        except Exception as e:
            LOG.error(str(e))
            return False, "date: run_date格式有问题"
        return False, ""

    if cron_trigger == "interval":
        seconds = cron_body.get("seconds")
        minutes = cron_body.get("minutes")
        hours = cron_body.get("hours")
        days = cron_body.get("days")
        start_date = cron_body.get("start_date")
        end_date = cron_body.get("end_date")

        kwargs = dict(trigger="interval")
        if seconds and not minutes and not hours and not days:
            kwargs.setdefault("seconds", int(seconds))
        elif minutes and not seconds and not hours and not days:
            kwargs.setdefault("minutes", int(minutes))
        elif hours and not seconds and not minutes and not days:
            kwargs.setdefault("hours", int(hours))
        elif days and not seconds and not hours and not minutes:
            kwargs.setdefault("days", int(days))
        else:
            return False, "任务时间格式存在问题"
        try:
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d %H:%M:%S")
            end_date = datetime.datetime.strptime(end_date,
                                                  "%Y-%m-%d %H:%M:%S")
            if start_date and end_date:
                kwargs.setdefault("start_date", start_date)
                kwargs.setdefault("end_date", end_date)
        except Exception as e:
            LOG.warning(str(e))
        return True, kwargs

    if cron_trigger == "cron":
        second = cron_body.get("second", "*")
        minute = cron_body.get("minute", "*")
        hour = cron_body.get("hour", "*")
        day = cron_body.get("day", "*")
        month = cron_body.get("month", "*")
        day_of_week = cron_body.get("day_of_week", "*")
        kwargs = dict(trigger="cron",
                      second=second,
                      minute=minute,
                      hour=hour,
                      day=day,
                      month=month,
                      day_of_week=day_of_week)
        return True, kwargs
    return False, ""


def register_task(cron_id, cron_type, cron_body, cron_time_trigger,
                  cron_time_body):
    """
        注册任务(添加任务)
    """

    FUNC = CrontabType()

    if cron_type == "post":
        func = getattr(FUNC, "request_post")
    elif cron_type == "get":
        func = getattr(FUNC, "request_get")
    elif cron_type == "local":
        func = getattr(FUNC, "shell_local")
    elif cron_type == "remote":
        func = getattr(FUNC, "shell_remote")
    else:
        return False
    args = dict(data=cron_body)
    code, kwargs = crontrigger(cron_time_trigger, cron_time_body)

    LOG.debug("任务触发信息: {}".format(kwargs))
    if code:
        scheduler.add_job(func=func,
                          id=cron_id,
                          kwargs=args,
                          **kwargs,
                          replace_existing=True)
        return cron_id
    else:
        return False


class CrontabType:
    """
      根据cront_type选择不同执行方法... 任务函数
    """
    def request_post(self, data):
        LOG.info("this request_post")
        LOG.info("data: {}".format(data))

    def request_get(self, data):
        LOG.info("this request_get")

    def shell_local(self, data):
        LOG.info("this is local_shell")

    def shell_remote(self, data):
        LOG.info("this is remote_shell")

    def write_log(self, data):
        pass
